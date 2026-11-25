import json

from django.test import TestCase, override_settings
from django.urls import reverse
from wen_web.services import get_resolver


@override_settings(WEN_SERVICE_BACKEND="mock")
class AddressAPITests(TestCase):

    def setUp(self):
        get_resolver.cache_clear()
        self.addCleanup(get_resolver.cache_clear)
        self.url = reverse("web:resolve_api")

    def send_request(self, data):
        return self.client.post(
            self.url,
            json.dumps(data),
            content_type="application/json"
        )

    def test_valid_address(self):
        response = self.send_request({
            "text": "near AUB main gate"
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["candidates"])

    def test_empty_description(self):
        response = self.send_request({"text": ""})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "too_short")

    def test_missing_text_parameter(self):
        response = self.send_request({})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "too_short")

    def test_short_description(self):
        response = self.send_request({"text": "hello"})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "too_short")

    def test_long_description(self):
        response = self.send_request({"text": "a" * 1001})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "too_long")

    def test_malformed_json(self):
        response = self.client.post(
            self.url,
            '{"text":',
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_json")

    def test_get_method_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_unknown_landmark(self):
        response = self.send_request({
            "text": "behind my grandmother's house"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidates"], [])

    def test_whitespace_description(self):
        response = self.send_request({"text": "       "})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "too_short")

    def test_surrounding_whitespace(self):
        response = self.send_request({
            "text": "   near AUB main gate   "
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["candidates"])
