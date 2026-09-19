import hashlib
import mimetypes
import os
import secrets
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, UploadFile, status
from app.core.config import get_settings


settings = get_settings()

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_FILE_SIZE = 15 * 1024 * 1024

def _write_stream_to_path(upload: UploadFile, target: Path) -> tuple[int, str]:
    size = 0
    digest = hashlib.sha256()
    with target.open("wb") as file:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds the maximum allowed size.",
                )
            digest.update(chunk)
            file.write(chunk)
    return size, digest.hexdigest()


def _detect_and_validate_mime(target: Path, declared: str | None) -> str:
    detected = filetype.guess(str(target))
    if detected is None:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unable to determine file content type.",
        )
    if declared and detected.mime != declared:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match declared type.",
        )
    if detected.mime not in ALLOWED_MIME_TYPES:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type.",
        )
    return detected.mime


def store_upload_to_tmp(
    upload: UploadFile,
    category: str,
) -> tuple[Path, str, str, int, str, str]:
    """
    Write to a temp file under the category dir.
    Returns (tmp_path, original_filename, stored_filename, size, checksum, mime_type).
    Call finalize_upload only after DB commit succeeds.
    """
    if category not in {
        "collection",
        "conservation",
        "loans",
        "exhibitions",
        "documents",
    }:
        raise HTTPException(status_code=400, detail="Invalid storage category.")

    declared = upload.content_type or mimetypes.guess_type(upload.filename or "")[0]
    original_filename = sanitize_filename(upload.filename or "file")
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{secrets.token_hex(20)}{suffix}"

    root = storage_root()
    category_dir = (root / category).resolve()
    category_dir.mkdir(parents=True, exist_ok=True)

    # temp name in same directory so rename is atomic on same filesystem
    tmp = tempfile.NamedTemporaryFile(
        dir=category_dir,
        prefix=".upload-",
        suffix=suffix,
        delete=False,
    )
    tmp_path = Path(tmp.name)
    tmp.close()

    try:
        size, checksum = _write_stream_to_path(upload, tmp_path)
        mime_type = _detect_and_validate_mime(tmp_path, declared)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    return tmp_path, original_filename, stored_filename, size, checksum, mime_type


def finalize_upload(tmp_path: Path, category: str, stored_filename: str) -> Path:
    root = storage_root()
    final = (root / category / stored_filename).resolve()
    if root not in final.parents:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid storage path.")
    tmp_path.replace(final)  # atomic on same FS
    return final


def store_upload(upload: UploadFile, category: str) -> tuple[str, str, int, str, str]:
    """Backward-compatible helper: write final file immediately (prefer store_upload_to_tmp). """
    tmp_path, original, stored, size, checksum, mime = store_upload_to_tmp(upload, category)
    finalize_upload(tmp_path, category, stored)
    return original, stored, size, checksum, mime

def storage_root() -> Path:
    root = Path(settings.file_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    for directory in (
        "collection",
        "conservation",
        "loans",
        "exhibitions",
        "documents",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)

    return root


def sanitize_filename(filename: str) -> str:
    filename = Path(filename).name
    clean = "".join(
        character
        if character.isalnum() or character in "._-"
        else "_"
        for character in filename
    )

    return clean[:150] or "file"


def store_upload(
    upload: UploadFile,
    category: str,
) -> tuple[str, str, int, str, str]:
    content_type = upload.content_type or mimetypes.guess_type(
        upload.filename or ""
    )[0]

    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type.",
        )

    if category not in {
        "collection",
        "conservation",
        "loans",
        "exhibitions",
        "documents",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid storage category.",
        )

    original_filename = sanitize_filename(upload.filename or "file")
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{secrets.token_hex(20)}{suffix}"

    root = storage_root()
    target = (root / category / stored_filename).resolve()

    if root not in target.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid storage path.",
        )

    size = 0
    digest = hashlib.sha256()

    with target.open("wb") as file:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)

            if size > MAX_FILE_SIZE:
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds the maximum allowed size.",
                )

            digest.update(chunk)
            file.write(chunk)

    import filetype

    detected = filetype.guess(str(target))
    if detected is None or detected.mime != content_type:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=415,
            detail="File content does not match declared type.",
        )
        
    return (
        original_filename,
        stored_filename,
        size,
        digest.hexdigest(),
        content_type,
    )


def resolve_file(category: str, filename: str) -> Path:
    root = storage_root()
    target = (root / category / Path(filename).name).resolve()

    if root not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return target
