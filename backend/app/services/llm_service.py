import litellm
import logging
import asyncio
import base64
import httpx
from typing import cast
from litellm import ModelResponse
from litellm.types.utils import Choices
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure litellm
litellm.telemetry = False

import io
from PIL import Image

# ... (imports)

async def _fetch_and_encode_image(image_url: str) -> tuple[str, str, int, int]:
    """
    Helper to fetch image from URL (handling internal/MinIO URLs).
    - Resizes image if either dimension > 2160px.
    - Returns (media_type, base64_string, width, height).
    """
    # Fetch image content
    image_content = None
    
    internal_prefix = f"http://{settings.STORAGE_ENDPOINT}/"
    public_prefix = f"http://{settings.STORAGE_PUBLIC_ENDPOINT}/"
    
    target_prefix = None
    if image_url.startswith(internal_prefix):
        target_prefix = internal_prefix
    elif image_url.startswith(public_prefix):
        target_prefix = public_prefix
        
    if target_prefix:
        from app.services.storage import storage_service
        path_parts = image_url.replace(target_prefix, "").split("/", 1)
        if len(path_parts) == 2:
            bucket, object_name = path_parts
            image_content = storage_service.get_object_data(bucket, object_name)
    
    if image_content is None:
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_content = image_response.content

    # Process image with Pillow
    try:
        with Image.open(io.BytesIO(image_content)) as img:
            width, height = img.size
            if width > 2160 or height > 2160:
                img.thumbnail((2160, 2160), Image.Resampling.LANCZOS)
                width, height = img.size
                
                # Save resized image to buffer
                buffer = io.BytesIO()
                # Determine format
                fmt = img.format if img.format else 'JPEG'
                img.save(buffer, format=fmt)
                image_content = buffer.getvalue()
                
            media_type = "image/jpeg"
            if img.format == 'PNG':
                media_type = "image/png"
            elif img.format == 'WEBP':
                media_type = "image/webp"

            image_base64 = base64.b64encode(image_content).decode('utf-8')
            return media_type, image_base64, width, height
            
    except Exception as e:
        logger.error(f"Error processing image with Pillow: {e}")
        # Fallback to original content if Pillow fails, assuming jpeg
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        return "image/jpeg", image_base64, 0, 0

async def analyze_room(image_url: str, reference_image_url: str | None = None, reference_analysis: str | None = None) -> str:
    """
    Analyzes room layout, surfaces, and depth using LiteLLM/OpenRouter.
    Returns a text description of the room analysis.
    If reference_image_url/reference_analysis is provided, it uses it to maintain consistency.
    """
    consistency_instruction = ""
    if reference_image_url:
        consistency_instruction = f"""
        CRITICAL ARCHITECTURAL ANCHORING:
        This is the SAME room as shown in the reference: {reference_image_url}.
        1. DEFINE ROTATION: Conclude if this Target Angle is Same-Side, Side-Wall, or Opposite-Side (~180).
        2. CHOOSE 2 ANCHORS: Identify two fixed landmarks (e.g., "The Large Window" and "The Far Corner") visible or implied in both views.
        3. SPATIAL PROJECTION: Map the furniture relative to these Anchors. If the "Large Window" moved from Left to Right, the furniture near it MUST follow the window to the Right.
        """
        if reference_analysis:
            consistency_instruction += f"\nHere is the analysis of that reference view: {reference_analysis}"

    prompt = f"""
    Analyze the uploaded interior photo for virtual staging.
    {consistency_instruction}

    TASK: Produce a precise architectural blueprint of this room. This analysis is the GROUND TRUTH that all subsequent staging steps MUST obey — any deviation from it is a critical failure.

    1. ROOM GEOMETRY & PERSPECTIVE:
       - Describe the exact camera angle (eye-level, elevated, corner shot, straight-on, etc.).
       - Map every wall visible in frame: label them (e.g., Left Wall, Back Wall, Right Wall) and note their angles relative to the camera.
       - Note the ceiling height, floor plane angle, and any perspective vanishing points.

    2. DOORS & OPENINGS (CRITICAL — these must NEVER be blocked, moved, or removed):
       - List EVERY door, doorway, archway, and opening visible or partially visible.
       - For each: note its EXACT position (e.g., "centered on the back wall", "far-right of the left wall"), its type (hinged, sliding, pocket, open archway), whether it is open or closed, and its swing direction if visible.
       - Note any hallways or passageways visible through openings.

    3. WINDOWS:
       - List every window with its exact position, size relative to the wall, and type (single-pane, double-hung, sliding, etc.).
       - Note what is visible through each window (exterior light, trees, sky, neighboring structure).

    4. BUILT-IN FIXTURES (must remain untouched):
       - Ceiling: lights, fans, sprinklers, smoke detectors, recessed lighting, beams.
       - Walls: outlets, switches, vents, thermostats, intercoms, sconces.
       - Floor: vents, floor outlets, transitions between flooring materials.

    5. SURFACES & MATERIALS:
       - Floor material and color (hardwood, tile, carpet, etc.).
       - Wall finish and color for each wall.
       - Ceiling finish.
       - Any trim, baseboards, crown molding, or wainscoting.

    6. CLOSETS & BUILT-INS:
       - Identify any open or visible closets. Note if the interior is visible, its size, and any existing shelves or rods.
       - Note built-in shelving, niches, or cabinetry.

    7. SPATIAL ZONES & TRAFFIC FLOW:
       - Identify clear paths of travel between doors/openings — these corridors MUST remain unobstructed.
       - Note any awkward angles, alcoves, or nooks.
       - Identify large empty wall surfaces and their approximate dimensions.

    8. LIGHTING:
       - Direction and quality of natural light (which windows, time of day estimate).
       - Existing artificial light sources and their warm/cool tone.
       - Shadow patterns on walls and floor.

    IMPORTANT: This analysis defines the IMMUTABLE room shell. Every wall angle, door position, window location, and fixture placement recorded here is LOCKED. Subsequent staging steps must treat this as an inviolable constraint map.
    """
    
    try:
        media_type, image_base64, _, _ = await _fetch_and_encode_image(image_url)
        
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_base64}"}}
            ]}
        ]

        if reference_image_url:
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages[0]["content"].append(
                {"type": "image_url", "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}}
            )

        response = cast(ModelResponse, await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        ))

        content = cast(Choices, response.choices[0]).message.content
        assert content is not None
        return content
    except Exception as e:
        logger.error(f"Error calling LiteLLM for room analysis: {str(e)}")
        raise

