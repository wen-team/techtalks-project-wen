"""Interfaces the frontend depends on.

Backend lanes replace the mock implementations by writing classes with the
same methods (for example an ORM-backed repository, or a client for wen_api)
and registering them in ``wen_web.services.get_*``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO, Iterable

from .types import AddressCard, Landmark, OwnerStats, Resolution


class LandmarkResolver(ABC):
    """Turns a free-text Lebanese description into candidate landmarks."""

    simulated: bool = False

    @abstractmethod
    def resolve(self, text: str) -> Resolution: ...

    @abstractmethod
    def get_landmark(self, landmark_id: str) -> Landmark | None: ...


class AddressRepository(ABC):
    """Stores address cards and their private share links.

    Every owner-facing method takes ``owner_id`` and must only return that
    owner's data. Share-link methods take the unguessable token instead.
    """

    # Owner side
    @abstractmethod
    def list_for_owner(self, owner_id: int) -> list[AddressCard]: ...

    @abstractmethod
    def get_for_owner(self, owner_id: int, address_id: str) -> AddressCard | None: ...

    @abstractmethod
    def create(self, owner_id: int, data: dict, photos: Iterable, voice_note=None) -> AddressCard: ...

    @abstractmethod
    def update(
        self,
        owner_id: int,
        address_id: str,
        data: dict,
        new_photos: Iterable = (),
        remove_photo_ids: Iterable[str] = (),
        voice_note=None,
        remove_voice_note: bool = False,
    ) -> AddressCard | None: ...

    @abstractmethod
    def delete(self, owner_id: int, address_id: str) -> bool: ...

    @abstractmethod
    def touch(self, owner_id: int, address_id: str) -> None:
        """Record that the owner used this address (for 'recently used')."""

    @abstractmethod
    def issue_link(self, owner_id: int, address_id: str, ttl_hours: int) -> AddressCard | None:
        """Create a new private link. Any previous link stops working."""

    @abstractmethod
    def revoke_link(self, owner_id: int, address_id: str) -> AddressCard | None: ...

    @abstractmethod
    def stats_for_owner(self, owner_id: int) -> OwnerStats: ...

    # Share-link side (drivers, no login)
    @abstractmethod
    def get_by_token(self, token: str) -> AddressCard | None:
        """Return the card for a token, whatever its state. Callers check the state."""

    @abstractmethod
    def record_link_event(self, token: str, event_type: str) -> AddressCard | None: ...

    @abstractmethod
    def mark_delivered(self, token: str) -> AddressCard | None:
        """Confirm delivery. The link expires immediately (proposal, section E)."""

    # Media
    @abstractmethod
    def open_media(self, address: AddressCard, asset_id: str) -> tuple[BinaryIO, str] | None:
        """Return (file object, content type) for an asset that belongs to ``address``."""
