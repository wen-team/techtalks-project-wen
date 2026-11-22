"""Development address store: one JSON file plus uploaded files on disk.

Good enough to build and demo the full flow (create, share, drive, deliver)
before the real models exist. Not for production: no migrations, a single
process-wide lock, and data lives under ``media/wen_dev/`` (git-ignored).
"""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Iterable

from django.utils import timezone

from .base import AddressRepository
from .types import AddressCard, Event, Landmark, MediaAsset, OwnerStats, Pin, ShareLink

_LOCK = threading.RLock()

EDITABLE_FIELDS = (
    "title", "description", "language", "building_description", "building_color",
    "floor", "entrance_description", "directions", "match_quality",
)


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _asset_to_dict(a: MediaAsset) -> dict:
    return {"id": a.id, "kind": a.kind, "filename": a.filename, "content_type": a.content_type, "size": a.size}


def _to_dict(card: AddressCard) -> dict:
    return {
        "id": card.id,
        "owner_id": card.owner_id,
        "title": card.title,
        "description": card.description,
        "language": card.language,
        "landmark": card.landmark.to_dict() if card.landmark else None,
        "pin": {"lat": card.pin.lat, "lng": card.pin.lng, "source": card.pin.source},
        "match_quality": card.match_quality,
        "building_description": card.building_description,
        "building_color": card.building_color,
        "floor": card.floor,
        "entrance_description": card.entrance_description,
        "directions": card.directions,
        "photos": [_asset_to_dict(p) for p in card.photos],
        "voice_note": _asset_to_dict(card.voice_note) if card.voice_note else None,
        "created_at": _iso(card.created_at),
        "updated_at": _iso(card.updated_at),
        "last_used_at": _iso(card.last_used_at),
        "link": None
        if not card.link
        else {
            "token": card.link.token,
            "created_at": _iso(card.link.created_at),
            "expires_at": _iso(card.link.expires_at),
            "revoked_at": _iso(card.link.revoked_at),
            "delivered_at": _iso(card.link.delivered_at),
        },
        "events": [{"type": e.type, "at": _iso(e.at)} for e in card.events],
    }


def _from_dict(d: dict) -> AddressCard:
    link = d.get("link")
    return AddressCard(
        id=d["id"],
        owner_id=d["owner_id"],
        title=d["title"],
        description=d["description"],
        language=d["language"],
        landmark=Landmark.from_dict(d.get("landmark")),
        pin=Pin(**d["pin"]),
        match_quality=d.get("match_quality"),
        building_description=d.get("building_description", ""),
        building_color=d.get("building_color", ""),
        floor=d.get("floor", ""),
        entrance_description=d.get("entrance_description", ""),
        directions=d.get("directions", ""),
        photos=[MediaAsset(**p) for p in d.get("photos", [])],
        voice_note=MediaAsset(**d["voice_note"]) if d.get("voice_note") else None,
        created_at=_dt(d.get("created_at")),
        updated_at=_dt(d.get("updated_at")),
        last_used_at=_dt(d.get("last_used_at")),
        link=None
        if not link
        else ShareLink(
            token=link["token"],
            created_at=_dt(link["created_at"]),
            expires_at=_dt(link["expires_at"]),
            revoked_at=_dt(link.get("revoked_at")),
            delivered_at=_dt(link.get("delivered_at")),
        ),
        events=[Event(type=e["type"], at=_dt(e["at"])) for e in d.get("events", [])],
    )


