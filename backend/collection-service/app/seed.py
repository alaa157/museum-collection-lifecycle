from datetime import date
from app.db.session import SessionLocal
from app.models.collection import (
    Acquisition,
    AcquisitionType,
    CollectionItem,
    CollectionStatus,
    Creator,
    Culture,
    Location,
    Material,
    ObjectType,
    ProvenanceRecord,
)


def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()

    if instance:
        return instance

    instance = model(**filters, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance


def seed():
    db = SessionLocal()

    try:
        painting = get_or_create(
            db,
            ObjectType,
            name="Painting",
            defaults={
                "description": "Two-dimensional painted work",
            },
        )

        sculpture = get_or_create(
            db,
            ObjectType,
            name="Sculpture",
            defaults={
                "description": "Three-dimensional sculptural work",
            },
        )

        manuscript = get_or_create(
            db,
            ObjectType,
            name="Manuscript",
            defaults={
                "description": "Historical written document",
            },
        )

        egyptian = get_or_create(
            db,
            Culture,
            name="Nile Valley",
            defaults={"region": "Upper and Lower Egypt"},
        )

        mediterranean = get_or_create(
            db,
            Culture,
            name="Mediterranean",
            defaults={"region": "Eastern Mediterranean"},
        )

        oil = get_or_create(
            db,
            Material,
            name="Oil on canvas",
        )

        limestone = get_or_create(
            db,
            Material,
            name="Limestone",
        )

        papyrus = get_or_create(
            db,
            Material,
            name="Papyrus",
        )

        creator_a = get_or_create(
            db,
            Creator,
            name="Nadia El-Masry",
            defaults={
                "birth_year": 1938,
                "death_year": 2007,
                "nationality": "Egyptian",
            },
        )

        creator_b = get_or_create(
            db,
            Creator,
            name="Omar Farid",
            defaults={
                "birth_year": 1962,
                "nationality": "Egyptian",
            },
        )

        museum = get_or_create(
            db,
            Location,
            name="Central Museum",
            defaults={"location_type": "MUSEUM"},
        )

        building = get_or_create(
            db,
            Location,
            name="Collections Building",
            defaults={
                "location_type": "BUILDING",
                "parent_id": museum.id,
            },
        )

        floor = get_or_create(
            db,
            Location,
            name="Floor 2",
            defaults={
                "location_type": "FLOOR",
                "parent_id": building.id,
            },
        )

        storage_room = get_or_create(
            db,
            Location,
            name="Secure Storage Room B",
            defaults={
                "location_type": "STORAGE_AREA",
                "parent_id": floor.id,
            },
        )

        gallery = get_or_create(
            db,
            Location,
            name="Gallery 4 — Mediterranean Arts",
            defaults={
                "location_type": "ROOM",
                "parent_id": floor.id,
            },
        )

        existing = db.query(CollectionItem).count()

        if existing == 0:
            item_1 = CollectionItem(
                accession_number="MCLP-2018-0042",
                object_number="PAINT-0042",
                title="Evening Along the Canal",
                description=(
                    "An atmospheric oil painting depicting a quiet canal "
                    "and surrounding architectural forms."
                ),
                classification="European-influenced modern painting",
                object_type_id=painting.id,
                culture_id=mediterranean.id,
                current_location_id=gallery.id,
                period_date="1974",
                dimensions={
                    "height_cm": 81.0,
                    "width_cm": 104.0,
                    "depth_cm": 4.0,
                },
                techniques="Oil painting with layered glazing",
                place_of_origin="Alexandria",
                acquisition_method=AcquisitionType.DONATION,
                acquisition_date=date(2018, 3, 14),
                ownership_status="OWNED",
                legal_status="Clear title",
                current_condition="Stable",
                value=185000,
                insurance_value=210000,
                notes="Display approved.",
                status=CollectionStatus.ON_DISPLAY,
                creators=[creator_a],
                materials=[oil],
            )

            item_2 = CollectionItem(
                accession_number="MCLP-2021-0178",
                object_number="SCULP-0178",
                title="Guardian Figure",
                description=(
                    "Limestone sculptural figure from a fictional "
                    "Mediterranean collection context."
                ),
                classification="Stone sculpture",
                object_type_id=sculpture.id,
                culture_id=egyptian.id,
                current_location_id=storage_room.id,
                period_date="20th century",
                dimensions={
                    "height_cm": 63.0,
                    "width_cm": 28.0,
                    "depth_cm": 21.0,
                },
                techniques="Carved limestone",
                place_of_origin="Upper Egypt",
                acquisition_method=AcquisitionType.PURCHASE,
                acquisition_date=date(2021, 9, 9),
                ownership_status="OWNED",
                legal_status="Clear title",
                current_condition="Good",
                value=72000,
                insurance_value=85000,
                notes="Scheduled for conservation review.",
                status=CollectionStatus.IN_STORAGE,
                creators=[creator_b],
                materials=[limestone],
            )

            item_3 = CollectionItem(
                accession_number="MCLP-2023-0315",
                object_number="MS-0315",
                title="Letters from the Coastal Archive",
                description=(
                    "Bound manuscript containing a fictional series of "
                    "correspondence records."
                ),
                classification="Historical manuscript",
                object_type_id=manuscript.id,
                culture_id=mediterranean.id,
                current_location_id=storage_room.id,
                period_date="1891–1897",
                dimensions={
                    "height_cm": 24.0,
                    "width_cm": 18.0,
                    "depth_cm": 4.5,
                },
                techniques="Ink on papyrus and later paper leaves",
                place_of_origin="Port Alexandria",
                acquisition_method=AcquisitionType.BEQUEST,
                acquisition_date=date(2023, 5, 22),
                ownership_status="OWNED",
                legal_status="Research restricted",
                current_condition="Fragile",
                value=46000,
                insurance_value=60000,
                notes="Controlled handling required.",
                status=CollectionStatus.IN_STORAGE,
                materials=[papyrus],
            )

            db.add_all([item_1, item_2, item_3])
            db.flush()

            db.add_all(
                [
                    Acquisition(
                        collection_item_id=item_1.id,
                        acquisition_type=AcquisitionType.DONATION,
                        acquisition_date=date(2018, 3, 14),
                        source="Alexandria Cultural Foundation",
                        notes="Gift accession.",
                        responsible_user_id=1,
                    ),
                    Acquisition(
                        collection_item_id=item_2.id,
                        acquisition_type=AcquisitionType.PURCHASE,
                        acquisition_date=date(2021, 9, 9),
                        source="Mediterranean Heritage Exchange",
                        price=72000,
                        currency="USD",
                        responsible_user_id=1,
                    ),
                    Acquisition(
                        collection_item_id=item_3.id,
                        acquisition_type=AcquisitionType.BEQUEST,
                        acquisition_date=date(2023, 5, 22),
                        source="El-Hadid Family Archive",
                        responsible_user_id=1,
                    ),
                ]
            )

            db.add_all(
                [
                    ProvenanceRecord(
                        collection_item_id=item_1.id,
                        previous_owner="Alexandria Cultural Foundation",
                        ownership_period="2010–2018",
                        acquisition_source="Documented donation",
                        transaction_type="DONATION",
                        record_date=date(2018, 3, 14),
                        start_date=date(2010, 1, 1),
                        geographic_location="Alexandria",
                    ),
                    ProvenanceRecord(
                        collection_item_id=item_2.id,
                        previous_owner="Mediterranean Heritage Exchange",
                        ownership_period="2002–2021",
                        acquisition_source="Purchase documentation",
                        transaction_type="PURCHASE",
                        record_date=date(2021, 9, 9),
                        geographic_location="Cairo",
                    ),
                ]
            )

        db.commit()

        print("Collection seed completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
