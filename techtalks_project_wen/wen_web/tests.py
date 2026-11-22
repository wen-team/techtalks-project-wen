import json
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

# Absolute imports on purpose: views import "wen_web.services", and the cached
# repository must be the same object the views use.
from wen_web.services import get_repository, get_resolver
from wen_web.services.mock_resolver import MockLandmarkResolver, detect_language, extract_hints

TINY_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00" + b"\x08" * 64
    + b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01" + b"\x00" * 15
    + b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
)


class ResolverTests(TestCase):
    def setUp(self):
        self.resolver = MockLandmarkResolver()

    def test_english_arabic_and_arabizi_point_to_the_same_landmark(self):
        for text in (
            "Near Saint Charbel church, 2nd floor",
            "قرب كنيسة مار شربل، الطابق الثاني",
            "jamb kenise mar charbel, tabe2 2",
        ):
            with self.subTest(text=text):
                result = self.resolver.resolve(text)
                self.assertEqual(result.candidates[0].landmark.id, "saint-charbel-jdeideh")
                self.assertEqual(result.hints.get("floor"), "2")

    def test_similar_generic_words_do_not_cross_match(self):
        result = self.resolver.resolve("After Mar Elias church, second right")
        self.assertEqual([c.landmark.id for c in result.candidates], ["mar-elias-church"])

    def test_unknown_place_returns_no_candidates(self):
        self.assertEqual(self.resolver.resolve("behind my grandmother's house").candidates, [])

    def test_language_detection(self):
        self.assertEqual(detect_language("after the church, 3rd floor"), "en")
        self.assertEqual(detect_language("ba3d el kenise, tabe2 3"), "arabizi")
        self.assertEqual(detect_language("بعد الكنيسة"), "ar")

    def test_hints(self):
        self.assertEqual(extract_hints("the building with green shutters, third floor"),
                         {"floor": "3", "building_color": "green"})
        self.assertEqual(extract_hints("البناية الخضرا، الطابق الأرضي"), {"floor": "0", "building_color": "green"})


