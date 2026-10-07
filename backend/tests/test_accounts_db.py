import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User


@pytest.mark.django_db
def test_email_identity_and_password_hashing():
    user = User.objects.create_user(" Buyer@Example.com ", "Long-example-password-713")
    assert user.email == "buyer@example.com"
    assert user.check_password("Long-example-password-713")
    assert not user.email_verified
    assert user.role == "buyer"


@pytest.mark.django_db
def test_database_enforces_case_insensitive_unique_email():
    User.objects.create_user("buyer@example.com")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(email="BUYER@example.com", password="!")])
