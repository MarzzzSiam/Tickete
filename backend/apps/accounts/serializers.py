from rest_framework import serializers

from .models import User


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: ["Unknown field."] for key in unknown})
        return super().to_internal_value(data)


class EmailSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class LoginSerializer(EmailSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class RegisterSerializer(LoginSerializer):
    full_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=["buyer", "organizer"], default="buyer")


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "role", "email_verified"]
        read_only_fields = fields


class ProfileUpdateSerializer(StrictSerializer):
    full_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=30, allow_blank=True, required=False)


class ConfirmSerializer(StrictSerializer):
    challenge_id = serializers.UUIDField()
    token = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class ResetConfirmSerializer(ConfirmSerializer):
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class ChangePasswordSerializer(StrictSerializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()
