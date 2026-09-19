from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select, and_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db
from app.models.collection import (Acquisition,AcquisitionType,Attachment,CollectionEvent,CollectionItem,CollectionStatus,Creator,Culture,ImageType,Location,Material,Movement,MovementRequest,MovementStatus,ObjectType,ProvenanceRecord,)
from app.permissions import require_role
from app.qr import generate_item_qr
from app.schemas import (AcquisitionCreate,AttachmentResponse,CollectionItemCreate,CollectionItemResponse,CollectionItemUpdate,LocationCreate,MovementDecision,MovementRequestCreate,PaginatedCollectionResponse,ProvenanceCreate,)
from app.security import get_current_user_id
from app.storage import resolve_file, store_upload
from app.cache import delete_prefix, get_json, set_json
from app.core.config import get_settings
from app.permissions import require_permission
from app.storage import resolve_file, store_upload_to_tmp, finalize_upload
from app.messaging import enqueue_event

router = APIRouter()
settings = get_settings()

@router.get("/items", response_model=PaginatedCollectionResponse)
def list_items(
    search: str | None = Query(default=None),
    status: CollectionStatus | None = None,
    object_type_id: int | None = None,
    culture_id: int | None = None,
    material_id: int | None = None,
    creator_id: int | None = None,
    location_id: int | None = None,
    acquisition_from: str | None = None,
    acquisition_to: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    sort: str = Query(default="created_at"),
    direction: str = Query(default="desc"),
    db: Session = Depends(get_db),
    _user_id: int = Depends(get_current_user_id),
):

    cache_key = (
        "collection:search:"
        f"{search}:{status}:{object_type_id}:{culture_id}:"
        f"{material_id}:{creator_id}:{location_id}:"
        f"{acquisition_from}:{acquisition_to}:{offset}:{limit}:"
        f"{sort}:{direction}"
    )

    cached = get_json(cache_key)

    if cached:
        return cached

    allowed_sort_columns = {
        "created_at": CollectionItem.created_at,
        "title": CollectionItem.title,
        "accession_number": CollectionItem.accession_number,
        "updated_at": CollectionItem.updated_at,
        "acquisition_date": CollectionItem.acquisition_date,
    }

    statement = select(CollectionItem)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                CollectionItem.accession_number.ilike(term),
                CollectionItem.object_number.ilike(term),
                CollectionItem.title.ilike(term),
                CollectionItem.description.ilike(term),
            )
        )

    if status:
        statement = statement.where(CollectionItem.status == status)

    if object_type_id:
        statement = statement.where(
            CollectionItem.object_type_id == object_type_id
        )

    if culture_id:
        statement = statement.where(
            CollectionItem.culture_id == culture_id
        )

    if material_id:
        statement = statement.join(CollectionItem.materials).where(
            Material.id == material_id
        )

    if creator_id:
        statement = statement.join(CollectionItem.creators).where(
            Creator.id == creator_id
        )

    if location_id:
        statement = statement.where(
            CollectionItem.current_location_id == location_id
        )

    if acquisition_from:
        statement = statement.where(
            CollectionItem.acquisition_date >= acquisition_from
        )

    if acquisition_to:
        statement = statement.where(
            CollectionItem.acquisition_date <= acquisition_to
        )

    count_statement = select(
        func.count()
    ).select_from(statement.distinct().subquery())

    total = db.scalar(count_statement) or 0

    sort_column = allowed_sort_columns.get(
        sort,
        CollectionItem.created_at,
    )

    if direction.lower() == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())

    statement = (
        statement.distinct()
        .offset(offset)
        .limit(limit)
    )

    items = list(db.scalars(statement).all())

    result = {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }

    set_json(cache_key, result, ttl=20)
    return result

