"""Signed-in pages: dashboard, address creation, saved addresses, insights."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from ..constants import DEFAULT_LINK_LIFETIME
from ..forms import AddressDetailsForm, AddressEditForm, LinkForm
from ..services import get_repository, get_resolver
from .common import address_data_from_form, card_initial, is_htmx, map_payload, owner_card_or_404


def _greeting() -> str:
    hour = timezone.localtime().hour
    if hour < 12:
        return _("Good morning")
    if hour < 18:
        return _("Good afternoon")
    return _("Good evening")


@login_required
@require_GET
def dashboard(request):
    repo = get_repository()
    cards = repo.list_for_owner(request.user.id)
    return render(request, "wen/app/dashboard.html", {
        "greeting": _greeting(),
        "recent": cards[:4],
        "stats": repo.stats_for_owner(request.user.id),
        "now": timezone.now(),
        "nav": "dashboard",
    })


FILTERS = ("all", "active", "none", "ended")
SORTS = ("recent", "newest", "name")


@login_required
@require_GET
def address_list(request):
    now = timezone.now()
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")
    sort = request.GET.get("sort", "recent")
    status = status if status in FILTERS else "all"
    sort = sort if sort in SORTS else "recent"

    all_cards = get_repository().list_for_owner(request.user.id)
    cards = all_cards
    if q:
        needle = q.casefold()

        def haystack(c):
            parts = [c.title, c.description, c.building_description, c.floor]
            if c.landmark:
                parts += [c.landmark.name, c.landmark.name_ar, c.landmark.area, c.landmark.area_ar]
            return " ".join(parts).casefold()

        cards = [c for c in cards if needle in haystack(c)]
    if status == "active":
        cards = [c for c in cards if c.link_state(now) == "active"]
    elif status == "none":
        cards = [c for c in cards if c.link_state(now) == "none"]
    elif status == "ended":
        cards = [c for c in cards if c.link_state(now) in ("expired", "delivered", "revoked")]
    if sort == "newest":
        cards = sorted(cards, key=lambda c: c.created_at, reverse=True)
    elif sort == "name":
        cards = sorted(cards, key=lambda c: c.title.casefold())

    context = {
        "cards": cards,
        "total": len(all_cards),
        "q": q,
        "status": status,
        "sort": sort,
        "now": now,
        "nav": "addresses",
    }
    template = "wen/app/partials/address_results.html" if is_htmx(request) else "wen/app/addresses.html"
    return render(request, template, context)


def _create_context(form, step=1, initial_state=None):
    return {
        "form": form,
        "step": step,
        "initial_state": initial_state or {},
        "nav": "create",
    }


@login_required
@require_http_methods(["GET", "POST"])
def address_create(request):
    resolver = get_resolver()
    if request.method == "POST":
        form = AddressDetailsForm(request.POST, request.FILES, resolver=resolver)
        if form.is_valid():
            data = address_data_from_form(form.cleaned_data)
            card = get_repository().create(
                request.user.id, data, form.cleaned_data["photos"], form.cleaned_data["voice_note"]
            )
            messages.success(request, _("Address card saved. Create its private link to share it."))
            return redirect("web:address_share", address_id=card.id)
        # Re-open the flow on the details step with what the user already chose.
        state = {
            "description": request.POST.get("description", ""),
            "landmark_id": request.POST.get("landmark_id", ""),
            "pin": {
                "lat": form.cleaned_data.get("pin_lat"),
                "lng": form.cleaned_data.get("pin_lng"),
                "source": request.POST.get("pin_source", "landmark"),
            },
            "resolution": resolver.resolve(request.POST.get("description", "")).to_dict()
            if len(request.POST.get("description", "")) >= 6 else None,
        }
        return render(request, "wen/app/create.html", _create_context(form, step=3, initial_state=state), status=422)

    description = request.GET.get("q", "")[:1000]
    form = AddressDetailsForm(initial={"description": description})
    return render(request, "wen/app/create.html", _create_context(form, initial_state={"description": description}))


@login_required
@require_GET
def address_share(request, address_id):
    """Step 4 of the creation flow: preview the card and create its link."""
    card = owner_card_or_404(request, address_id)
    return render(request, "wen/app/share_step.html", {
        "card": card,
        "map_data": map_payload(card),
        "link_form": LinkForm(initial={"lifetime": DEFAULT_LINK_LIFETIME}),
        "now": timezone.now(),
        "step": 4,
        "nav": "create",
    })


@login_required
@require_GET
def address_detail(request, address_id):
    card = owner_card_or_404(request, address_id)
    get_repository().touch(request.user.id, address_id)
    return render(request, "wen/app/detail.html", {
        "card": card,
        "map_data": map_payload(card),
        "link_form": LinkForm(initial={"lifetime": DEFAULT_LINK_LIFETIME}),
        "now": timezone.now(),
        "events": list(reversed(card.events))[:12],
        "nav": "addresses",
    })


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request, address_id):
    card = owner_card_or_404(request, address_id)
    photo_ids = [p.id for p in card.photos]
    resolver = get_resolver()
    if request.method == "POST":
        form = AddressEditForm(request.POST, request.FILES, resolver=resolver, photo_ids=photo_ids)
        if form.is_valid():
            data = address_data_from_form(form.cleaned_data)
            get_repository().update(
                request.user.id, address_id, data,
                new_photos=form.cleaned_data["photos"],
                remove_photo_ids=form.cleaned_data["remove_photos"],
                voice_note=form.cleaned_data["voice_note"],
                remove_voice_note=form.cleaned_data["remove_voice_note"],
            )
            messages.success(request, _("Changes saved."))
            return redirect("web:address_detail", address_id=address_id)
        status = 422
    else:
        form = AddressEditForm(initial=card_initial(card), resolver=resolver, photo_ids=photo_ids)
        status = 200
    return render(request, "wen/app/edit.html", {
        "card": card,
        "form": form,
        "map_data": map_payload(card),
        "nav": "addresses",
    }, status=status)


@login_required
@require_POST
def address_delete(request, address_id):
    card = owner_card_or_404(request, address_id)
    get_repository().delete(request.user.id, card.id)
    messages.success(request, _("“%(title)s” was deleted.") % {"title": card.title})
    return redirect("web:addresses")


@login_required
@require_POST
def link_issue(request, address_id):
    owner_card_or_404(request, address_id)
    form = LinkForm(request.POST)
    lifetime = form.cleaned_data["lifetime"] if form.is_valid() else DEFAULT_LINK_LIFETIME
    card = get_repository().issue_link(request.user.id, address_id, lifetime)
    context = {"card": card, "now": timezone.now(), "link_form": LinkForm(initial={"lifetime": lifetime}),
               "just_created": True}
    if is_htmx(request):
        return render(request, "wen/components/link_panel.html", context)
    messages.success(request, _("Private link created."))
    return redirect("web:address_detail", address_id=address_id)


@login_required
@require_POST
def link_revoke(request, address_id):
    owner_card_or_404(request, address_id)
    card = get_repository().revoke_link(request.user.id, address_id) or owner_card_or_404(request, address_id)
    context = {"card": card, "now": timezone.now(), "link_form": LinkForm(initial={"lifetime": DEFAULT_LINK_LIFETIME})}
    if is_htmx(request):
        return render(request, "wen/components/link_panel.html", context)
    messages.success(request, _("Link turned off. Anyone who has it can no longer open the card."))
    return redirect("web:address_detail", address_id=address_id)


@login_required
@require_GET
def owner_media(request, address_id, asset_id):
    card = owner_card_or_404(request, address_id)
    opened = get_repository().open_media(card, asset_id)
    if not opened:
        raise Http404
    fh, content_type = opened
    response = FileResponse(fh, content_type=content_type)
    response["Cache-Control"] = "private, max-age=3600"
    return response


@login_required
@require_GET
def insights(request):
    """Business view. Every number comes from recorded events; nothing is estimated."""
    repo = get_repository()
    cards = repo.list_for_owner(request.user.id)
    stats = repo.stats_for_owner(request.user.id)
    deliveries = []
    for card in cards:
        opened = None
        for event in card.events:
            if event.type == "link_created":
                opened = None
            elif event.type == "link_opened" and opened is None:
                opened = event.at
            elif event.type == "delivered":
                minutes = round((event.at - opened).total_seconds() / 60) if opened else None
                deliveries.append({"card": card, "opened": opened, "delivered": event.at, "minutes": minutes})
    deliveries.sort(key=lambda d: d["delivered"], reverse=True)
    timed = [d["minutes"] for d in deliveries if d["minutes"] is not None]
    median = sorted(timed)[len(timed) // 2] if timed else None
    checks = stats.landmark_confirmations + stats.landmark_rejections
    return render(request, "wen/app/insights.html", {
        "stats": stats,
        "deliveries": deliveries[:10],
        "median_minutes": median,
        "landmark_checks": checks,
        "landmark_rate": round(100 * stats.landmark_confirmations / checks) if checks else None,
        "nav": "insights",
    })
