from django.contrib.auth import get_user_model

User = get_user_model()


def update_user_fields(user, validated_data, skip_fields=None):
    """
    Safely update a user with validated data.

    skip_fields: list of fields to skip (e.g., password, role, tenant)
    """
    skip_fields = skip_fields or []
    for field, value in validated_data.items():
        if field not in skip_fields:
            setattr(user, field, value)
