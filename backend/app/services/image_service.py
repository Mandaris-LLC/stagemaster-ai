import asyncio
import base64
import io
import logging

import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _fetch_and_encode_image(image_url: str) -> tuple[str, str, int, int]:
    """
    Helper to fetch image from URL (handling internal/MinIO URLs).
    - Resizes image if either dimension > 2160px.
    - Returns (media_type, base64_string, width, height).
    """
    image_content = None
    from app.services.storage import storage_service

    internal_prefix = f"{storage_service.get_protocol()}://{settings.STORAGE_ENDPOINT}/"
    public_prefix = f"{storage_service.get_protocol()}://{settings.STORAGE_PUBLIC_ENDPOINT}/"

    target_prefix = None
    if image_url.startswith(internal_prefix):
        target_prefix = internal_prefix
    elif image_url.startswith(public_prefix):
        target_prefix = public_prefix

    if target_prefix:
        path_parts = image_url.replace(target_prefix, "").split("/", 1)
        if len(path_parts) == 2:
            bucket, object_name = path_parts
            image_content = storage_service.get_object_data(bucket, object_name)

    if image_content is None:
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_content = image_response.content

    try:
        with Image.open(io.BytesIO(image_content)) as img:
            width, height = img.size
            if width > 2160 or height > 2160:
                img.thumbnail((2160, 2160), Image.Resampling.LANCZOS)
                width, height = img.size

                buffer = io.BytesIO()
                fmt = img.format if img.format else "JPEG"
                img.save(buffer, format=fmt)
                image_content = buffer.getvalue()

            media_type = "image/jpeg"
            if img.format == "PNG":
                media_type = "image/png"
            elif img.format == "WEBP":
                media_type = "image/webp"

            image_base64 = base64.b64encode(image_content).decode("utf-8")
            return media_type, image_base64, width, height

    except Exception as e:
        logger.error(f"Error processing image with Pillow: {e}")
        image_base64 = base64.b64encode(image_content).decode("utf-8")
        return "image/jpeg", image_base64, 0, 0


