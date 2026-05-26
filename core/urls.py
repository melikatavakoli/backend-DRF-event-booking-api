from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path(
        "auth/register/",
        views.RegisterWithOTPView.as_view(),
        name="auth_register",
    ),
    path("auth/otp/send/", views.SendOTPView.as_view(), name="auth_send_otp"),
    path("auth/otp/login/", views.LoginOTPView.as_view(), name="auth_login_otp"),
    path("auth/login/", views.LoginView.as_view(), name="auth_login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth_logout"),
    path(
        "auth/password/reset/",
        views.ResetPasswordView.as_view(),
        name="password_reset",
    ),
    path(
        "auth/password/change/",
        views.ChangePasswordView.as_view(),
        name="password_change",
    ),
    path("users/", views.UserListView.as_view(), name="user_list"),
]