# ... (plan_furniture_placement and generate_staged_image_prompt remain unchanged)

# Duplicate generate_image removed (confirmed)

async def plan_furniture_placement(
    analysis: str, 
    room_type: str, 
    style_preset: str, 
    wall_decorations: bool = True, 
    include_tv: bool = False,
    target_image_url: str | None= None,
    reference_image_url: str | None = None,
    reference_plan: str | None = None
) -> str:
    """
    Generates a furniture placement plan based on room analysis.
    Uses vision if images are provided. Uses reference_plan for strict consistency.
    """
    decor_instruction = "Include wall decorations like hanging paintings or framed posters that match the chosen style. IMPORTANT: If there are large, empty wall surfaces prominent in the image, you MUST utilize that space for something (e.g., a large statement art piece, a gallery wall, or a large mirror). You may also include a maximum of one mirror or art piece leaning against a wall. Ensure all decorations are staged as non-permanent (e.g., using adhesive strips for hanging items)." if wall_decorations else "Do NOT include any wall decorations or wall art."
    tv_instruction = "Include a non-wall mounted flat screen TV in the furniture arrangement (e.g., on a TV stand or media console)." if include_tv else ""
    
    consistency_hint = ""
    if reference_image_url:
        consistency_hint = f"""
        PHYSICAL INVENTORY MAPPING (STAGED REFERENCE PROVIDED):
        1. LIST EVERY OBJECT: From the reference image, identify every piece of furniture (Sofa, Rug, Coffee Table, Art, Lamp).
        2. MAP TO TARGET: For EACH item, specify its new 2D/3D location in the Target Image. 
        3. AXIS CHECK: If the target camera is on the opposite side of the room, you MUST invert the positions (Left becomes Right, Near becomes Far).
        4. NO OMISSIONS: You must include EVERY item visible in the reference view into the target view's staging plan.
        """
        if reference_plan:
            consistency_hint += f"\nSTRICT TASK: Replicate the following layout exactly in the new angle: {reference_plan}"

    prompt = f"""
    Based on the following room analysis:
    {analysis}

    Room Type: {room_type}
    Design Style: {style_preset}
    {consistency_hint}

    TASK: Create a furniture placement plan that stages this room while treating the room's architecture as SACRED and IMMUTABLE.

    ===== ABSOLUTE CONSTRAINTS (VIOLATION = FAILURE) =====

    1. DOOR & OPENING PRESERVATION:
       - Every door, doorway, and archway identified in the analysis MUST remain fully visible and completely unobstructed.
       - NO furniture may be placed in front of, partially blocking, or within the swing arc of any door.
       - Traffic corridors between doors/openings must remain clear (minimum 36" / 90cm passage).

    2. WINDOW PRESERVATION:
       - No furniture may block or obscure any window, even partially.
       - Furniture placed beneath windows must not extend above the window sill.

    3. FIXTURE PRESERVATION:
       - All ceiling fixtures (lights, fans, vents) must remain completely visible and unobstructed.
       - All wall fixtures (outlets, switches, vents, thermostats) must remain accessible.
       - No tall furniture may be placed directly under ceiling fans.

    4. WALL & ANGLE PRESERVATION:
       - Furniture must follow the exact wall angles shown in the analysis. If a wall is angled, furniture against it must match that angle.
       - Do NOT suggest any structural modifications (removing walls, adding built-ins, changing floor plan).

    5. PERSPECTIVE PRESERVATION:
       - All furniture must be described from the EXACT camera angle shown in the target image.
       - Items closer to camera appear larger; items further appear smaller — respect this depth.

    ===== FURNITURE PLAN =====

    For each piece of furniture, specify:
    - Item name and style (matching {style_preset})
    - Exact position (which wall, distance from corners/doors, depth in room)
    - Orientation and facing direction
    - Approximate dimensions
    - How it relates to nearby architectural features (e.g., "centered on back wall, 2ft left of the door")

    {decor_instruction}
    {tv_instruction}

    CLOSET STAGING: If an open or visible closet was identified in the analysis, include a staging plan for its interior with organized clothing on matching hangers, neatly folded items on shelves, and stylish storage accessories.

    ===== FINAL VERIFICATION CHECKLIST =====
    Before finishing, mentally verify:
    - [ ] Every door identified in the analysis is still fully visible and unblocked
    - [ ] Every window is unobstructed
    - [ ] All ceiling fixtures remain visible
    - [ ] Traffic paths between all openings are clear
    - [ ] No furniture floats, clips through walls, or defies the room's perspective
    - [ ] The room's geometry (wall angles, corners, ceiling lines) is unchanged
    """
    
    try:
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        
        if target_image_url:
            media_type, image_base64, _, _ = await _fetch_and_encode_image(target_image_url)
            messages[0]["content"].append({
                "type": "image_url", 
                "image_url": {"url": f"data:{media_type};base64,{image_base64}"}
            })
            
        if reference_image_url:
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages[0]["content"].append({
                "type": "image_url", 
                "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}
            })

        response = cast(ModelResponse, await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        ))
        content = cast(Choices, response.choices[0]).message.content
        assert content is not None
        return content
    except Exception as e:
        logger.error(f"Error calling LiteLLM for furniture placement: {str(e)}")
        raise

