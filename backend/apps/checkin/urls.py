from django.urls import path

from apps.events.reporting import CloseEvent, Dashboard, FinalReport

from . import views

urlpatterns = [
    path("events/<uuid:pk>/dashboard/", Dashboard.as_view()),
    path("events/<uuid:pk>/report/", FinalReport.as_view()),
    path("events/<uuid:pk>/close/", CloseEvent.as_view()),
    path("team/events/", views.TeamEvents.as_view()),
    path("team/accept/", views.AcceptInvitation.as_view()),
    path("events/<uuid:pk>/operations/", views.Summary.as_view()),
    path("events/<uuid:pk>/attendees/", views.Attendees.as_view()),
    path("events/<uuid:pk>/team/", views.Team.as_view()),
    path("events/<uuid:pk>/team/<uuid:member_id>/", views.Member.as_view()),
    path(
        "events/<uuid:pk>/invitations/<uuid:invitation_id>/revoke/",
        views.RevokeInvitation.as_view(),
    ),
    path("events/<uuid:pk>/scan/", views.Scan.as_view()),
    path("events/<uuid:pk>/tickets/<uuid:ticket_id>/cancel/", views.CancelTicket.as_view()),
]
