from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext as _

from ..constants import BUILDING_COLOR_MAP, CATEGORY_LABELS, LANGUAGE_LABELS, MATCH_LABELS

register = template.Library()

# Icons whose meaning has a direction; they are mirrored in right-to-left layouts.
DIRECTIONAL = {"arrow-right", "arrow-left", "chevron-right", "chevron-left", "corner-up-right", "log-out", "undo-2"}


@register.simple_tag
def icon(name, size=20, label=None, cls=""):
    classes = "icon" + (" icon--flip" if name in DIRECTIONAL else "") + (f" {cls}" if cls else "")
    aria = format_html('role="img" aria-label="{}"', label) if label else mark_safe('aria-hidden="true"')
    return format_html(
        '<svg class="{}" width="{}" height="{}" {} focusable="false"><use href="{}#{}"></use></svg>',
        classes, size, size, aria, static("wen/img/icons.svg"), name,
    )


def _arabic() -> bool:
    return (get_language() or "").startswith("ar")


@register.filter
def lm_name(landmark):
    if not landmark:
        return ""
    return landmark.name_ar if _arabic() and landmark.name_ar else landmark.name


@register.filter
def lm_name_alt(landmark):
    """The landmark name in the *other* language, shown as a secondary line."""
    if not landmark:
        return ""
    return landmark.name if _arabic() else landmark.name_ar


@register.filter
def lm_area(landmark):
    if not landmark:
        return ""
    return landmark.area_ar if _arabic() and landmark.area_ar else landmark.area


@register.filter
def category_label(key):
    return CATEGORY_LABELS.get(key, CATEGORY_LABELS["landmark"])


@register.filter
def color_hex(key):
    return BUILDING_COLOR_MAP.get(key, (None, ""))[1]


@register.filter
def color_label(value):
    if not value:
        return ""
    entry = BUILDING_COLOR_MAP.get(value)
    return entry[0] if entry else value


@register.filter
def floor_label(value):
    value = (value or "").strip()
    if not value:
        return ""
    if value == "0":
        return _("Ground floor")
    if value.isdigit():
        return _("Floor %(number)s") % {"number": value}
    return value


@register.filter
def language_label(key):
    return LANGUAGE_LABELS.get(key, "")


@register.filter
def match_label(key):
    return MATCH_LABELS.get(key, "")


@register.filter
def link_state(card, now):
    return card.link_state(now)


@register.filter
def event_label(event_type):
    # Wrapped in _() at call time so the strings are translated per request.
    labels = {
        "created": _("Address card created"),
        "link_created": _("Private link created"),
        "link_opened": _("Link opened"),
        "landmark_confirmed": _("Driver confirmed the landmark"),
        "landmark_rejected": _("Driver reported the landmark was wrong"),
        "delivered": _("Delivery confirmed, link expired"),
        "link_revoked": _("Link turned off"),
    }
    return labels.get(event_type, event_type)


@register.filter
def styled(bound_field, kind=""):
    """Render a form field's widget with the Wen input classes and error state."""
    widget = bound_field.field.widget
    name = widget.__class__.__name__
    if name == "Textarea":
        css = "textarea"
    elif name in ("Select", "SelectMultiple"):
        css = "select"
    else:
        css = "input"
    attrs = {"class": css}
    if bound_field.errors:
        attrs["aria-invalid"] = "true"
    if kind == "password":
        attrs["x-bind:type"] = "show ? 'text' : 'password'"
    return bound_field.as_widget(attrs=attrs)


@register.filter
def initials(user):
    name = (user.get_full_name() or user.get_username() or "?").strip()
    parts = name.split()
    return "".join(p[0] for p in parts[:2]).upper() if parts else "?"


@register.filter
def display_name(user):
    return user.first_name or user.get_full_name() or user.get_username().split("@")[0]