async def generate_staged_image_prompt(
    original_image_url: str,
    analysis: str,
    placement_plan: str,
    style_preset: str,
    fix_white_balance: bool = False,
    wall_decorations: bool = True,
    include_tv: bool = False,
    reference_image_url: str | None = None,
    reference_plan: str | None = None
) -> str:
    """
    Generates a highly detailed prompt for the image generation model (e.g., Stable Diffusion or DALL-E)
    to stage the room.
    """
    consistency_instruction = ""
    if reference_image_url:
        consistency_instruction = f"""
        STAGING EDIT INSTRUCTIONS (STAGED REFERENCE):
        The Target Image must be virtual staged using the EXACT physical inventory of the Reference Image.
        INVENTORY LIST: List all items from the reference (Sofa, Rug, Coffee Table, Art, etc.).
        3D RE-PROJECTION: Describe their exact new placement in THIS Target Image angle. Ensure the layout is a logical spatial continuation of the reference view.
        """
        if reference_plan:
            consistency_instruction += f"\nTHE SOURCE OF TRUTH FOR FURNITURE IS: {reference_plan}"

    if fix_white_balance:
        wb_instruction = "CORRECT the white balance if the original image is too warm (yellow) or cool (blue), making it look like high-end neutral architectural photography, BUT ensure the original colors of painted surfaces (walls, etc.) are preserved and not altered by the correction."
    else:
        wb_instruction = "STRICTLY PRESERVE the original white balance, color temperature, and lighting tint of the photo exactly as it is. Do NOT attempt to 'fix' or 'neutralize' the colors. If the original photo is warm/yellow or cool/blue, the final rendered image MUST maintain that exact same warmth or coolness."
    
    decor_instruction = "Include furniture and wall decor. You MUST utilize any large, empty wall surfaces for appropriate decorations such as large paintings, framed posters, or mirrors (aligned with the style). At most one object (like a mirror or art piece) may be leaning against a wall. Ensure all staged wall items appear as if mounted via non-destructive means like adhesive strips." if wall_decorations else "Add furniture only. Keep walls completely bare of any art or decorations."
    tv_instruction = "Include a non-wall mounted flat screen TV on a professional stand or media console, appropriately placed for the room's purpose and layout." if include_tv else ""

    prompt = f"""
    You are a professional architectural photographer and virtual staging specialist.
    Create a highly detailed, photorealistic prompt for an image generation model to stage this room.

    {consistency_instruction}

    ===== ROOM PRESERVATION PROTOCOL (NON-NEGOTIABLE) =====

    The following elements from the Target Image are FROZEN — they must appear in the output at the EXACT same pixel positions, angles, and proportions:

    GEOMETRY LOCK:
    - Every wall edge, corner, and angle must remain pixel-identical to the Target Image.
    - The ceiling line, floor plane, and all perspective vanishing points are immutable.
    - The camera position, height, tilt, focal length, and lens distortion must NOT change.

    DOOR & OPENING LOCK:
    - Every door, doorway, and archway must remain at its exact position, size, and state (open/closed).
    - No furniture may appear in front of or overlapping any door or opening.
    - Hallways and passages visible through openings must remain visible.

    WINDOW LOCK:
    - Every window must remain at its exact position and size.
    - The view through each window must be preserved.
    - No furniture may obscure any part of any window.

    FIXTURE LOCK:
    - All ceiling fixtures (lights, fans, sprinklers, vents) must remain visible and unchanged.
    - All wall fixtures (outlets, switches, thermostats, sconces) must remain visible and unchanged.
    - No furniture may be placed over or in front of any fixture.

    LIGHTING LOCK:
    - {wb_instruction}
    - Natural light direction, shadow angles, and shadow intensity must match the Target Image exactly.
    - Furniture shadows must be consistent with the existing light sources in the room.

    ===== STAGING INSTRUCTIONS =====

    1. OVERLAY ONLY: Your task is to composite furniture INTO the existing room photograph. Think of it as physically placing real furniture into the real room — the room itself does not change.
    2. {decor_instruction} {tv_instruction}
    3. CLOSET STAGING: If a closet is visible or open, stage its interior with organized high-end clothing on matching wooden hangers, neatly folded items, and stylish storage accessories.
    4. DEPTH & SCALE: Furniture must respect the room's perspective — items closer to camera are larger, items further away are smaller. Furniture must sit flat on the floor plane with correct shadow contact.
    5. MATERIAL REALISM: Render fabric textures, wood grain, metal reflections, and glass transparency with photorealistic quality matching the room's existing lighting.

    ===== SOURCE DATA =====

    Original Room Analysis:
    {analysis}

    Furniture Plan:
    {placement_plan}

    Style: {style_preset}

    ===== OUTPUT FORMAT =====

    Produce a SINGLE PARAGRAPH prompt for the image generation model. The prompt must:
    - Begin with an explicit instruction: "Edit this room photograph by rendering the following furniture into the existing space WITHOUT altering the room's architecture, camera angle, wall positions, door locations, window placements, or any structural element."
    - Include specific furniture descriptions with materials, colors, and exact positions from the plan.
    - Include photorealistic rendering keywords (8K, architectural photography, natural lighting, ray-traced shadows).
    - Include specific camera/lens terms that match the original photo's perspective.
    - End with: "The room's walls, doors, windows, ceiling, floor, and all fixtures must remain at their exact original pixel positions."

    Original Image URL for reference: {original_image_url}
    """
    
    try:
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        
        if original_image_url:
            media_type, image_base64, _, _ = await _fetch_and_encode_image(original_image_url)
            messages[0]["content"].append({
                "type": "image_url", 
                "image_url": {"url": f"data:{media_type};base64,{image_base64}"}
            })
            
        if reference_image_url:
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages[0]["content"].append({
                "type": "image_url", 
                "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}
            })

        response = cast(ModelResponse, await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        ))
        content = cast(Choices, response.choices[0]).message.content
        assert content is not None
        return content
    except Exception as e:
        logger.error(f"Error calling LiteLLM for generation prompt: {str(e)}")
        raise

