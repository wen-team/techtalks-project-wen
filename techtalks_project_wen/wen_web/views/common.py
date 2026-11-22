"""Helpers shared by the view modules."""

from django.http import Http404
from django.utils import timezone

from ..services import get_repository, get_resolver
from ..services.types import AddressCard, Pin


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def owner_card_or_404(request, address_id: str) -> AddressCard:
    card = get_repository().get_for_owner(request.user.id, address_id)
    if card is None:
        raise Http404("Address not found")
    return card


def address_data_from_form(cleaned: dict) -> dict:
    """Map a cleaned AddressDetailsForm onto the repository's data dict."""
    landmark = cleaned.get("landmark")
    source = cleaned["pin_source"]
    if landmark is None and source == "landmark":
        source = "manual"
    return {
        "title": cleaned["title"],
        "description": cleaned["description"].strip(),
        "language": cleaned.get("language") or get_resolver().resolve(cleaned["description"]).language,
        "landmark": landmark,
        "pin": Pin(lat=round(cleaned["pin_lat"], 6), lng=round(cleaned["pin_lng"], 6), source=source),
        "match_quality": (cleaned.get("match_quality") or None) if landmark else None,
        "building_description": cleaned.get("building_description", "").strip(),
        "building_color": cleaned.get("building_color", "").strip(),
        "floor": cleaned.get("floor", "").strip(),
        "entrance_description": cleaned.get("entrance_description", "").strip(),
        "directions": cleaned.get("directions", "").strip(),
    }


def card_initial(card: AddressCard) -> dict:
    """Initial values for editing an existing card."""
    return {
        "title": card.title,
        "description": card.description,
        "building_description": card.building_description,
        "building_color": card.building_color,
        "floor": card.floor,
        "entrance_description": card.entrance_description,
        "directions": card.directions,
        "landmark_id": card.landmark.id if card.landmark else "",
        "pin_lat": card.pin.lat,
        "pin_lng": card.pin.lng,
        "pin_source": card.pin.source,
        "match_quality": card.match_quality or "",
        "language": card.language,
    }


def map_payload(card: AddressCard) -> dict:
    """What the Leaflet components need to draw a card's map. No owner data."""
    return {
        "pin": {"lat": card.pin.lat, "lng": card.pin.lng, "source": card.pin.source},
        "landmark": card.landmark.to_dict() if card.landmark else None,
        "quality": card.match_quality,
    }


def now():
    return timezone.now()
