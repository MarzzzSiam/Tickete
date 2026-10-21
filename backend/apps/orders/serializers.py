from rest_framework import serializers

from apps.accounts.serializers import StrictSerializer


class SelectionInput(StrictSerializer):
    category_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000)
    attendee_names = serializers.ListField(
        child=serializers.CharField(max_length=150, allow_blank=True),
        max_length=1000,
        required=False,
        default=list,
    )


class CheckoutInput(StrictSerializer):
    event_id = serializers.UUIDField()
    buyer_email = serializers.EmailField()
    is_gift = serializers.BooleanField(default=False)
    recipient_email = serializers.EmailField(required=False)
    selections = SelectionInput(many=True, allow_empty=False)
    answers = serializers.DictField(required=False, default=dict)
    idempotency_key = serializers.UUIDField()
    access_token = serializers.RegexField(r"^[A-Za-z0-9_-]{43,128}$", write_only=True)

    def validate_selections(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Choose at most 50 categories.")
        if len({row["category_id"] for row in value}) != len(value):
            raise serializers.ValidationError("Each category may appear only once.")
        return value


class PaymentInput(StrictSerializer):
    provider = serializers.ChoiceField(choices=["dummy_bkash", "dummy_nagad"])
    phone = serializers.RegexField(r"^01[3-9][0-9]{8}$")


class VerifyInput(StrictSerializer):
    otp = serializers.RegexField(r"^[0-9]{6}$")


class CheckoutResult(serializers.Serializer):
    id = serializers.UUIDField()
    number = serializers.CharField()
    status = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    quantity = serializers.IntegerField()
    expires_at = serializers.DateTimeField()
    server_time = serializers.DateTimeField()
    recipient_email = serializers.EmailField()
    is_gift = serializers.BooleanField()
    snapshot = serializers.JSONField()
    payment = serializers.JSONField(allow_null=True)
    tickets = serializers.JSONField()
    delivery_status = serializers.CharField()
    pdf_ready = serializers.BooleanField()