class JsonFileAddressRepository(AddressRepository):
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.db_path = self.root / "addresses.json"

    # ----------------------------------------------------------------- storage
    def _load(self) -> dict[str, dict]:
        if not self.db_path.exists():
            return {}
        with self.db_path.open(encoding="utf-8") as fh:
            return json.load(fh).get("addresses", {})

    def _save(self, addresses: dict[str, dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.db_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump({"version": 1, "addresses": addresses}, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, self.db_path)

    def _media_dir(self, address_id: str) -> Path:
        return self.root / "media" / address_id

    def _store_file(self, address_id: str, upload, kind: str) -> MediaAsset:
        asset_id = secrets.token_hex(8)
        ext = mimetypes.guess_extension(upload.content_type or "") or Path(upload.name).suffix or ""
        if ext == ".weba":
            ext = ".webm"
        folder = self._media_dir(address_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{asset_id}{ext}"
        with path.open("wb") as fh:
            for chunk in upload.chunks():
                fh.write(chunk)
        return MediaAsset(asset_id, kind, path.name, upload.content_type or "application/octet-stream", upload.size)

    def _remove_file(self, address_id: str, asset: MediaAsset) -> None:
        path = self._media_dir(address_id) / asset.filename
        if path.exists():
            path.unlink()

    def _mutate(self, address_id: str, fn, owner_id: int | None = None) -> AddressCard | None:
        with _LOCK:
            addresses = self._load()
            raw = addresses.get(address_id)
            if raw is None or (owner_id is not None and raw["owner_id"] != owner_id):
                return None
            card = _from_dict(raw)
            result = fn(card)
            if result is False:
                return None
            addresses[address_id] = _to_dict(card)
            self._save(addresses)
            return card

    def _find_token(self, token: str) -> AddressCard | None:
        if not token:
            return None
        for raw in self._load().values():
            link = raw.get("link")
            if link and secrets.compare_digest(link["token"], token):
                return _from_dict(raw)
        return None

    # -------------------------------------------------------------- owner side
    def list_for_owner(self, owner_id: int) -> list[AddressCard]:
        with _LOCK:
            cards = [_from_dict(r) for r in self._load().values() if r["owner_id"] == owner_id]
        return sorted(cards, key=lambda c: c.last_used_at or c.created_at, reverse=True)

    def get_for_owner(self, owner_id: int, address_id: str) -> AddressCard | None:
        with _LOCK:
            raw = self._load().get(address_id)
        if raw is None or raw["owner_id"] != owner_id:
            return None
        return _from_dict(raw)

    def create(self, owner_id: int, data: dict, photos: Iterable, voice_note=None) -> AddressCard:
        now = timezone.now()
        address_id = secrets.token_hex(8)
        card = AddressCard(
            id=address_id,
            owner_id=owner_id,
            title=data["title"],
            description=data["description"],
            language=data.get("language") or "en",
            landmark=data.get("landmark"),
            pin=data["pin"],
            match_quality=data.get("match_quality"),
            building_description=data.get("building_description", ""),
            building_color=data.get("building_color", ""),
            floor=data.get("floor", ""),
            entrance_description=data.get("entrance_description", ""),
            directions=data.get("directions", ""),
            created_at=now,
            updated_at=now,
            last_used_at=now,
            events=[Event("created", now)],
        )
        card.photos = [self._store_file(address_id, f, "photo") for f in photos]
        if voice_note:
            card.voice_note = self._store_file(address_id, voice_note, "voice")
        with _LOCK:
            addresses = self._load()
            addresses[address_id] = _to_dict(card)
            self._save(addresses)
        return card

    def update(self, owner_id, address_id, data, new_photos=(), remove_photo_ids=(), voice_note=None,
               remove_voice_note=False):
        remove_ids = set(remove_photo_ids)

        def apply(card: AddressCard):
            for name in EDITABLE_FIELDS:
                if name in data:
                    setattr(card, name, data[name])
            if "pin" in data:
                card.pin = data["pin"]
            if "landmark" in data:
                card.landmark = data["landmark"]
            for asset in [p for p in card.photos if p.id in remove_ids]:
                self._remove_file(card.id, asset)
            card.photos = [p for p in card.photos if p.id not in remove_ids]
            card.photos += [self._store_file(card.id, f, "photo") for f in new_photos]
            if (remove_voice_note or voice_note) and card.voice_note:
                self._remove_file(card.id, card.voice_note)
                card.voice_note = None
            if voice_note:
                card.voice_note = self._store_file(card.id, voice_note, "voice")
            card.updated_at = timezone.now()

        return self._mutate(address_id, apply, owner_id)

    def delete(self, owner_id: int, address_id: str) -> bool:
        with _LOCK:
            addresses = self._load()
            raw = addresses.get(address_id)
            if raw is None or raw["owner_id"] != owner_id:
                return False
            del addresses[address_id]
            self._save(addresses)
        shutil.rmtree(self._media_dir(address_id), ignore_errors=True)
        return True

    def touch(self, owner_id: int, address_id: str) -> None:
        def apply(card):
            card.last_used_at = timezone.now()

        self._mutate(address_id, apply, owner_id)

    def issue_link(self, owner_id: int, address_id: str, ttl_hours: int) -> AddressCard | None:
        def apply(card):
            now = timezone.now()
            card.link = ShareLink(
                token=secrets.token_urlsafe(18),
                created_at=now,
                expires_at=now + timedelta(hours=ttl_hours),
            )
            card.last_used_at = now
            card.events.append(Event("link_created", now))

        return self._mutate(address_id, apply, owner_id)

    def revoke_link(self, owner_id: int, address_id: str) -> AddressCard | None:
        def apply(card):
            if not card.link or card.link.state(timezone.now()) != "active":
                return False
            now = timezone.now()
            card.link.revoked_at = now
            card.events.append(Event("link_revoked", now))

        return self._mutate(address_id, apply, owner_id)

    def stats_for_owner(self, owner_id: int) -> OwnerStats:
        now = timezone.now()
        cards = self.list_for_owner(owner_id)
        events = [e.type for c in cards for e in c.events]
        return OwnerStats(
            addresses=len(cards),
            active_links=sum(1 for c in cards if c.link_state(now) == "active"),
            link_opens=events.count("link_opened"),
            deliveries=events.count("delivered"),
            landmark_confirmations=events.count("landmark_confirmed"),
            landmark_rejections=events.count("landmark_rejected"),
        )

    # -------------------------------------------------------------- link side
    def get_by_token(self, token: str) -> AddressCard | None:
        with _LOCK:
            return self._find_token(token)

    def record_link_event(self, token: str, event_type: str) -> AddressCard | None:
        with _LOCK:
            card = self._find_token(token)
            if not card or card.link_state(timezone.now()) != "active":
                return None

            def apply(c):
                c.events.append(Event(event_type, timezone.now()))
                if event_type == "link_opened":
                    c.last_used_at = timezone.now()

            return self._mutate(card.id, apply)

    def mark_delivered(self, token: str) -> AddressCard | None:
        with _LOCK:
            card = self._find_token(token)
            if not card or card.link_state(timezone.now()) != "active":
                return None

            def apply(c):
                now = timezone.now()
                c.link.delivered_at = now
                c.events.append(Event("delivered", now))

            return self._mutate(card.id, apply)

    # ------------------------------------------------------------------ media
    def open_media(self, address: AddressCard, asset_id: str) -> tuple[BinaryIO, str] | None:
        assets = list(address.photos) + ([address.voice_note] if address.voice_note else [])
        asset = next((a for a in assets if a.id == asset_id), None)
        if not asset:
            return None
        path = self._media_dir(address.id) / asset.filename
        if not path.is_file():
            return None
        return path.open("rb"), asset.content_type