async def generate_image_openrouter(prompt: str, original_image_url: str | None = None, fix_white_balance: bool = False, reference_image_url: str | None = None) -> bytes:
    """
    Generates an image using the configured image generation model.
    Returns the raw binary content of the generated image.
    Uses direct HTTP call to OpenRouter to support specific 'modalities' param for Gemini.
    """
    try:
        api_key = settings.OPENROUTER_API_KEY
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://stage-master.app", # Recommended by OpenRouter
            "X-Title": "Stage Master",
        }
        
        # Ensure we use an explicit model name, stripping openrouter/ if present to be safe, 
        # though OpenRouter often accepts both. The user example showed "google/gemini-..."
        model = settings.LITELLM_GENERATION_MODEL
        if model.startswith("openrouter/"):
            model = model.replace("openrouter/", "")

        messages_content = []
        orig_width, orig_height = 0, 0

        # 1. Reference Image (Context ONLY) - FIRST
        if reference_image_url:
            messages_content.append({"type": "text", "text": "\n\nCONSISTENCY REFERENCE (Staged Angle):\nThis image shows the EXISTING furniture and style from another angle of the same room.\nUse this ONLY to identify the inventory of items to be placed (materials, styles, exact objects).\nDo NOT copy the camera angle, wall positions, or room geometry from this reference."})
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages_content.append(
                {"type": "image_url", "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}}
            )

        # 2. Target Image (THE MASTER BACKGROUND) - SECOND & FINAL
        if original_image_url:
             messages_content.append({"type": "text", "text": "THE TARGET IMAGE (IMMUTABLE BACKGROUND):\nThis is the room photograph you are editing. The following are LOCKED and must appear at their EXACT pixel positions in your output:\n- Every wall edge, corner, and angle\n- Every door, doorway, and archway (position, size, open/closed state)\n- Every window (position, size, view through it)\n- All ceiling fixtures (lights, fans, vents)\n- All wall fixtures (outlets, switches, thermostats)\n- The camera angle, height, tilt, and lens perspective\n- The floor plane and ceiling line\nDo NOT move, warp, resize, crop, or alter ANY of these elements."})
             media_type, image_base64, width, height = await _fetch_and_encode_image(original_image_url)
             orig_width, orig_height = width, height
             messages_content.append(
                 {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_base64}"}}
             )

             # Add instructions for this image
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
            "messages": [
                {
                    "role": "user",
                    "content": messages_content
                }
            ],
            "modalities": ["image", "text"]
        }

        logger.info(f"Calling OpenRouter Chat API for image generation with model: {model}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0 # Image generation can be slow
            )
            response.raise_for_status()
            result = response.json()
            
        # Parse response
        # Expected format: choices[0].message.images[0].image_url.url
        # The user said: message["images"] list
        
        if not result.get("choices"):
             raise ValueError(f"No choices in response: {result}")
             
        message = result["choices"][0]["message"]
        
        # OpenRouter/Gemini specific format for images in chat
        image_url = None
        if message.get("images"):
             image_url = message["images"][0]["image_url"]["url"]
        
        # Fallback: sometimes purely text models might return a link in content? 
        # But we expect 'images' key based on user snippet.
        
        if not image_url:
             # Debug log entire message to see what happened
             logger.error(f"Full response message: {message}")
             raise ValueError("No image URL found in response")

        # Handle Base64 Data URL
        if image_url.startswith("data:"):
            # Format: data:image/png;base64,.....
            header, encoded = image_url.split(",", 1)
            generated_bytes = base64.b64decode(encoded)
        else:
            # It's a regular URL, download it
            async with httpx.AsyncClient() as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                generated_bytes = img_resp.content

        # Resize output to match the original image dimensions
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
        logger.error(f"Error generating image: {str(e)}")
        raise

