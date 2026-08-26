from rest_framework import serializers
from .models import CustomUser, Projects, Task


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "full_name",
            "user_type",
        )
        read_only_fields = (
            "id",
            "created_at",
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "full_name",
            "password",
            "user_type",
        )
        read_only_fields = ("id",)


class ProjectSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True
    )
    user_name = serializers.CharField(
        source="user.full_name",
        read_only=True
    )

    class Meta:
        model = Projects
        fields = (
            "id",
            "user",
            "user_email",
            "user_name",
            "name",
            "description",
            "start_date",
            "end_date",
            "status",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(
        source="project.name",
        read_only=True
    )
    assigned_to_email = serializers.EmailField(
        source="assigned_to.email",
        read_only=True
    )
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name",
        read_only=True
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "due_date",
            "assigned_to",
            "assigned_to_email",
            "assigned_to_name",
            "status",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )
