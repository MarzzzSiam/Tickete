from django.urls import path

from . import views

urlpatterns = [
    path("tickets/recovery/", views.StartRecovery.as_view()),
    path("tickets/recovery/<uuid:pk>/verify/", views.VerifyRecovery.as_view()),
    path("tickets/recovery/<uuid:pk>/orders/", views.RecoveryOrders.as_view()),
    path(
        "tickets/recovery/<uuid:pk>/orders/<uuid:order_id>/resend/", views.RecoveryResend.as_view()
    ),
    path(
        "tickets/recovery/<uuid:pk>/orders/<uuid:order_id>/pdf/", views.RecoveryDownload.as_view()
    ),
]