async def generate_image_vertex(prompt: str, original_image_url: str | None = None, fix_white_balance: bool = False, reference_image_url: str | None = None) -> bytes:
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

        # 1. Original room image (THE MASTER BACKGROUND) - primary reference
        if original_image_url:
            _, image_base64, orig_width, orig_height = await _fetch_and_encode_image(original_image_url)
            reference_images.append(RawReferenceImage(
                reference_id=ref_id,
                image=VertexImage(image_bytes=base64.b64decode(image_base64)),
            ))
            ref_id += 1

        # 2. Consistency reference (another angle of same room, if provided)
        if reference_image_url:
            _, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            reference_images.append(RawReferenceImage(
                reference_id=ref_id,
                image=VertexImage(image_bytes=base64.b64decode(ref_image_base64)),
            ))

        # Build full prompt
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
                key=lambda r: abs((int(r.split(":")[0]) / int(r.split(":")[1])) - target_ratio)
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
            )
        )

        generated_bytes = images[0]._image_bytes

        # Resize output to match the original image dimensions
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
        logger.error(f"Error generating image: {str(e)}")
        raise

async def generate_image(prompt: str, original_image_url: str | None = None, fix_white_balance: bool = False, reference_image_url: str | None = None) -> bytes:
    return await generate_image_vertex(prompt, original_image_url, fix_white_balance, reference_image_url)