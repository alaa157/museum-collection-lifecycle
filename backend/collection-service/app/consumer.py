import json
import logging
import threading
import time
import pika
from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.collection import CollectionItem, CollectionStatus

logger = logging.getLogger(__name__)
settings = get_settings()
EXCHANGE = "museum.events"
QUEUE = "collection-conservation-sync"


def _apply_conservation_started(payload: dict):
    item_id = payload.get("collection_item_id")

    if not item_id:
        raise ValueError(
            "ConservationStarted missing collection_item_id"
        )

    db = SessionLocal()

    try:
        item = db.get(CollectionItem, item_id)

        if not item:
            raise ValueError(
                f"Collection item {item_id} not found"
            )

        if item.status == CollectionStatus.UNDER_CONSERVATION:
            return

        if item.status in {
            CollectionStatus.ON_LOAN,
            CollectionStatus.MISSING,
            CollectionStatus.DEACCESSIONED,
        }:
            raise ValueError(
                f"Collection item {item_id} cannot enter conservation "
                f"from status {item.status}"
            )

        item.previous_status = item.status
        item.status = CollectionStatus.UNDER_CONSERVATION

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def _apply_conservation_completed(payload: dict):
    item_id = payload.get("collection_item_id")

    if not item_id:
        raise ValueError(
            "ConservationCompleted missing collection_item_id"
        )

    db = SessionLocal()

    try:
        item = db.get(CollectionItem, item_id)

        if not item:
            raise ValueError(
                f"Collection item {item_id} not found"
            )

        if item.status != CollectionStatus.UNDER_CONSERVATION:
            # Idempotent handling:
            # an already-restored item is not a persistence failure.
            if item.previous_status is None:
                return

            raise ValueError(
                f"Collection item {item_id} is not under conservation"
            )

        restored_status = (
            item.previous_status
            or CollectionStatus.ACTIVE
        )

        item.status = restored_status
        item.previous_status = None

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        
def _set_items_on_loan(payload: dict):
    ids = payload.get("collection_item_ids") or []

    if not ids:
        raise ValueError(
            "LoanActivated missing collection_item_ids"
        )

    db = SessionLocal()

    try:
        for raw_id in ids:
            item = db.get(CollectionItem, raw_id)

            if not item:
                raise ValueError(
                    f"Collection item {raw_id} not found"
                )

            if item.status in {
                CollectionStatus.MISSING,
                CollectionStatus.DEACCESSIONED,
            }:
                raise ValueError(
                    f"Collection item {raw_id} cannot be placed on loan "
                    f"from status {item.status}"
                )

            if item.status != CollectionStatus.ON_LOAN:
                item.previous_status = item.status
                item.status = CollectionStatus.ON_LOAN

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
def _restore_items_from_loan(payload: dict):
    ids = payload.get("collection_item_ids") or []

    if not ids:
        raise ValueError(
            "LoanReturned missing collection_item_ids"
        )

    db = SessionLocal()

    try:
        for raw_id in ids:
            item = db.get(CollectionItem, raw_id)

            if not item:
                raise ValueError(
                    f"Collection item {raw_id} not found"
                )

            if item.status != CollectionStatus.ON_LOAN:
                continue

            item.status = (
                item.previous_status
                or CollectionStatus.ACTIVE
            )

            item.previous_status = None

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

HANDLERS = {
    "ConservationStarted": _apply_conservation_started,
    "ConservationCompleted": _apply_conservation_completed,
    "LoanActivated": _set_items_on_loan,
    "LoanReturned": _restore_items_from_loan,
}


def consume():
    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.rabbitmq_host,
                    port=settings.rabbitmq_port,
                    credentials=pika.PlainCredentials(
                        settings.rabbitmq_user,
                        settings.rabbitmq_password,
                    ),
                    heartbeat=30,
                )
            )
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE, durable=True)
            for key in HANDLERS:
                channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=key)

            def callback(ch, method, properties, body):
                try:
                    message = json.loads(body)
            
                    event_name = (
                        message.get("event_type")
                        or message.get("event_name")
                    )
            
                    if not event_name:
                        raise ValueError(
                            "Missing event_type/event_name"
                        )
            
                    handler = HANDLERS.get(event_name)
            
                    if handler is None:
                        # Unknown event for this consumer is not a processing error.
                        ch.basic_ack(
                            delivery_tag=method.delivery_tag
                        )
                        return
            
                    handler(
                        message.get("payload") or {}
                    )
            
                    ch.basic_ack(
                        delivery_tag=method.delivery_tag
                    )
            
                except json.JSONDecodeError:
                    logger.exception(
                        "Malformed collection event"
                    )
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False,
                    )
            
                except ValueError:
                    logger.exception(
                        "Invalid collection event contract"
                    )
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False,
                    )
            
                except Exception:
                    logger.exception(
                        "Collection event persistence failed"
                    )
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True,
                    )

            channel.basic_qos(prefetch_count=20)
            channel.basic_consume(queue=QUEUE, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            logger.exception("Collection conservation consumer disconnected; retrying")
            time.sleep(5)
        finally:
            if connection and not connection.is_closed:
                connection.close()


def start_consumer():
    threading.Thread(target=consume, name="collection-conservation-consumer", daemon=True).start()