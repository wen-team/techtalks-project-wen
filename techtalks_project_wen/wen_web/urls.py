from django.contrib.auth import views as django_auth_views
from django.urls import path

from .views import app, auth, public, share

app_name = "web"

urlpatterns = [
    # Public
    path("", public.landing, name="landing"),
    path("ui-api/resolve/", public.resolve_api, name="resolve_api"),

    # Accounts
    path("accounts/login/", auth.LoginView.as_view(), name="login"),
    path("accounts/logout/", django_auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", auth.register, name="register"),
    path("accounts/password-reset/", auth.PasswordResetView.as_view(), name="password_reset"),
    path("accounts/password-reset/sent/", auth.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/done/", auth.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Signed-in app
    path("app/", app.dashboard, name="dashboard"),
    path("app/addresses/", app.address_list, name="addresses"),
    path("app/addresses/new/", app.address_create, name="address_create"),
    path("app/addresses/<str:address_id>/", app.address_detail, name="address_detail"),
    path("app/addresses/<str:address_id>/share/", app.address_share, name="address_share"),
    path("app/addresses/<str:address_id>/edit/", app.address_edit, name="address_edit"),
    path("app/addresses/<str:address_id>/delete/", app.address_delete, name="address_delete"),
    path("app/addresses/<str:address_id>/link/", app.link_issue, name="link_issue"),
    path("app/addresses/<str:address_id>/link/revoke/", app.link_revoke, name="link_revoke"),
    path("app/addresses/<str:address_id>/media/<str:asset_id>/", app.owner_media, name="owner_media"),
    path("app/insights/", app.insights, name="insights"),

    # Private share links (no login; the token is the key)
    path("c/<str:token>/", share.share_card, name="share_card"),
    path("c/<str:token>/drive/", share.driver_mode, name="driver_mode"),
    path("c/<str:token>/drive/landmark/", share.driver_landmark, name="driver_landmark"),
    path("c/<str:token>/drive/delivered/", share.driver_delivered, name="driver_delivered"),
    path("c/<str:token>/media/<str:asset_id>/", share.share_media, name="share_media"),
]
