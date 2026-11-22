from django.utils.translation import gettext_lazy as _

# Building colours offered as swatches. Keys are stored; labels are translated.
BUILDING_COLORS = [
    ("white", _("White"), "#F7F7F4"),
    ("beige", _("Beige"), "#E4D3B4"),
    ("grey", _("Grey"), "#9AA3AB"),
    ("yellow", _("Yellow"), "#E9C45A"),
    ("orange", _("Orange"), "#E08A45"),
    ("red", _("Red"), "#B9473E"),
    ("pink", _("Pink"), "#E3A3B0"),
    ("green", _("Green"), "#4E8B5F"),
    ("blue", _("Blue"), "#4A79B0"),
    ("brown", _("Brown"), "#87603F"),
    ("black", _("Black"), "#2A2D31"),
]
BUILDING_COLOR_MAP = {key: (label, hex_) for key, label, hex_ in BUILDING_COLORS}

LINK_LIFETIMES = [
    (24, _("24 hours")),
    (72, _("3 days")),
    (168, _("7 days")),
    (720, _("30 days")),
]
DEFAULT_LINK_LIFETIME = 168

LANGUAGE_LABELS = {
    "ar": _("Arabic"),
    "arabizi": _("Arabizi"),
    "en": _("English"),
    "mixed": _("Mixed languages"),
}

MATCH_LABELS = {
    "strong": _("Strong match"),
    "partial": _("Possible match"),
    "weak": _("Weak match"),
}

CATEGORY_LABELS = {
    "church": _("Church"),
    "mosque": _("Mosque"),
    "university": _("University"),
    "street": _("Street"),
    "square": _("Square"),
    "mall": _("Shopping centre"),
    "roundabout": _("Roundabout"),
    "hospital": _("Hospital"),
    "landmark": _("Landmark"),
}

# Rough bounding box of Lebanon, used to reject pins dropped elsewhere.
LEBANON_BOUNDS = {"min_lat": 33.0, "max_lat": 34.75, "min_lng": 35.05, "max_lng": 36.65}

MAX_PHOTOS = 4
MAX_PHOTO_BYTES = 8 * 1024 * 1024
MAX_VOICE_BYTES = 10 * 1024 * 1024
PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
VOICE_TYPES = {
    "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/aac", "audio/wav",
    "audio/x-wav", "video/webm",  # some browsers label recorder output as video/webm
}
