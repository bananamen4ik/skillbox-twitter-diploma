"""Logic functionality with medias."""

from mimetypes import guess_extension

from pathlib import Path

from aiofiles import open as aiofiles_open
from aiofiles.threadpool.binary import AsyncBufferedIOBase

from fastapi import UploadFile

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.medias import Media
from app.config import settings
from app.schemas.medias import MediaSchema
from app.crud.medias import (
    create_media,
    get_media_by_id
)


async def upload_image(
        session: AsyncSession,
        user_id: int,
        image_file: UploadFile
) -> MediaSchema | None:
    """Upload image."""
    upload_dir: Path = settings.path_images

    if (
            image_file.content_type is None or
            not image_file.content_type.startswith("image/")
    ):
        return None

    file_ext: str | None = guess_extension(image_file.content_type)
    if file_ext is None:
        return None

    media: Media | None = await create_media(
        session,
        Media(
            ext=file_ext[1:],
            user_id=user_id
        )
    )
    if media is None:
        return None

    media_filename: str = f"{media.id}{file_ext}"

    await save_media(
        image_file,
        upload_dir / media_filename
    )

    try:
        await session.commit()
    except SQLAlchemyError:  # pragma: no cover
        Path(upload_dir / media_filename).unlink()
        return None

    return MediaSchema.model_validate(media)


async def save_media(
        media_file: UploadFile,
        path_to: str | Path
) -> None:
    """Save image file to path."""
    buffer: AsyncBufferedIOBase

    async with aiofiles_open(path_to, "wb") as buffer:
        content_file: bytes = await media_file.read(1024)
        while content_file:
            await buffer.write(content_file)
            content_file = await media_file.read(1024)


async def delete_media_files(media_filenames: list[str]) -> None:
    """Delete media files by media filenames."""
    media_filename: str
    path_to_medias: Path = settings.path_images

    for media_filename in media_filenames:
        path_to_file: Path = path_to_medias / media_filename
        path_to_file.unlink()


async def get_media_filename_by_id(
        session: AsyncSession,
        media_id: int
) -> str | None:
    """Get media filename by media id."""
    media: Media | None = await get_media_by_id(
        session,
        media_id
    )

    if media is None:
        return None

    return f"{media.id}.{media.ext}"
