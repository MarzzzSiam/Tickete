from rest_framework import serializers

from apps.accounts.serializers import StrictSerializer

from .models import Event, EventFormField, TicketCategory


class CategoryInput(StrictSerializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    seat_limit = serializers.IntegerField(min_value=1, allow_null=True, default=None)
    is_active = serializers.BooleanField(default=True)

    def validate(self, data):
        for field in ("name", "price"):
            if field not in data:
                raise serializers.ValidationError({field: "Required in each category."})
        data.setdefault("seat_limit", None)
        data.setdefault("is_active", True)
        return data


class FieldInput(StrictSerializer):
    id = serializers.UUIDField(required=False)
    label = serializers.CharField(max_length=150)
    type = serializers.ChoiceField(choices=EventFormField.Type.choices)
    required = serializers.BooleanField(default=False)
    options = serializers.ListField(
        child=serializers.CharField(max_length=150), max_length=50, default=list
    )
    sort_order = serializers.IntegerField(min_value=0, default=0)

    def validate(self, data):
        for field in ("label", "type"):
            if field not in data:
                raise serializers.ValidationError({field: "Required in each field."})
        options = data.setdefault("options", [])
        data.setdefault("required", False)
        data.setdefault("sort_order", 0)
        if data["type"] == "dropdown" and (not options or len(set(options)) != len(options)):
            raise serializers.ValidationError(
                {"options": "Dropdown options must be nonempty and unique."}
            )
        if data["type"] != "dropdown" and options:
            raise serializers.ValidationError(
                {"options": "Only dropdown fields can define options."}
            )
        return data


class DraftInput(StrictSerializer):
    title = serializers.CharField(max_length=180)
    description = serializers.CharField(max_length=20000, allow_blank=True, required=False)
    venue = serializers.CharField(max_length=300, allow_blank=True, required=False)
    starts_at = serializers.DateTimeField(allow_null=True, required=False)
    ends_at = serializers.DateTimeField(allow_null=True, required=False)
    sales_start = serializers.DateTimeField(allow_null=True, required=False)
    sales_end = serializers.DateTimeField(allow_null=True, required=False)
    max_per_order = serializers.IntegerField(min_value=1, max_value=1000, required=False)
    collect_attendee_names = serializers.BooleanField(required=False)
    categories = CategoryInput(many=True, required=False, max_length=50)
    form_fields = FieldInput(many=True, required=False, max_length=50)


class CategoryOutput(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = ["id", "name", "price", "seat_limit", "sold_count", "is_active"]


class FieldOutput(serializers.ModelSerializer):
    class Meta:
        model = EventFormField
        fields = ["id", "label", "type", "required", "options", "sort_order"]


class PublicEventSerializer(serializers.ModelSerializer):
    categories = CategoryOutput(many=True)
    form_fields = FieldOutput(many=True)
    has_banner = serializers.SerializerMethodField()

    def get_has_banner(self, obj) -> bool:
        return bool(obj.banner_key)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "venue",
            "has_banner",
            "starts_at",
            "ends_at",
            "sales_start",
            "sales_end",
            "max_per_order",
            "collect_attendee_names",
            "categories",
            "form_fields",
        ]


class EventSerializer(PublicEventSerializer):
    class Meta(PublicEventSerializer.Meta):
        fields = PublicEventSerializer.Meta.fields + [
            "status",
            "rejection_reason",
            "reviewed_at",
            "updated_at",
        ]


class ReviewInput(StrictSerializer):
    reason = serializers.CharField(max_length=2000)


class BannerInput(StrictSerializer):
    banner = serializers.FileField()
