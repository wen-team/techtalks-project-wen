from django.apps import AppConfig


class WenWebConfig(AppConfig):
    """Frontend for Wen: server-rendered pages (Django templates + HTMX + Alpine + Leaflet).

    All data access goes through ``wen_web.services`` so the UI never talks to
    storage or the resolver directly. See ``wen_web/README.md``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "wen_web"
    verbose_name = "Wen frontend"
