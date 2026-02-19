import litellm
import logging
from typing import cast
from litellm import ModelResponse
from litellm.types.utils import Choices
from app.core.config import settings
from app.services.image_service import _fetch_and_encode_image

logger = logging.getLogger(__name__)

# Configure litellm
litellm.telemetry = False

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