@router.post("/items",response_model=CollectionItemResponse,status_code=201,)
def create_item(
    payload: CollectionItemCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:create")),
):
    item = CollectionItem(
        accession_number=payload.accession_number,
        object_number=payload.object_number,
        title=payload.title,
        description=payload.description,
        classification=payload.classification,
        object_type_id=payload.object_type_id,
        culture_id=payload.culture_id,
        period_date=payload.period_date,
        dimensions=payload.dimensions,
        techniques=payload.techniques,
        place_of_origin=payload.place_of_origin,
        acquisition_method=payload.acquisition_method,
        acquisition_date=payload.acquisition_date,
        ownership_status=payload.ownership_status,
        legal_status=payload.legal_status,
        current_condition=payload.current_condition,
        value=payload.value,
        insurance_value=payload.insurance_value,
        notes=payload.notes,
        current_location_id=payload.current_location_id,
        status=CollectionStatus.ACTIVE,
    )

    if payload.object_type_id is not None:
        ot = db.get(ObjectType, payload.object_type_id)
        if ot is None:
            raise HTTPException(status_code=404, detail=f"Unknown object_type_id: {payload.object_type_id}")
        item.object_type = ot

    if payload.culture_id is not None:
        c = db.get(Culture, payload.culture_id)
        if c is None:
            raise HTTPException(status_code=404, detail=f"Unknown culture_id: {payload.culture_id}")
        item.culture = c

    requested_materials = set(payload.material_ids)
    if requested_materials:
        found_materials = set(
            db.scalars(select(Material.id).where(Material.id.in_(requested_materials))).all()
        )
        if missing := requested_materials - found_materials:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown material IDs: {sorted(missing)}",
            )
        item.materials = list(
            db.scalars(select(Material).where(Material.id.in_(requested_materials))).all()
        )
    else:
        item.materials = []

    requested_creators = set(payload.creator_ids)
    if requested_creators:
        found_creators = set(
            db.scalars(select(Creator.id).where(Creator.id.in_(requested_creators))).all()
        )
        if missing := requested_creators - found_creators:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown creator IDs: {sorted(missing)}",
            )
        item.creators = list(
            db.scalars(select(Creator).where(Creator.id.in_(requested_creators))).all()
        )
    else:
        item.creators = []

    db.add(item)
    db.flush()

    db.add(
        CollectionEvent(
            collection_item_id=item.id,
            event_type="ITEM_CREATED",
            event_payload={
                "accession_number": item.accession_number,
                "title": item.title,
            },
            performed_by=user_id,
        )
    )
    
    enqueue_event(
        db,
        "CollectionItemCreated",
        {
            "item_id": str(item.id),
            "title": item.title,
            "accession_number": item.accession_number,
            "user_id": user_id,
        },
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Accession number or object number already exists.",
        )
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    db.refresh(item)

    return item

@router.get("/items/{item_id}", response_model=CollectionItemResponse)
def get_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    item = db.scalar(
        select(CollectionItem).where(CollectionItem.id == item_id)
    )

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    return item

@router.patch("/items/{item_id}", response_model=CollectionItemResponse)
def update_item(
    item_id: UUID,
    payload: CollectionItemUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:update")),
):
    item = db.scalar(
        select(CollectionItem).where(CollectionItem.id == item_id)
    )

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    changes = payload.model_dump(
        exclude_unset=True,
        exclude={"version", "creator_ids", "material_ids"},
    )
    
    if "object_type_id" in changes and changes["object_type_id"] is not None:
        if db.get(ObjectType, changes["object_type_id"]) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown object_type_id: {changes['object_type_id']}",
            )

    if "culture_id" in changes and changes["culture_id"] is not None:
        if db.get(Culture, changes["culture_id"]) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown culture_id: {changes['culture_id']}",
            )

    if payload.material_ids is not None:  # always for create; conditional for update
        requested = set(payload.material_ids)
        found = set(
            db.scalars(select(Material.id).where(Material.id.in_(requested))).all()
        )
        if missing := requested - found:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown material IDs: {sorted(missing)}",
            )
        item.materials = list(
            db.scalars(select(Material).where(Material.id.in_(requested))).all()
        )

    if payload.creator_ids is not None:
        requested = set(payload.creator_ids)
        found = set(
            db.scalars(select(Creator.id).where(Creator.id.in_(requested))).all()
        )
        if missing := requested - found:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown creator IDs: {sorted(missing)}",
            )
        item.creators = list(
            db.scalars(
                select(Creator).where(Creator.id.in_(requested))
            ).all()
        )
        
    result = db.execute(
        update(CollectionItem)
        .where(
            CollectionItem.id == item_id,
            CollectionItem.version == payload.version,
        )
        .values(
            **changes,
            version=CollectionItem.version + 1,
            updated_at=func.now(),
        )
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Collection item was modified by another user.",
        )

    item = db.get(CollectionItem, item_id)

    db.add(
        CollectionEvent(
            collection_item_id=item.id,
            event_type="ITEM_UPDATED",
            event_payload=changes,
            performed_by=user_id,
        )
    )
    
    enqueue_event(
        db,
        "CollectionItemUpdated",
        {
            "item_id": str(item.id),
            "title": item.title,
            "user_id": user_id,
        },
    )

    db.commit()
    
    db.refresh(item)
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    return item

