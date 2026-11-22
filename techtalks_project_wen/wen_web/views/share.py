"""Pages opened from a private share link (drivers, guests). No login.

Access rule: the unguessable token is the only key. Once a link is delivered,
revoked or past its expiry date, nothing about the address is shown or served.
"""

from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from ..services import get_repository
from .common import is_htmx, map_payload


def _unavailable(request, card=None):
    state = card.link_state(timezone.now()) if card else "missing"
    status = 404 if state == "missing" else 410
    return render(request, "wen/share/unavailable.html", {"state": state}, status=status)


def _active_card(token):
    card = get_repository().get_by_token(token)
    if card and card.link_state(timezone.now()) == "active":
        return card, None
    return None, card


def _no_index(response):
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "same-origin"
    response["Cache-Control"] = "private, no-store"
    return response


@never_cache
@require_GET
def share_card(request, token):
    card, ended = _active_card(token)
    if card is None:
        return _no_index(_unavailable(request, ended))
    get_repository().record_link_event(token, "link_opened")
    return _no_index(render(request, "wen/share/card.html", {
        "card": card,
        "token": token,
        "map_data": map_payload(card),
        "now": timezone.now(),
    }))


@never_cache
@require_GET
def driver_mode(request, token):
    card, ended = _active_card(token)
    if card is None:
        return _no_index(_unavailable(request, ended))
    since = card.link.created_at
    if card.has_event("landmark_rejected", since):
        landmark_state = "rejected"
    elif card.has_event("landmark_confirmed", since):
        landmark_state = "confirmed"
    else:
        landmark_state = "pending"
    return _no_index(render(request, "wen/share/driver.html", {
        "card": card,
        "token": token,
        "map_data": map_payload(card),
        "landmark_state": landmark_state,
        "stage": "landmark" if landmark_state == "pending" else "entrance",
        "now": timezone.now(),
    }))


@require_POST
def driver_landmark(request, token):
    """The driver says whether the suggested landmark was right."""
    verdict = request.POST.get("verdict")
    if verdict not in ("confirmed", "rejected"):
        return render(request, "wen/share/partials/landmark_check.html", {"error": True, "token": token}, status=400)
    card = get_repository().record_link_event(token, f"landmark_{verdict}")
    if card is None:
        return _unavailable(request, get_repository().get_by_token(token))
    context = {"card": card, "token": token, "landmark_state": verdict}
    if is_htmx(request):
        return render(request, "wen/share/partials/landmark_check.html", context)
    return driver_mode(request, token)


@require_POST
def driver_delivered(request, token):
    card = get_repository().mark_delivered(token)
    if card is None:
        return _no_index(_unavailable(request, get_repository().get_by_token(token)))
    return _no_index(render(request, "wen/share/delivered.html", {"card": card}))


@require_GET
def share_media(request, token, asset_id):
    card, _ended = _active_card(token)
    if card is None:
        raise Http404
    opened = get_repository().open_media(card, asset_id)
    if not opened:
        raise Http404
    fh, content_type = opened
    response = FileResponse(fh, content_type=content_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex"
    return response
