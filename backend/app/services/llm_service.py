import litellm
import logging
import asyncio
import base64
import httpx
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

async def analyze_room(image_url: str, reference_image_url: str = None, reference_analysis: str = None) -> str:
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
    
    TASK: Provide a detailed architectural analysis of this room.
    1. Identify all surfaces (floor, walls, ceiling) and their materials.
    2. Identify all architectural features (windows, doors, paths of travel).
    3. Identify all BUILT-IN FIXTURES (ceiling lights, fans, wall outlets, vents, switches).
    4. CRITICAL: Identify any OPEN or VISIBLE CLOSETS. Note if the interior is visible, its size, and any existing shelves or rods.
    5. Estimate room dimensions and lighting direction.
    6. CRITICAL: Identify any large, empty wall surfaces that are prominent in the view. Note their size and position (e.g., "Large blank wall on the left, behind the intended sofa area").
    
    IMPORTANT: Focus on the "bones" of the room. This analysis will be used to ensure that subsequent staging steps do not alter the room's layout or fixtures.
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

        response = await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        )
        return response.choices[0].message.content
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
    target_image_url: str = None,
    reference_image_url: str = None,
    reference_plan: str = None
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
    
    Provide a detailed furniture placement plan for the TARGET IMAGE. 
    If a reference image is provided, your plan MUST be a logical continuation of the staging seen there.
    List specific furniture items, their positions, and how they should look.
    {decor_instruction}
    {tv_instruction}
    
    CLOSET STAGING: If an open or visible closet was identified in the analysis, you MUST include a staging plan for its interior. This should include organized clothing on matching hangers, neatly folded items on shelves, and stylish storage bins or baskets to make it look functional and attractive.
    
    IMPORTANT ARCHITECTURAL LOCKDOWN: The furniture arrangement must respect the existing room layout, doors, windows, and traffic flow. 
    Do not suggest removing, altering, or obstructing any architectural features or existing fixtures (light fixtures, fans, vents, windows).
    The goal is to furnish the room AS IS, matching the reference view perfectly without changing a single structural line.
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

        response = await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        )
        return response.choices[0].message.content
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
    reference_image_url: str = None,
    reference_plan: str = None
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
    You are a professional architectural photographer and interior designer.
    Create a highly detailed, photorealistic prompt for generating a virtually staged version of this room.
    
    {consistency_instruction}
    
    CRITICAL PERSPECTIVE LOCKDOWN:
    1. The goal is to VIRTUAL STAGE the EXISTING room pixels.
    2. You MUST preserve the 100% EXACT structure and PIXEL POSITION of the room's architecture (walls, ceiling, floor lines, windows, doors) from the Target Image.
    3. You MUST preserve the EXACT camera angle and lens perspective of the Target Image. Do NOT move the camera or warp the background to match the reference image.
    4. You MUST preserve the current natural lighting direction, shadows, and reflections exactly as they appear in the Target Image.
    5. {wb_instruction}
    6. {decor_instruction} {tv_instruction} DO NOT remove or alter architectural elements.
    7. CLOSET STAGING: If a closet is visible or open, render it as fully staged with organized, high-end clothing, matching wooden hangers, and neat storage accessories.
    8. CRITICAL: Do NOT remove, modify, or obscure any existing room objects, fixtures, or layout elements such as light fixtures, ceiling fans, wall switches, vents, or built-ins. They must remain exactly as they are.
    9. THE BACKGROUND IS SACRED: Your task is to overlay furniture into the room EXACTLY as it is, as if you are physically placing items into the existing space. The architectural background of the Target Image must remain pixel-identical.
    
    Original Room Analysis:
    {analysis}
    
    Furniture Plan:
    {placement_plan}
    
    Style: {style_preset}
    
    Produce a single paragraph prompt that includes lighting details, texture descriptions, specific camera settings, and photorealistic keywords.
    The prompt should explicitly consist of instructions to the generation model to "render the following furniture into the provided room image without changing the room's geometry or perspective".
    
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

        response = await litellm.acompletion(
            model=settings.LITELLM_ANALYSIS_MODEL,
            messages=messages,
            api_key=settings.OPENROUTER_API_KEY
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling LiteLLM for generation prompt: {str(e)}")
        raise

async def generate_image(prompt: str, original_image_url: str = None, fix_white_balance: bool = False, reference_image_url: str = None) -> bytes:
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
        
        # 1. Reference Image (Context ONLY) - FIRST
        if reference_image_url:
            messages_content.append({"type": "text", "text": f"\n\nCONSISTENCY REFERENCE (Staged Angle):\nThis image shows the EXISTING furniture and style from another angle of the same room. \nUse this ONLY to identify the inventory of items to be placed (materials, styles, exact objects)."})
            ref_media_type, ref_image_base64, _, _ = await _fetch_and_encode_image(reference_image_url)
            messages_content.append(
                {"type": "image_url", "image_url": {"url": f"data:{ref_media_type};base64,{ref_image_base64}"}}
            )

        # 2. Target Image (THE MASTER BACKGROUND) - SECOND & FINAL
        if original_image_url:
             messages_content.append({"type": "text", "text": "THE TARGET IMAGE (Background to be Edited):\nThis is the photo you are virtually staging. Treat this as the absolute, immutable background. Do NOT change its camera angle, perspective, or a single pixel of the architecture (walls, windows, fixtures)."})
             media_type, image_base64, width, height = await _fetch_and_encode_image(original_image_url)
             messages_content.append(
                 {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_base64}"}}
             )
             
             # Add instructions for this image
             extra_text = f"\n\nEDIT TASK: OVERLAY STAGING\n{prompt}"
             
             if width > 0 and height > 0:
                 extra_text += f"\n\nIMPORTANT: The output image MUST maintain the exact {width}x{height} resolution."
             
             if not fix_white_balance:
                 extra_text += "\n\nCRITICAL: PRESERVE the original white balance of this Target Image."
             
             extra_text += "\n\nFINAL CHECK: The generated image must be this Target Image with the furniture added. Any change to the camera height, tilt, or room's geometry is a CRITICAL FAILURE."
             
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
            return base64.b64decode(encoded)
        else:
            # It's a regular URL, download it
            async with httpx.AsyncClient() as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                return img_resp.content

    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise
