"""One-time migration: move the legacy single-operator Althea (un-prefixed
collections + grown code on disk) into the founder's private tenant."""
import logging
import shutil
from datetime import datetime, timezone

from core import GROWN_ROOT, shared_db, tenant_collection_name

LEGACY_PREFIXES = ("althea_", "symbolic_", "research_", "neural_sessions", "command")
MARKER = "althea_meta"


async def migrate_legacy_to_founder(founder_id: str) -> dict:
    meta = await shared_db[MARKER].find_one({"key": "legacy_migration"}, {"_id": 0})
    if meta:
        return {"migrated": False, "reason": "already_done", "founder": meta.get("founder_id")}
    names = await shared_db.list_collection_names()
    legacy = [n for n in names if "__" not in n and n != MARKER and n.startswith(LEGACY_PREFIXES)]
    moved = []
    for name in legacy:
        target = tenant_collection_name(name, founder_id)
        try:
            await shared_db[name].rename(target, dropTarget=True)
            moved.append(name)
        except Exception:
            logging.exception("legacy rename failed for %s", name)
    files = 0
    try:
        dest = GROWN_ROOT / founder_id
        dest.mkdir(parents=True, exist_ok=True)
        for p in GROWN_ROOT.iterdir():
            if p.is_file():
                shutil.move(str(p), str(dest / p.name))
                files += 1
    except Exception:
        logging.exception("legacy grown-code move failed")
    await shared_db[MARKER].insert_one({
        "key": "legacy_migration", "founder_id": founder_id, "collections": moved,
        "files": files, "at": datetime.now(timezone.utc).isoformat()})
    logging.info("legacy Althea migrated to founder %s: %d collections, %d files", founder_id, len(moved), files)
    return {"migrated": True, "collections": moved, "files": files, "founder": founder_id}
