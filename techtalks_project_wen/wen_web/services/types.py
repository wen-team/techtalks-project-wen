"""Data shapes shared by the UI and every service implementation.

These are the contract between the frontend and the backend lanes. A real
implementation (ORM models, wen_api endpoints, Photon resolver...) only has to
return these objects for every page to keep working.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal

MatchQuality = Literal["strong", "partial", "weak"]
PinSource = Literal["landmark", "adjusted", "manual"]
LinkState = Literal["none", "active", "expired", "delivered", "revoked"]
Language = Literal["ar", "arabizi", "en", "mixed"]


@dataclass(frozen=True)
class Landmark:
    id: str
    name: str
    name_ar: str
    category: str  # church, mosque, university, square, street, shop, landmark...
    area: str
    area_ar: str
    lat: float
    lng: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> Landmark | None:
        return cls(**data) if data else None


@dataclass(frozen=True)
class Candidate:
    landmark: Landmark
    score: float  # 0..1, from the resolver
    quality: MatchQuality
    matched_text: str  # the part of the user's text that produced the match

    def to_dict(self) -> dict:
        return {
            "landmark": self.landmark.to_dict(),
            "score": round(self.score, 3),
            "quality": self.quality,
            "matched_text": self.matched_text,
        }


@dataclass(frozen=True)
class Resolution:
    text: str
    language: Language
    candidates: list[Candidate]
    hints: dict  # e.g. {"floor": "3", "building_color": "green"}
    simulated: bool  # True when the resolver is the development mock

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "candidates": [c.to_dict() for c in self.candidates],
            "hints": self.hints,
            "simulated": self.simulated,
        }


@dataclass
class MediaAsset:
    id: str
    kind: Literal["photo", "voice"]
    filename: str
    content_type: str
    size: int


@dataclass
class ShareLink:
    token: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    delivered_at: datetime | None = None

    def state(self, now: datetime) -> LinkState:
        if self.delivered_at:
            return "delivered"
        if self.revoked_at:
            return "revoked"
        if now >= self.expires_at:
            return "expired"
        return "active"


@dataclass
class Event:
    type: str  # created, link_created, link_opened, landmark_confirmed, landmark_rejected, delivered, link_revoked
    at: datetime


@dataclass
class Pin:
    lat: float
    lng: float
    source: PinSource


@dataclass
class AddressCard:
    id: str
    owner_id: int
    title: str
    description: str
    language: Language
    landmark: Landmark | None
    pin: Pin
    match_quality: MatchQuality | None
    building_description: str = ""
    building_color: str = ""
    floor: str = ""
    entrance_description: str = ""
    directions: str = ""
    photos: list[MediaAsset] = field(default_factory=list)
    voice_note: MediaAsset | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_used_at: datetime | None = None
    link: ShareLink | None = None
    events: list[Event] = field(default_factory=list)

    def link_state(self, now: datetime) -> LinkState:
        return self.link.state(now) if self.link else "none"

    def has_event(self, event_type: str, since: datetime | None = None) -> bool:
        return any(e.type == event_type and (since is None or e.at >= since) for e in self.events)


@dataclass
class OwnerStats:
    addresses: int
    active_links: int
    link_opens: int
    deliveries: int
    landmark_confirmations: int
    landmark_rejections: int
