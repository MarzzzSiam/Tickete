from django.urls import path

from .views import CancelOrder, CreateOrder, OrderStatus, StartPayment, VerifyPayment

urlpatterns = [
    path("orders/", CreateOrder.as_view()),
    path("orders/<uuid:pk>/status/", OrderStatus.as_view()),
    path("orders/<uuid:pk>/payments/", StartPayment.as_view()),
    path("orders/<uuid:pk>/verify/", VerifyPayment.as_view()),
    path("orders/<uuid:pk>/cancel/", CancelOrder.as_view()),
]
