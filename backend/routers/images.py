"""Image generation — Althea draws diagrams, physics visuals, and
explanatory pictures on demand using Gemini Nano Banana via emergentintegrations.
"""
import base64
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core import EMERGENT_LLM_KEY, db, is_budget_exceeded
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import Memory

router = APIRouter()

GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"


class ImageRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    purpose: Optional[str] = "explanation"  # "explanation" | "diagram" | "art"


class ImageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    prompt: str
    purpose: str
    image_data: str  # base64-encoded PNG/JPEG (no data: prefix; we add it on read)
    mime_type: str = "image/png"
    text_caption: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None
    bytes_size: int = 0


@router.post("/images/generate")
async def generate_image(req: ImageRequest):
    """Generate an image via Gemini Nano Banana. Returns the base64 data URL
    so the frontend can render it inline immediately."""
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="empty_prompt")
    if not EMERGENT_LLM_KEY:
        raise HTTPException(
            status_code=503,
            detail="image_generation_offline_no_llm_key",
        )

    session_id = req.session_id or str(uuid4())
    purpose = req.purpose or "explanation"

    # System prompt nudges Nano Banana toward a clean educational rendering
    # that complements the cyberpunk aesthetic of Althea's terminal.
    system_message = (
        "You produce educational, high-contrast illustrations and diagrams "
        "for an advanced AI system named ALTHEA. Style: cinematic, futuristic, "
        "neon-on-black where appropriate, clarity over flair. Render exactly "
        "one image per request that best explains the user prompt."
    )

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message,
        ).with_model("gemini", GEMINI_IMAGE_MODEL).with_params(
            modalities=["image", "text"],
        )
        msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
    except Exception as exc:
        if is_budget_exceeded(exc):
            raise HTTPException(
                status_code=402,
                detail=(
                    "image_budget_exceeded: top up the universal key "
                    "(Profile → Universal Key → Add Balance)."
                ),
            )
        logging.exception("image generation failed")
        raise HTTPException(status_code=502, detail=f"gemini_failure: {str(exc)[:160]}")

    if not images:
        raise HTTPException(
            status_code=502,
            detail="no_image_returned",
        )

    first = images[0]
    b64 = first.get("data") or ""
    mime = first.get("mime_type", "image/png")
    if not b64:
        raise HTTPException(status_code=502, detail="empty_image_data")

    # Store the record (without the giant base64 in the response payload would
    # be cleaner, but the frontend needs it immediately to render — store it
    # too so the operator can see it again later via /api/images/list).
    record = ImageRecord(
        prompt=prompt,
        purpose=purpose,
        image_data=b64,
        mime_type=mime,
        text_caption=(text or "")[:600],
        session_id=session_id,
        bytes_size=len(base64.b64decode(b64, validate=False)),
    )
    doc = record.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_images.insert_one(doc)

    # Log a memory event so the lattice knows Althea visualized something.
    mem = Memory(
        content=f"[IMAGINED] {prompt[:200]}",
        source="image",
        tags=["image", purpose],
        session_id=session_id,
    )
    mdoc = mem.model_dump()
    mdoc["timestamp"] = mdoc["timestamp"].isoformat()
    await db.althea_memories.insert_one(mdoc)

    return {
        "id": record.id,
        "prompt": prompt,
        "data_url": f"data:{mime};base64,{b64}",
        "mime_type": mime,
        "text_caption": record.text_caption,
        "bytes_size": record.bytes_size,
        "timestamp": doc["timestamp"],
    }


@router.get("/images/list")
async def list_images(limit: int = 20, include_data: bool = False):
    projection = {"_id": 0}
    if not include_data:
        projection["image_data"] = 0
    docs = await db.althea_images.find({}, projection).sort(
        "timestamp", -1
    ).to_list(max(1, min(limit, 200)))
    return {"count": len(docs), "images": docs}


@router.get("/images/{image_id}")
async def get_image(image_id: str):
    doc = await db.althea_images.find_one(
        {"id": image_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    return {
        **{k: v for k, v in doc.items() if k != "image_data"},
        "data_url": f"data:{doc.get('mime_type','image/png')};base64,{doc['image_data']}",
    }
