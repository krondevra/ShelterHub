"""Animal photo storage on disk.

Files live under ``UPLOAD_DIR/animals`` and are served by the ``/uploads``
static mount in ``main.py``. The database only stores the file name
(``Animal.photo_path``), never the bytes.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", Path(__file__).resolve().parent.parent / "uploads"))
ANIMAL_PHOTO_DIR = UPLOAD_DIR / "animals"

MAX_PHOTO_BYTES = 5 * 1024 * 1024
_CHUNK_BYTES = 64 * 1024


def ensure_upload_dirs() -> None:
    ANIMAL_PHOTO_DIR.mkdir(parents=True, exist_ok=True)


def _image_extension(head: bytes) -> str | None:
    """Detect the format from the file's first bytes, not from its name or the
    client-supplied Content-Type, which are both trivial to fake."""
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


def save_animal_photo(animal_id: int, upload: UploadFile) -> str:
    """Validate and store an uploaded photo. Returns the stored file name.

    Raises 415 for anything that is not JPEG/PNG/WebP and 413 as soon as more
    than ``MAX_PHOTO_BYTES`` have been read.
    """
    head = upload.file.read(_CHUNK_BYTES)
    extension = _image_extension(head)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Photo must be a JPEG, PNG or WebP image",
        )

    ensure_upload_dirs()
    file_name = f"{animal_id}-{uuid4().hex}{extension}"
    target = ANIMAL_PHOTO_DIR / file_name
    size = 0
    try:
        with target.open("wb") as out:
            chunk = head
            while chunk:
                size += len(chunk)
                if size > MAX_PHOTO_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Photo must be at most 5 MB",
                    )
                out.write(chunk)
                chunk = upload.file.read(_CHUNK_BYTES)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return file_name


def delete_animal_photo(file_name: str | None) -> None:
    if file_name:
        (ANIMAL_PHOTO_DIR / file_name).unlink(missing_ok=True)
