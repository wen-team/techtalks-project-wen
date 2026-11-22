import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from django.utils.translation import gettext as _

from ..services import get_resolver
from ..services.types import AddressCard, Pin
from .common import map_payload

MAX_DESCRIPTION = 1000


def _example_card() -> AddressCard:
    """A clearly labelled sample card for the landing page. Not stored anywhere."""
    landmark = get_resolver().get_landmark("mar-elias-church")
    return AddressCard(
        id="example",
        owner_id=0,
        title=_("Rima's flat, Mar Elias"),
        description="After Mar Elias church, second right, next to Abu Ali's bakery, "
                    "the building with green shutters, third floor.",
        language="en",
        landmark=landmark,
        pin=Pin(lat=landmark.lat, lng=landmark.lng, source="landmark") if landmark else Pin(33.8873, 35.4867, "manual"),
        match_quality="strong",
        building_color="green",
        building_description=_("Five floors, green shutters, a pharmacy on the ground floor."),
        floor="3",
        entrance_description=_("Glass door to the left of the pharmacy. Press 3B."),
        directions=_("Take the second street on the right after the church. The building is next to Abu Ali's bakery."),
    )


@require_GET
def landing(request):
    card = _example_card()
    return render(request, "wen/pages/landing.html", {"example": card, "example_map": map_payload(card)})


@require_POST
def resolve_api(request):
    """POST {"text": "..."} -> candidate landmarks.

    Used by the create flow and by the live demo on the landing page.
    CSRF-protected; the frontend sends the token from the page.
    """
    try:
        payload = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    text = str(payload.get("text", "")).strip()
    if len(text) < 6:
        return JsonResponse({"error": "too_short"}, status=422)
    if len(text) > MAX_DESCRIPTION:
        return JsonResponse({"error": "too_long"}, status=422)
    return JsonResponse(get_resolver().resolve(text).to_dict())
