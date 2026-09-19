from io import BytesIO
from uuid import UUID

import qrcode
from fastapi.responses import StreamingResponse


def generate_item_qr(item_id: UUID, base_url: str):
    target = f"{base_url.rstrip('/')}/collection/{item_id}"

    qr = qrcode.QRCode(
        version=None,
        box_size=10,
        border=4,
    )

    qr.add_data(target)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition":
                f'inline; filename="collection-{item_id}.png"'
        },
    )