async def generate_image_v1(
    prompt: str,
    original_image_url: str | None = None,
    fix_white_balance: bool = False,
    reference_image_url: str | None = None,
) -> bytes:
    """
    Generates an image using OpenRouter (Gemini chat completions with image modality).
    Returns the raw binary content of the generated image.
    """
    try:
        api_key = settings.OPENROUTER_API_KEY
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://stage-master.app",
            "X-Title": "Stage Master",
        }

        model = settings.LITELLM_GENERATION_MODEL
        if model.startswith("openrouter/"):
            model = model.replace("openrouter/", "")

        messages_content = []
        orig_width, orig_height = 0, 0

        # 1. Reference Image (Context ONLY) - FIRST
        if reference_image_url:
            messages_content.append(
                {
                    "type": "text",
                    "text": "\n\nCONSISTENCY REFERENCE (Staged Angle):\nThis image shows the EXISTING furniture and style from another angle of the same room.\nUse this ONLY to identify the inventory of items to be placed (materials, styles, exact objects).\nDo NOT copy the camera angle, wall positions, or room geometry from this reference.",
                }
            )
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages_content.append(
                {"type": "image_url", "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}}
            )

        # 2. Target Image (THE MASTER BACKGROUND) - SECOND & FINAL
        if original_image_url:
            messages_content.append(
                {
                    "type": "text",
                    "text": "THE TARGET IMAGE (IMMUTABLE BACKGROUND):\nThis is the room photograph you are editing. The following are LOCKED and must appear at their EXACT pixel positions in your output:\n- Every wall edge, corner, and angle\n- Every door, doorway, and archway (position, size, open/closed state)\n- Every window (position, size, view through it)\n- All ceiling fixtures (lights, fans, vents)\n- All wall fixtures (outlets, switches, thermostats)\n- The camera angle, height, tilt, and lens perspective\n- The floor plane and ceiling line\nDo NOT move, warp, resize, crop, or alter ANY of these elements.",
                }
            )
            media_type, image_base64, width, height = await _fetch_and_encode_image(original_image_url)
            orig_width, orig_height = width, height
            messages_content.append(
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_base64}"}}
            )

            extra_text = f"\n\nEDIT TASK: OVERLAY FURNITURE INTO THIS EXACT ROOM\n{prompt}"
            extra_text += "\n\nROOM PRESERVATION RULES:"
            extra_text += "\n- Walls must remain at their exact angles and positions"
            extra_text += "\n- Doors and doorways must remain fully visible and unblocked by furniture"
            extra_text += "\n- Windows must remain fully visible and unobscured"
            extra_text += "\n- All ceiling and wall fixtures must remain visible"
            extra_text += "\n- Furniture must sit on the existing floor plane with correct perspective"
            extra_text += "\n- Furniture shadows must match the room's existing light direction"

            if width > 0 and height > 0:
                extra_text += f"\n\nRESOLUTION LOCK: Output MUST be exactly {width}x{height} pixels."

            if not fix_white_balance:
                extra_text += "\n\nWHITE BALANCE LOCK: Preserve the original color temperature exactly."

            extra_text += "\n\nFAILURE CONDITIONS: Any of the following in the output means the image is REJECTED:"
            extra_text += "\n- A door or doorway has moved, disappeared, or is blocked by furniture"
            extra_text += "\n- A wall angle or corner position has shifted"
            extra_text += "\n- A window has moved or is obscured"
            extra_text += "\n- The camera angle, height, or perspective has changed"
            extra_text += "\n- Any ceiling or wall fixture is missing or altered"

            messages_content.append({"type": "text", "text": extra_text})

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": messages_content}],
            "modalities": ["image", "text"],
        }

        logger.info(f"Calling OpenRouter Chat API for image generation with model: {model}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()

        if not result.get("choices"):
            raise ValueError(f"No choices in response: {result}")

        message = result["choices"][0]["message"]

        image_url = None
        if message.get("images"):
            image_url = message["images"][0]["image_url"]["url"]

        if not image_url:
            logger.error(f"Full response message: {message}")
            raise ValueError("No image URL found in response")

        if image_url.startswith("data:"):
            header, encoded = image_url.split(",", 1)
            generated_bytes = base64.b64decode(encoded)
        else:
            async with httpx.AsyncClient() as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                generated_bytes = img_resp.content

        if orig_width > 0 and orig_height > 0:
            with Image.open(io.BytesIO(generated_bytes)) as gen_img:
                if gen_img.size != (orig_width, orig_height):
                    logger.info(f"Resizing generated image from {gen_img.size} to ({orig_width}, {orig_height})")
                    gen_img = gen_img.resize((orig_width, orig_height), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                gen_img.save(buffer, format="JPEG")
                generated_bytes = buffer.getvalue()

        return generated_bytes

    except Exception as e:
        logger.error(f"Error generating image via OpenRouter: {str(e)}")
        raise


async def generate_image_v2(
    prompt: str,
    original_image_url: str | None = None,
    fix_white_balance: bool = False,
    reference_image_url: str | None = None,
) -> bytes:
    """
    Generates an image using Vertex AI Imagen with RawReferenceImage support.
    Returns the raw binary content of the generated image.
    """
    try:
        import json

        import vertexai
        from vertexai.preview.vision_models import (
            Image as VertexImage,
            ImageGenerationModel,
            RawReferenceImage,
        )

        credentials = None
        projectId = settings.GOOGLE_CLOUD_PROJECT
        if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
            from google.oauth2 import service_account

            json_creds = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
            projectId = json_creds.get("project_id", projectId)
            credentials = service_account.Credentials.from_service_account_info(
                json_creds,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )

        vertexai.init(
            project=projectId,
            location=settings.GOOGLE_CLOUD_LOCATION,
            credentials=credentials,
        )

        generation_model = ImageGenerationModel.from_pretrained(settings.VERTEX_IMAGEN_MODEL)

        reference_images = []
        orig_width, orig_height = 0, 0
        ref_id = 1

        if original_image_url:
            _, image_base64, orig_width, orig_height = await _fetch_and_encode_image(original_image_url)
            reference_images.append(
                RawReferenceImage(
                    reference_id=ref_id,
                    image=VertexImage(image_bytes=base64.b64decode(image_base64)),
                )
            )
            ref_id += 1

        if reference_image_url:
            _, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            reference_images.append(
                RawReferenceImage(
                    reference_id=ref_id,
                    image=VertexImage(image_bytes=base64.b64decode(ref_image_base64)),
                )
            )

        full_prompt = prompt

        if original_image_url:
            full_prompt += "\n\nTHE TARGET IMAGE (IMMUTABLE BACKGROUND):"
            full_prompt += "\nThis is the room photograph you are editing. The following are LOCKED and must appear at their EXACT pixel positions in your output:"
            full_prompt += "\n- Every wall edge, corner, and angle"
            full_prompt += "\n- Every door, doorway, and archway (position, size, open/closed state)"
            full_prompt += "\n- Every window (position, size, view through it)"
            full_prompt += "\n- All ceiling fixtures (lights, fans, vents)"
            full_prompt += "\n- All wall fixtures (outlets, switches, thermostats)"
            full_prompt += "\n- The camera angle, height, tilt, and lens perspective"
            full_prompt += "\n- The floor plane and ceiling line"
            full_prompt += "\nDo NOT move, warp, resize, crop, or alter ANY of these elements."

            if not fix_white_balance:
                full_prompt += "\n\nWHITE BALANCE LOCK: Preserve the original color temperature exactly."

        if reference_image_url:
            full_prompt += "\n\nCONSISTENCY REFERENCE (Staged Angle): The second reference image shows existing furniture and style from another angle of the same room. Use it ONLY to match materials, styles, and object inventory. Do NOT copy its camera angle, wall positions, or room geometry."

        logger.info(f"Calling Vertex AI Imagen ({settings.VERTEX_IMAGEN_MODEL}) for image generation")

        possible_aspect_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        if orig_width > 0 and orig_height > 0:
            target_ratio = orig_width / orig_height
            aspect_ratio = min(
                possible_aspect_ratios,
                key=lambda r: abs((int(r.split(":")[0]) / int(r.split(":")[1])) - target_ratio),
            )
        else:
            aspect_ratio = "1:1"

        logger.info(f"Selected aspect ratio {aspect_ratio} for original size {orig_width}x{orig_height}")

        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            lambda: generation_model._generate_images(
                prompt=full_prompt,
                number_of_images=1,
                negative_prompt="distorted walls, moved doors, changed camera angle, altered room geometry, shifted windows",
                aspect_ratio=aspect_ratio,
                person_generation="dont_allow",
                safety_filter_level="",
                reference_images=reference_images if reference_images else None,
            ),
        )

        generated_bytes = images[0]._image_bytes

        if orig_width > 0 and orig_height > 0:
            with Image.open(io.BytesIO(generated_bytes)) as gen_img:
                if gen_img.size != (orig_width, orig_height):
                    logger.info(f"Resizing generated image from {gen_img.size} to ({orig_width}, {orig_height})")
                    gen_img = gen_img.resize((orig_width, orig_height), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                gen_img.save(buffer, format="JPEG")
                generated_bytes = buffer.getvalue()

        return generated_bytes

    except Exception as e:
        logger.error(f"Error generating image via Vertex AI: {str(e)}")
        raise


async def generate_image(
    prompt: str,
    original_image_url: str | None = None,
    fix_white_balance: bool = False,
    reference_image_url: str | None = None,
    model: str = "v2",
) -> bytes:
    """
    Generates a staged room image.

    Args:
        model: "v1" uses OpenRouter, "v2" uses Vertex AI Imagen (default).
    """
    if model == "v1":
        return await generate_image_v1(prompt, original_image_url, fix_white_balance, reference_image_url)
    return await generate_image_v2(prompt, original_image_url, fix_white_balance, reference_image_url)
