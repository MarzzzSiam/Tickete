from .views import EventDetail


class EventPreview(EventDetail):
    http_method_names = ["get", "head", "options"]