@override_settings(WEN_SERVICE_BACKEND="mock")
class FlowTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.override = override_settings(WEN_MOCK_DATA_DIR=self.tmp)
        self.override.enable()
        get_repository.cache_clear()
        get_resolver.cache_clear()
        User = get_user_model()
        self.user = User.objects.create_user("rima@example.com", "rima@example.com", "Cedar-Route-2026", first_name="Rima")
        self.other = User.objects.create_user("sami@example.com", "sami@example.com", "Cedar-Route-2026")
        self.client.force_login(self.user)

    def tearDown(self):
        self.override.disable()
        get_repository.cache_clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def create_card(self, **extra):
        landmark = get_resolver().get_landmark("mar-elias-church")
        data = {
            "title": "Home, Mar Elias",
            "description": "After Mar Elias church, second right, third floor",
            "landmark_id": landmark.id,
            "pin_lat": landmark.lat,
            "pin_lng": landmark.lng,
            "pin_source": "landmark",
            "match_quality": "strong",
            "floor": "3",
            "building_color": "green",
            "photos": [SimpleUploadedFile("door.jpg", TINY_JPEG, content_type="image/jpeg")],
            **extra,
        }
        response = self.client.post(reverse("web:address_create"), data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["form"].errors)
        return get_repository().list_for_owner(self.user.id)[0]

    def test_public_pages_render(self):
        self.client.logout()
        for name in ("landing", "login", "register", "password_reset"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f"web:{name}")).status_code, 200)

    def test_app_pages_require_login(self):
        self.client.logout()
        response = self.client.get(reverse("web:dashboard"))
        self.assertRedirects(response, reverse("web:login") + "?next=" + reverse("web:dashboard"))

    def test_register_logs_in(self):
        self.client.logout()
        response = self.client.post(reverse("web:register"), {
            "full_name": "Khaled Restom", "email": "Khaled@Example.com",
            "password1": "Cedar-Route-2026", "password2": "Cedar-Route-2026",
        })
        self.assertRedirects(response, reverse("web:dashboard"))
        self.assertTrue(get_user_model().objects.filter(username="khaled@example.com").exists())

    def test_resolve_api(self):
        response = self.client.post(reverse("web:resolve_api"), json.dumps({"text": "near AUB main gate"}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["simulated"])
        self.assertEqual(body["candidates"][0]["landmark"]["id"], "aub-main-gate")
        too_short = self.client.post(reverse("web:resolve_api"), json.dumps({"text": "hi"}), content_type="application/json")
        self.assertEqual(too_short.status_code, 422)

    def test_create_share_drive_deliver(self):
        card = self.create_card()
        self.assertEqual(len(card.photos), 1)
        self.assertEqual(self.client.get(reverse("web:address_share", args=[card.id])).status_code, 200)

        response = self.client.post(reverse("web:link_issue", args=[card.id]), {"lifetime": "24"}, HTTP_HX_REQUEST="true")
        self.assertContains(response, "/c/")
        card = get_repository().get_for_owner(self.user.id, card.id)
        token = card.link.token
        self.assertGreaterEqual(len(token), 20)

        driver = self.client_class()
        page = driver.get(reverse("web:share_card", args=[token]))
        self.assertContains(page, "Mar Elias Church")
        self.assertEqual(page["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(driver.get(reverse("web:share_media", args=[token, card.photos[0].id])).status_code, 200)
        self.assertEqual(driver.get(reverse("web:driver_mode", args=[token])).status_code, 200)
        self.assertContains(driver.post(reverse("web:driver_landmark", args=[token]), {"verdict": "confirmed"},
                                        HTTP_HX_REQUEST="true"), "Landmark confirmed")
        self.assertContains(driver.post(reverse("web:driver_delivered", args=[token])), "Delivered")

        self.assertEqual(driver.get(reverse("web:share_card", args=[token])).status_code, 410)
        self.assertEqual(driver.get(reverse("web:share_media", args=[token, card.photos[0].id])).status_code, 404)
        stats = get_repository().stats_for_owner(self.user.id)
        self.assertEqual((stats.deliveries, stats.landmark_confirmations, stats.link_opens), (1, 1, 1))
        self.assertContains(self.client.get(reverse("web:insights")), "Recent deliveries")

    def test_expired_and_revoked_links(self):
        card = self.create_card()
        card = get_repository().issue_link(self.user.id, card.id, 24)
        token = card.link.token
        get_repository().revoke_link(self.user.id, card.id)
        self.assertContains(self.client_class().get(reverse("web:share_card", args=[token])), "turned off", status_code=410)

        card = get_repository().issue_link(self.user.id, card.id, 24)
        self.assertNotEqual(card.link.token, token, "a new link must replace the old one")
        self.assertEqual(self.client_class().get(reverse("web:share_card", args=[token])).status_code, 404)

        later = timezone.now() + timedelta(hours=25)
        self.assertEqual(card.link_state(later), "expired")

    def test_owners_cannot_see_each_others_cards(self):
        card = self.create_card()
        self.client.force_login(self.other)
        for name in ("address_detail", "address_edit", "address_share"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f"web:{name}", args=[card.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("web:address_delete", args=[card.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("web:owner_media", args=[card.id, card.photos[0].id])).status_code, 404)

    def test_pin_outside_lebanon_is_rejected(self):
        response = self.client.post(reverse("web:address_create"), {
            "title": "Paris", "description": "Eiffel tower please", "pin_lat": 48.85, "pin_lng": 2.35,
            "pin_source": "manual",
        })
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "inside Lebanon", status_code=422)

    def test_edit_search_and_delete(self):
        card = self.create_card()
        response = self.client.post(reverse("web:address_edit", args=[card.id]), {
            "title": "Home (edited)", "description": card.description, "landmark_id": card.landmark.id,
            "pin_lat": card.pin.lat + 0.0005, "pin_lng": card.pin.lng, "pin_source": "adjusted",
            "match_quality": "strong", "remove_photos": [card.photos[0].id],
        })
        self.assertRedirects(response, reverse("web:address_detail", args=[card.id]))
        card = get_repository().get_for_owner(self.user.id, card.id)
        self.assertEqual((card.title, card.pin.source, len(card.photos)), ("Home (edited)", "adjusted", 0))

        results = self.client.get(reverse("web:addresses"), {"q": "edited"}, HTTP_HX_REQUEST="true")
        self.assertContains(results, "Home (edited)")
        self.assertNotContains(self.client.get(reverse("web:addresses"), {"q": "zzz"}), "Home (edited)")

        self.client.post(reverse("web:address_delete", args=[card.id]))
        self.assertEqual(get_repository().list_for_owner(self.user.id), [])

    def test_arabic_interface(self):
        self.client.cookies.load({"django_language": "ar"})
        response = self.client.get(reverse("web:landing"))
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, "لبنان، أخيرًا على الخريطة")
