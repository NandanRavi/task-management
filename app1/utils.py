from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


def is_admin_user(user):
    return user.is_authenticated and (user.user_type == "admin" or user.is_staff or user.is_superuser)


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return refresh.access_token, refresh


def create_user(validated_data):
    password = validated_data.pop("password")
    user = CustomUser(**validated_data)
    user.set_password(password)
    user.save()
    return user

def validate_user_password(password):
    validate_password(password)
    return password