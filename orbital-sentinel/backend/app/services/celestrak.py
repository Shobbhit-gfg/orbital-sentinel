import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
from sgp4.api import Satrec
from sgp4 import omm


class IngestedRecord:
    def __init__(self, fields: dict[str, Any], sat: Satrec, source_url: str, retrieved_at: datetime):
        self.fields = fields
        self.sat = sat
        self.source_url = source_url
        self.retrieved_at = retrieved_at

    @property
    def norad_id(self) -> str:
        value = self.fields.get("NORAD_CAT_ID") or self.fields.get("NORAD_CAT_ID_STR") or self.fields.get("CATNR")
        return str(value)

    @property
    def name(self) -> str:
        return str(self.fields.get("OBJECT_NAME") or self.fields.get("OBJECT_ID") or f"NORAD {self.norad_id}").strip()

    @property
    def epoch(self) -> datetime | None:
        value = self.fields.get("EPOCH")
        if not value:
            return None
        text = str(value).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _normalize_json_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        # CelesTrak may return a wrapper; accept common record-list keys.
        for key in ("data", "records", "OMM", "omm"):
            if isinstance(payload.get(key), list):
                return [dict(x) for x in payload[key] if isinstance(x, dict)]
        return [payload]
    if isinstance(payload, list):
        return [dict(x) for x in payload if isinstance(x, dict)]
    raise ValueError("Unexpected CelesTrak JSON shape")


def _parse_tle(text: str, source_url: str, retrieved_at: datetime) -> list[IngestedRecord]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    records: list[IngestedRecord] = []
    i = 0
    while i < len(lines):
        if i + 1 >= len(lines):
            break
        if lines[i].startswith("1 ") and lines[i + 1].startswith("2 "):
            name = f"NORAD {lines[i][2:7].strip()}"
            line1, line2 = lines[i], lines[i + 1]
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            name = lines[i]
            line1, line2 = lines[i + 1], lines[i + 2]
            i += 3
        else:
            i += 1
            continue
        try:
            sat = Satrec.twoline2rv(line1, line2)
            fields = {"NORAD_CAT_ID": line1[2:7].strip(), "OBJECT_NAME": name, "TLE_LINE1": line1, "TLE_LINE2": line2}
            records.append(IngestedRecord(fields, sat, source_url, retrieved_at))
        except Exception:
            continue
    return records


async def fetch_celestrak(url: str, timeout_seconds: int) -> tuple[list[IngestedRecord], str, datetime]:
    retrieved_at = datetime.now(timezone.utc)
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "ORBITAL-SENTINEL/0.1"})
        response.raise_for_status()
        raw = response.content
        checksum = hashlib.sha256(raw).hexdigest()
        content_type = response.headers.get("content-type", "").lower()
        is_tle = "format=tle" in url.lower() or "text/plain" in content_type
        if is_tle:
            return _parse_tle(raw.decode("utf-8", errors="replace"), url, retrieved_at), checksum, retrieved_at
        payload = response.json()

    records: list[IngestedRecord] = []
    for fields in _normalize_json_records(payload):
        try:
            # Official sgp4 OMM path: deterministic conversion from published mean elements.
            sat = Satrec()
            omm.initialize(sat, fields)
            record = IngestedRecord(fields, sat, url, retrieved_at)
            if record.norad_id:
                records.append(record)
        except Exception:
            continue

    return records, checksum, retrieved_at
