from django.urls import path

from . import views
from .coupons import CouponDetail, CouponList
from .preview import EventPreview

urlpatterns = [
    path("events/<uuid:pk>/coupons/", CouponList.as_view()),
    path("events/<uuid:pk>/coupons/<uuid:coupon_id>/", CouponDetail.as_view()),
    path("events/", views.EventList.as_view()),
    path("events/<uuid:pk>/", views.EventDetail.as_view()),
    path("events/<uuid:pk>/preview/", EventPreview.as_view()),
    path("events/<uuid:pk>/submit/", views.SubmitView.as_view()),
    path("events/<uuid:pk>/banner/", views.BannerView.as_view()),
    path("admin/events/", views.ReviewQueue.as_view()),
    path("admin/events/<uuid:pk>/approve/", views.ApproveView.as_view()),
    path("admin/events/<uuid:pk>/reject/", views.RejectView.as_view()),
    path("public/events/", views.PublicList.as_view()),
    path("public/events/<slug:slug>/", views.PublicDetail.as_view()),
    path("public/events/<slug:slug>/banner/", views.PublicBanner.as_view()),
    path("notifications/", views.NotificationList.as_view()),
    path("notifications/<uuid:pk>/read/", views.NotificationRead.as_view()),
]
