import base64
import io
import logging
import mimetypes

import requests
from fastapi import UploadFile

from open_webui.config import CACHE_DIR

from open_webui.models.chats import Chats
from open_webui.routers.files import upload_file_handler

log = logging.getLogger(__name__)

IMAGE_CACHE_DIR = CACHE_DIR / "image" / "generations"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_image_data(data: str, headers=None):
    try:
        if data.startswith("http://") or data.startswith("https://"):
            if headers:
                r = requests.get(data, headers=headers)
            else:
                r = requests.get(data)

            r.raise_for_status()
            if r.headers["content-type"].split("/")[0] == "image":
                mime_type = r.headers["content-type"]
                return r.content, mime_type
            else:
                log.error("Url does not point to an image.")
                return None
        else:
            if "," in data:
                header, encoded = data.split(",", 1)
                mime_type = header.split(";")[0].lstrip("data:")
                img_data = base64.b64decode(encoded)
            else:
                mime_type = "image/png"
                img_data = base64.b64decode(data)
            return img_data, mime_type
    except Exception as e:
        log.exception(f"Error loading image data: {e}")
        return None, None


def upload_image(request, image_data, content_type, metadata, user):
    image_format = mimetypes.guess_extension(content_type)
    file = UploadFile(
        file=io.BytesIO(image_data),
        filename=f"generated-image{image_format}",  # will be converted to a unique ID on upload_file
        headers={
            "content-type": content_type,
        },
    )
    file_item = upload_file_handler(
        request,
        file=file,
        metadata=metadata,
        process=False,
        user=user,
    )

    if file_item and file_item.id:
        # If chat_id and message_id are provided in metadata, link the file to the chat message
        chat_id = metadata.get("chat_id")
        message_id = metadata.get("message_id")

        if chat_id and message_id:
            Chats.insert_chat_files(
                chat_id=chat_id,
                message_id=message_id,
                file_ids=[file_item.id],
                user_id=user.id,
            )

    url = request.app.url_path_for("get_file_content_by_id", id=file_item.id)
    return file_item, url
