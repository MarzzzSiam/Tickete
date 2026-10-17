from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.CsrfView.as_view()),
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("refresh/", views.RefreshView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("me/", views.MeView.as_view()),
    path("change-password/", views.ChangePasswordView.as_view()),
    path("verify-email/request/", views.VerifyRequestView.as_view()),
    path("verify-email/confirm/", views.VerifyConfirmView.as_view()),
    path("password-reset/request/", views.ResetRequestView.as_view()),
    path("password-reset/confirm/", views.ResetConfirmView.as_view()),
]
