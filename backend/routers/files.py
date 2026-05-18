"""File attachments — operator uploads files to the terminal, Althea reads
text contents, files can be re-downloaded later.

Limits: 2MB per file, text preview extracted for human-readable types.
"""
import base64
import logging
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from core import db
from models import FileItem, Memory
from routers.notifications import emit_notification

router = APIRouter()

MAX_BYTES = 2 * 1024 * 1024  # 2MB
TEXT_MIMES_PREFIX = ("text/", "application/json", "application/xml")
TEXT_EXT = {
    ".txt", ".md", ".json", ".csv", ".tsv", ".log", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".html", ".css", ".yaml", ".yml", ".xml", ".env",
    ".sh", ".rs", ".go", ".java", ".c", ".cpp", ".h",
}


def _is_text(filename: str, mime: str, sample: bytes) -> bool:
    if mime and (mime.startswith("text/") or mime in ("application/json", "application/xml", "application/javascript")):
        return True
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext in TEXT_EXT:
        return True
    # heuristic: low fraction of non-printable bytes
    if not sample:
        return False
    printable = sum(1 for b in sample if b == 9 or b == 10 or b == 13 or 32 <= b < 127)
    return (printable / max(len(sample), 1)) > 0.85


@router.post("/files/upload", response_model=FileItem)
async def upload_file(file: UploadFile = File(...)):
    buf = BytesIO()
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_BYTES:
            raise HTTPException(status_code=413, detail="file_too_large_2MB_max")
        buf.write(chunk)
    raw = buf.getvalue()
    sample = raw[:4096]
    is_text = _is_text(file.filename or "blob", file.content_type or "", sample)
    text_preview = None
    if is_text:
        try:
            text_preview = sample.decode("utf-8", errors="replace")[:4000]
        except Exception:
            text_preview = None

    item = FileItem(
        filename=file.filename or f"blob-{datetime.now(timezone.utc).timestamp()}",
        mime=file.content_type or "application/octet-stream",
        size_bytes=total,
        is_text=is_text,
        text_preview=text_preview,
        data_base64=base64.b64encode(raw).decode("ascii"),
        tags=["upload"],
    )
    doc = item.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_files.insert_one(doc)

    # Ingest into memory so Althea is "aware" of the file
    mem = Memory(
        content=(
            f"[FILE-INGEST id:{item.id[:8]} {item.filename}] "
            f"size={item.size_bytes}B mime={item.mime} text={is_text}. "
            + (f"preview: {text_preview[:280]}" if text_preview else "(binary)")
        ),
        source="file",
        tags=["file", "ingest", item.filename.rsplit(".", 1)[-1].lower()[:16]],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    await emit_notification(
        title=f"file ingested · {item.filename}",
        body=(
            f"{item.size_bytes} bytes · {item.mime} · "
            + ("text — preview captured into memory." if is_text else "binary — checksum stored.")
        ),
        category="file",
        priority="info",
        payload={"id": item.id, "filename": item.filename, "size": item.size_bytes},
    )

    # Return without data_base64 for response payload size
    out = item.model_dump()
    out["data_base64"] = None
    return out


@router.get("/files", response_model=List[FileItem])
async def list_files(limit: int = 200):
    docs = await db.althea_files.find(
        {}, {"_id": 0, "data_base64": 0}
    ).sort("timestamp", -1).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.get("/files/{file_id}")
async def get_file_meta(file_id: str, include_text: bool = True):
    doc = await db.althea_files.find_one(
        {"id": file_id}, {"_id": 0, "data_base64": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    if not include_text:
        doc.pop("text_preview", None)
    return doc


@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    doc = await db.althea_files.find_one({"id": file_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    raw = base64.b64decode(doc.get("data_base64") or "")
    filename = doc.get("filename", "althea-file")
    safe = re.sub(r'[^A-Za-z0-9._-]', "_", filename) or "file"
    return Response(
        content=raw,
        media_type=doc.get("mime", "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    res = await db.althea_files.delete_one({"id": file_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": file_id}