@router.post("/items/{item_id}/acquisitions")
def add_acquisition(
    item_id: UUID,
    payload: AcquisitionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:create")),
):
    item = db.get(CollectionItem, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    acquisition = Acquisition(
        collection_item_id=item.id,
        acquisition_type=payload.acquisition_type,
        acquisition_date=payload.acquisition_date,
        source=payload.source,
        price=payload.price,
        currency=payload.currency,
        legal_documentation=payload.legal_documentation,
        notes=payload.notes,
        responsible_user_id=user_id,
    )

    if not item.acquisition_method:
        item.acquisition_method = payload.acquisition_type

    if not item.acquisition_date:
        item.acquisition_date = payload.acquisition_date

    db.add(acquisition)
    db.add(
        CollectionEvent(
            collection_item_id=item.id,
            event_type="ITEM_ACQUIRED",
            event_payload={
                "acquisition_type": payload.acquisition_type.value,
                "source": payload.source,
            },
            performed_by=user_id,
        )
    )
    
    enqueue_event(
        db,
        "AcquisitionRecorded",
        {
            "item_id": str(item.id),
            "acquisition_id": acquisition.id,
            "acquisition_type": payload.acquisition_type.value,
            "source": payload.source,
            "user_id": user_id,
        },
    )

    db.commit()
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    return {"id": acquisition.id}

@router.post("/items/{item_id}/provenance")
def add_provenance(
    item_id: UUID,
    payload: ProvenanceCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:create")),
):
    item = db.get(CollectionItem, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    record = ProvenanceRecord(
        collection_item_id=item.id,
        **payload.model_dump(),
    )

    db.add(record)
    db.flush()

    db.add(
        CollectionEvent(
            collection_item_id=item.id,
            event_type="PROVENANCE_ADDED",
            event_payload={
                "provenance_id": record.id,
                "previous_owner": record.previous_owner,
            },
            performed_by=user_id,
        )
    )
    
    enqueue_event(
        db,
        "ProvenanceAdded",
        {
            "item_id": str(item.id),
            "provenance_id": record.id,
            "previous_owner": record.previous_owner,
            "user_id": user_id,
        },
    )

    db.commit()
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")
    
    return {"id": record.id}

@router.get("/items/{item_id}/provenance")
def get_provenance(
    item_id: UUID,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    item = db.get(CollectionItem, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    records = db.scalars(
        select(ProvenanceRecord)
        .where(ProvenanceRecord.collection_item_id == item_id)
        .order_by(ProvenanceRecord.start_date.asc().nulls_last())
    ).all()

    return records

@router.post("/locations", status_code=201)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:create")),
):
    if payload.parent_id and not db.get(Location, payload.parent_id):
        raise HTTPException(status_code=404, detail="Parent location not found.")

    location = Location(**payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)

    return location

@router.get("/locations")
def list_locations(
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    return db.scalars(
        select(Location).order_by(Location.name)
    ).all()

@router.post("/items/{item_id}/movements", status_code=201)
def request_movement(
    item_id: UUID,
    payload: MovementRequestCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:move")),
):
    item = db.get(CollectionItem, item_id)
    destination = db.get(Location, payload.to_location_id)

    if not item:
        raise HTTPException(status_code=404, detail="Collection item not found.")

    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found.")

    request = MovementRequest(
        collection_item_id=item.id,
        from_location_id=item.current_location_id,
        to_location_id=payload.to_location_id,
        requested_by=user_id,
        reason=payload.reason,
        status=MovementStatus.REQUESTED,
    )

    db.add(request)
    db.flush()

    db.add(
        CollectionEvent(
            collection_item_id=item.id,
            event_type="MOVEMENT_REQUESTED",
            event_payload={
                "movement_request_id": request.id,
                "from_location_id": item.current_location_id,
                "to_location_id": payload.to_location_id,
            },
            performed_by=user_id,
        )
    )
    
    enqueue_event(
        db,
        "CollectionMovementRequested",
        {
            "item_id": str(item.id),
            "movement_request_id": request.id,
            "from_location_id": request.from_location_id,
            "to_location_id": request.to_location_id,
            "requested_by": user_id,
        },
    )

    db.commit()
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")
    
    return request

@router.get("/movements")
def list_movements(
    movement_status: MovementStatus | None = None,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    statement = select(MovementRequest).order_by(
        MovementRequest.created_at.desc()
    )

    if movement_status:
        statement = statement.where(
            MovementRequest.status == movement_status
        )

    return db.scalars(statement).all()

@router.patch("/movements/{movement_request_id}")
def change_movement_status(
    movement_request_id: int,
    payload: MovementDecision,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:move")),
):
    request = db.get(MovementRequest, movement_request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Movement request not found.")

    current = request.status
    desired = payload.status

    transitions = {
        MovementStatus.REQUESTED: {
            MovementStatus.APPROVED,
            MovementStatus.REJECTED,
            MovementStatus.CANCELLED,
        },
        MovementStatus.APPROVED: {
            MovementStatus.IN_TRANSIT,
            MovementStatus.CANCELLED,
        },
        MovementStatus.IN_TRANSIT: {
            MovementStatus.COMPLETED,
        },
        MovementStatus.REJECTED: set(),
        MovementStatus.COMPLETED: set(),
        MovementStatus.CANCELLED: set(),
    }

    if desired == MovementStatus.APPROVED:
        item = db.get(CollectionItem, request.collection_item_id)

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Collection item not found.",
            )

        request.approved_by = user_id
        request.approved_at = datetime.now(timezone.utc)

    if desired == MovementStatus.COMPLETED:
        item = db.get(CollectionItem, request.collection_item_id)

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Collection item not found.",
            )
            
        item = db.execute(
            select(CollectionItem)
            .where(CollectionItem.id == request.collection_item_id)
            .with_for_update()
        ).scalar_one()
        
        if item.current_location_id != request.from_location_id:
            raise HTTPException(
                status_code=409,
                detail="Collection item location changed since movement request.",
            )

        movement = Movement(
            collection_item_id=item.id,
            from_location_id=item.current_location_id,
            to_location_id=request.to_location_id,
            movement_request_id=request.id,
            moved_by=user_id,
            reason=request.reason,
        )

        item.current_location_id = request.to_location_id
        request.completed_at = datetime.now(timezone.utc)

        destination = db.get(Location, request.to_location_id)
        if destination is None:
            raise HTTPException(status_code=404, detail="Destination location not found.")

        if destination.location_type in {"ROOM", "GALLERY"}:
            item.status = CollectionStatus.ON_DISPLAY
        elif destination.location_type in {"STORAGE_AREA", "BUILDING", "FLOOR"}:
            item.status = CollectionStatus.IN_STORAGE

        db.add(movement)

        db.add(
            CollectionEvent(
                collection_item_id=item.id,
                event_type="ITEM_MOVED",
                event_payload={
                    "from_location_id": request.from_location_id,
                    "to_location_id": request.to_location_id,
                    "movement_request_id": request.id,
                },
                performed_by=user_id,
            )
        )

    request.status = desired
    
    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    event_by_status = {
        MovementStatus.APPROVED: "CollectionMovementApproved",
        MovementStatus.REJECTED: "CollectionMovementRejected",
        MovementStatus.IN_TRANSIT: "CollectionMovementStarted",
        MovementStatus.COMPLETED: "CollectionMovementCompleted",
        MovementStatus.CANCELLED: "CollectionMovementCancelled",
    }

    event_name = event_by_status.get(desired)

    if event_name:
        enqueue_event(
            db,
            event_name,
            {
                "item_id": str(request.collection_item_id),
                "movement_request_id": request.id,
                "from_location_id": request.from_location_id,
                "to_location_id": request.to_location_id,
                "status": desired.value,
                "user_id": user_id,
            },
        )

        if desired == MovementStatus.COMPLETED:
            enqueue_event(
                db,
                "CollectionItemMoved",
                {
                    "item_id": str(request.collection_item_id),
                    "from_location_id": request.from_location_id,
                    "to_location_id": request.to_location_id,
                    "movement_request_id": request.id,
                    "user_id": user_id,
                },
            )

    db.commit()

    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    return request

@router.post(
    "/items/{item_id}/attachments",
    response_model=AttachmentResponse,
)
def upload_attachment(
    item_id: UUID,
    file: UploadFile = File(...),
    image_type: ImageType | None = None,
    photographer: str | None = None,
    caption: str | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("collection:create")),
):
    item = db.get(CollectionItem, item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Collection item not found.",
        )

    (
        tmp_path,
        original_filename,
        stored_filename,
        size_bytes,
        checksum,
        mime_type,
    ) = store_upload_to_tmp(file, "collection")

    attachment = Attachment(
        collection_item_id=item.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_category="collection",
        mime_type=mime_type,
        size_bytes=size_bytes,
        checksum=checksum,
        image_type=image_type,
        photographer=photographer,
        caption=caption,
        uploaded_by=user_id,
    )

    db.add(attachment)

    try:
        db.flush()

        enqueue_event(
            db,
            "AttachmentUploaded",
            {
                "item_id": str(item.id),
                "attachment_id": attachment.id,
                "user_id": user_id,
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        tmp_path.unlink(missing_ok=True)
        raise

    try:
        finalize_upload(
            tmp_path,
            "collection",
            stored_filename,
        )
    except Exception:
        # The database row cannot safely reference a missing file.
        # Delete the committed metadata row if finalization fails.
        try:
            db.delete(attachment)
            db.commit()
        except Exception:
            db.rollback()

        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Attachment could not be finalized.",
        )

    db.refresh(attachment)

    delete_prefix("collection:search:")
    delete_prefix("collection:dashboard:")

    return attachment

@router.get("/items/{item_id}/attachments")
def list_attachments(
    item_id: UUID,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    return db.scalars(
        select(Attachment)
        .where(Attachment.collection_item_id == item_id)
        .order_by(Attachment.uploaded_at.desc())
    ).all()

@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    attachment = db.get(Attachment, attachment_id)

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")

    file_path = resolve_file(
        attachment.storage_category,
        attachment.stored_filename,
    )

    return FileResponse(
        file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )

@router.get("/items/{item_id}/qr")
def item_qr(
    item_id: UUID,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    if not db.get(CollectionItem, item_id):
        raise HTTPException(
            status_code=404,
            detail="Collection item not found.",
        )

    return generate_item_qr(
        item_id,
        settings.public_frontend_url,
    )

@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("collection:read")),
):
    cache_key = "collection:dashboard:summary"

    cached = get_json(cache_key)
    if cached:
        return cached

    from app.dashboard import get_collection_dashboard

    result = get_collection_dashboard(db)
    set_json(cache_key, result, ttl=30)

    return result
