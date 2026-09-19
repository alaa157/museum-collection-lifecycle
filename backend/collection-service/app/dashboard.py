from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.collection import (
    CollectionItem,
    CollectionStatus,
    Material,
    ObjectType,
)


def get_collection_dashboard(db: Session) -> dict:
    total = db.scalar(
        select(func.count()).select_from(CollectionItem)
    ) or 0

    status_rows = db.execute(
        select(
            CollectionItem.status,
            func.count(CollectionItem.id),
        ).group_by(CollectionItem.status)
    ).all()

    type_rows = db.execute(
        select(
            ObjectType.name,
            func.count(CollectionItem.id),
        )
        .join(CollectionItem, CollectionItem.object_type_id == ObjectType.id)
        .group_by(ObjectType.name)
        .order_by(func.count(CollectionItem.id).desc())
        .limit(10)
    ).all()

    material_rows = db.execute(
        select(
            Material.name,
            func.count(CollectionItem.id),
        )
        .join(CollectionItem.materials)
        .group_by(Material.name)
        .order_by(func.count(CollectionItem.id).desc())
        .limit(10)
    ).all()

    by_status = {
        status.value if hasattr(status, "value") else status: count
        for status, count in status_rows
    }

    return {
        "total_items": total,
        "on_display": by_status.get(CollectionStatus.ON_DISPLAY.value, 0),
        "in_storage": by_status.get(CollectionStatus.IN_STORAGE.value, 0),
        "on_loan": by_status.get(CollectionStatus.ON_LOAN.value, 0),
        "under_conservation": by_status.get(
            CollectionStatus.UNDER_CONSERVATION.value,
            0,
        ),
        "missing": by_status.get(CollectionStatus.MISSING.value, 0),
        "deaccessioned": by_status.get(
            CollectionStatus.DEACCESSIONED.value,
            0,
        ),
        "by_status": [
            {"name": name, "value": count}
            for name, count in by_status.items()
        ],
        "by_object_type": [
            {"name": name, "value": count}
            for name, count in type_rows
        ],
        "by_material": [
            {"name": name, "value": count}
            for name, count in material_rows
        ],
    }
