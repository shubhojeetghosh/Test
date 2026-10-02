"""Move existing data-URL quiz media into private Supabase Storage.

Run from the backend directory. A dry run is the default; pass --apply only
after configuring SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and the bucket.
"""

from __future__ import annotations

import argparse
import base64
import re
from urllib.parse import unquote_to_bytes

from sqlalchemy import select

from app.admin_portal.models.option import Option
from app.admin_portal.models.question import Question
from app.core.database import SessionLocal
from app.services.media_storage import MAX_MEDIA_BYTES, upload_media


DATA_URL = re.compile(r"^data:([^;,]+)((?:;[^,]*)*),(.*)$", re.DOTALL)
MEDIA_FIELDS = ("image_url", "audio_url")


def decode_data_url(value: str) -> tuple[bytes, str]:
    match = DATA_URL.match(value)
    if not match:
        raise ValueError("Malformed data URL")
    content_type, metadata, payload = match.groups()
    if ";base64" in metadata.lower():
        content = base64.b64decode(payload, validate=True)
    else:
        content = unquote_to_bytes(payload)
    if not content or len(content) > MAX_MEDIA_BYTES:
        raise ValueError("Embedded media must be between 1 byte and 10 MB")
    if not (content_type.startswith("image/") or content_type.startswith("audio/")):
        raise ValueError(f"Unsupported media type: {content_type}")
    return content, content_type


def migrate_model(db, model, apply: bool) -> tuple[int, int]:
    migrated = 0
    failed = 0
    ids = db.scalars(
        select(model.id).where(
            (model.image_url.like("data:%")) | (model.audio_url.like("data:%"))
        )
    ).all()
    print(f"{model.__tablename__}: {len(ids)} rows contain embedded media")
    if not apply:
        return 0, 0

    for row_id in ids:
        record = db.get(model, row_id)
        if record is None:
            continue
        changed = False
        try:
            for field in MEDIA_FIELDS:
                value = getattr(record, field)
                if not value or not value.startswith("data:"):
                    continue
                content, content_type = decode_data_url(value)
                storage_path = upload_media(content, content_type, f"{row_id}.{field}")
                setattr(record, field, storage_path)
                changed = True
            if changed:
                db.commit()
                migrated += 1
        except Exception as exc:
            db.rollback()
            failed += 1
            print(f"Could not migrate {model.__tablename__} row {row_id}: {exc}")
    return migrated, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload media and replace database data URLs with Storage paths.",
    )
    args = parser.parse_args()
    db = SessionLocal()
    try:
        totals = [migrate_model(db, model, args.apply) for model in (Question, Option)]
        migrated = sum(result[0] for result in totals)
        failed = sum(result[1] for result in totals)
        if args.apply:
            print(f"Migrated rows: {migrated}; failed rows: {failed}")
            return 1 if failed else 0
        print("Dry run only. Add --apply to migrate after Supabase setup.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
