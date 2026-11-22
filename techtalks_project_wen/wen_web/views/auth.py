from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..forms import EmailLoginForm, RegisterForm


class LoginView(auth_views.LoginView):
    template_name = "wen/auth/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("web:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, _("Your account is ready. Create your first address card."))
        return redirect("web:dashboard")
    return render(request, "wen/auth/register.html", {"form": form})


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "wen/auth/password_reset_form.html"
    email_template_name = "wen/auth/email/password_reset_email.txt"
    html_email_template_name = "wen/auth/email/password_reset_email.html"
    subject_template_name = "wen/auth/email/password_reset_subject.txt"
    success_url = reverse_lazy("web:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "wen/auth/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "wen/auth/password_reset_confirm.html"
    success_url = reverse_lazy("web:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "wen/auth/password_reset_complete.html"
