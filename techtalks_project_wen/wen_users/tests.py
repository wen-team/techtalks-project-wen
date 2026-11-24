from django.test import TestCase
from django.contrib.auth import get_user_model
from wen_web.forms import EmailLoginForm, RegisterForm


class AuthenticationTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.password = "Wen-Secure-2026!"

        self.user = self.User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password=self.password
        )

    def test_valid_login(self):
        form = EmailLoginForm(data={
            "username": "test@example.com",
            "password": self.password
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_password(self):
        form = EmailLoginForm(data={
            "username": "test@example.com",
            "password": "WrongPassword"
        })
        self.assertFalse(form.is_valid())

    def test_nonexistent_account(self):
        form = EmailLoginForm(data={
            "username": "unknown@example.com",
            "password": self.password
        })
        self.assertFalse(form.is_valid())

    def test_uppercase_email_login(self):
        form = EmailLoginForm(data={
            "username": "TEST@EXAMPLE.COM",
            "password": self.password
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_registration(self):
        form = RegisterForm(data={
            "full_name": "Test User",
            "email": "new@example.com",
            "password1": self.password,
            "password2": self.password
        })

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password(self.password))

    def test_duplicate_email(self):
        form = RegisterForm(data={
            "full_name": "Duplicate User",
            "email": "TEST@example.com",
            "password1": self.password,
            "password2": self.password
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_mismatch(self):
        form = RegisterForm(data={
            "full_name": "Test User",
            "email": "new@example.com",
            "password1": self.password,
            "password2": "DifferentPassword123!"
        })

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_invalid_email(self):
        form = RegisterForm(data={
            "full_name": "Test User",
            "email": "invalid-email",
            "password1": self.password,
            "password2": self.password
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
