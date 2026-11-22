from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .constants import (
    LEBANON_BOUNDS,
    LINK_LIFETIMES,
    DEFAULT_LINK_LIFETIME,
    MAX_PHOTO_BYTES,
    MAX_PHOTOS,
    MAX_VOICE_BYTES,
    PHOTO_TYPES,
    VOICE_TYPES,
)


# ---------------------------------------------------------------------- auth
class EmailLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Email"),
        widget=forms.TextInput(attrs={"autocomplete": "email", "inputmode": "email", "autofocus": True}),
    )

    error_messages = {
        "invalid_login": _("That email and password don't match an account. Check both and try again."),
        "inactive": _("This account is inactive."),
    }

    def clean(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if "@" in username:
            self.cleaned_data["username"] = username.lower()
        return super().clean()


class RegisterForm(forms.Form):
    full_name = forms.CharField(label=_("Full name"), max_length=120,
                                widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1 = forms.CharField(
        label=_("Password"), strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=_("At least 8 characters. Avoid common words and all-number passwords."),
    )
    password2 = forms.CharField(
        label=_("Confirm password"), strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        User = get_user_model()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists. Log in instead."))
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("The two passwords don't match."))
        if p1 and cleaned.get("email"):
            User = get_user_model()
            probe = User(username=cleaned["email"], email=cleaned["email"], first_name=cleaned.get("full_name", ""))
            try:
                password_validation.validate_password(p1, probe)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        User = get_user_model()
        full_name = self.cleaned_data["full_name"].strip()
        first, _sep, last = full_name.partition(" ")
        return User.objects.create_user(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=first[:150],
            last_name=last[:150],
        )


# ------------------------------------------------------------------ uploads
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data if d]
        return [single(data, initial)] if data else []


def _check_photos(files):
    for f in files:
        if (f.content_type or "").lower() not in PHOTO_TYPES:
            raise forms.ValidationError(_("Photos must be JPEG, PNG or WebP images."))
        if f.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError(_("Each photo must be smaller than 8 MB."))
    return files


def _check_voice(f):
    if f is None:
        return None
    content_type = (f.content_type or "").split(";")[0].lower()
    if content_type not in VOICE_TYPES:
        raise forms.ValidationError(_("The voice note must be an audio file (MP3, M4A, WebM, OGG or WAV)."))
    if f.size > MAX_VOICE_BYTES:
        raise forms.ValidationError(_("The voice note must be smaller than 10 MB."))
    return f


# ---------------------------------------------------------------- addresses
class AddressDetailsForm(forms.Form):
    """Fields shared by creating and editing an address card."""

    title = forms.CharField(label=_("Address name"), max_length=80, widget=forms.TextInput(attrs={"dir": "auto"}))
    description = forms.CharField(label=_("Original description"), max_length=1000,
                                  widget=forms.Textarea(attrs={"rows": 4, "dir": "auto"}))
    building_description = forms.CharField(label=_("Building description"), max_length=300, required=False,
                                           widget=forms.Textarea(attrs={"rows": 2, "dir": "auto"}))
    building_color = forms.CharField(label=_("Building colour"), max_length=40, required=False)
    floor = forms.CharField(label=_("Floor"), max_length=20, required=False)
    entrance_description = forms.CharField(label=_("Entrance"), max_length=300, required=False,
                                           widget=forms.Textarea(attrs={"rows": 2, "dir": "auto"}))
    directions = forms.CharField(label=_("Final directions"), max_length=600, required=False,
                                 widget=forms.Textarea(attrs={"rows": 3, "dir": "auto"}))
    landmark_id = forms.CharField(required=False, max_length=80)
    pin_lat = forms.FloatField()
    pin_lng = forms.FloatField()
    pin_source = forms.ChoiceField(choices=[("landmark", "landmark"), ("adjusted", "adjusted"), ("manual", "manual")])
    match_quality = forms.ChoiceField(required=False,
                                      choices=[("", ""), ("strong", "strong"), ("partial", "partial"), ("weak", "weak")])
    language = forms.ChoiceField(required=False,
                                 choices=[("", ""), ("ar", "ar"), ("arabizi", "arabizi"), ("en", "en"), ("mixed", "mixed")])
    photos = MultipleFileField(required=False)
    voice_note = forms.FileField(required=False)

    existing_photo_count = 0

    def __init__(self, *args, resolver=None, existing_photo_count=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolver = resolver
        self.existing_photo_count = existing_photo_count

    def clean_title(self):
        return self.cleaned_data["title"].strip()

    def clean_photos(self):
        return _check_photos(self.cleaned_data.get("photos") or [])

    def clean_voice_note(self):
        return _check_voice(self.cleaned_data.get("voice_note"))

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("pin_lat"), cleaned.get("pin_lng")
        b = LEBANON_BOUNDS
        if lat is not None and lng is not None:
            if not (b["min_lat"] <= lat <= b["max_lat"] and b["min_lng"] <= lng <= b["max_lng"]):
                raise forms.ValidationError(_("The pin must be inside Lebanon. Move it and try again."))
        elif not self.errors:
            raise forms.ValidationError(_("Choose a landmark or place the pin on the map first."))
        landmark_id = cleaned.get("landmark_id")
        cleaned["landmark"] = None
        if landmark_id and self.resolver:
            cleaned["landmark"] = self.resolver.get_landmark(landmark_id)
            if cleaned["landmark"] is None:
                raise forms.ValidationError(_("That landmark is no longer available. Resolve the description again."))
        photos = cleaned.get("photos") or []
        removed = len(cleaned.get("remove_photos") or [])
        if self.existing_photo_count - removed + len(photos) > MAX_PHOTOS:
            self.add_error("photos", _("You can add up to 4 entrance photos."))
        return cleaned


class AddressEditForm(AddressDetailsForm):
    remove_photos = forms.MultipleChoiceField(required=False, choices=())
    remove_voice_note = forms.BooleanField(required=False)

    def __init__(self, *args, photo_ids=(), **kwargs):
        super().__init__(*args, existing_photo_count=len(photo_ids), **kwargs)
        self.fields["remove_photos"].choices = [(pid, pid) for pid in photo_ids]


class LinkForm(forms.Form):
    lifetime = forms.TypedChoiceField(
        label=_("Link expires after"),
        choices=LINK_LIFETIMES,
        coerce=int,
        initial=DEFAULT_LINK_LIFETIME,
    )
