from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import get_language, get_language_bidi, gettext as _

from . import services
from .constants import BUILDING_COLORS, CATEGORY_LABELS, LANGUAGE_LABELS, MATCH_LABELS


def _js_strings() -> dict:
    """Strings the JavaScript needs, translated for the current request."""
    return {
        "copied": _("Link copied"),
        "copyFailed": _("Couldn't copy. Select the link and copy it manually."),
        "resolveFailed": _("Couldn't reach the resolver. Check your connection and try again."),
        "tooShort": _("Describe the place in a few more words."),
        "micDenied": _("Microphone access was blocked. Allow it in your browser settings, or upload a recording."),
        "micUnsupported": _("This browser can't record audio. Upload a recording instead."),
        "tooManyPhotos": _("You can add up to 4 entrance photos."),
        "photoTooBig": _("Each photo must be smaller than 8 MB."),
        "photoType": _("Photos must be JPEG, PNG or WebP images."),
        "voiceTooLong": _("Recording stopped at 2 minutes."),
        "mapUnavailable": _("The map couldn't load. Directions and photos are still below."),
        "pinMoved": _("Pin moved. The card will show your building instead of the landmark."),
        "pinPlaced": _("Pin placed."),
        "landmark": _("Landmark"),
        "yourBuilding": _("Your building"),
        "shareTitle": _("Address card"),
        "shareText": _("Here is my address on Wen:"),
        "networkError": _("Something went wrong. Check your connection and try again."),
        "languages": {k: str(v) for k, v in LANGUAGE_LABELS.items()},
        "match": {k: str(v) for k, v in MATCH_LABELS.items()},
        "categories": {k: str(v) for k, v in CATEGORY_LABELS.items()},
        "colors": {key: str(label) for key, label, _hex in BUILDING_COLORS},
    }


def wen(request):
    return {
        "wen_simulated": services.is_simulated(),
        "wen_building_colors": BUILDING_COLORS,
        "wen_js_config": {
            "lang": get_language(),
            "rtl": get_language_bidi(),
            "tiles": getattr(settings, "WEN_MAP_TILES", {}),
            "icons": static("wen/img/icons.svg"),
            "resolveUrl": reverse("web:resolve_api"),
            "simulated": services.is_simulated(),
            "t": _js_strings(),
        },
    }
