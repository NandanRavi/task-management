from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Q, Max
from django.contrib.auth import authenticate


from .serializers import (
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    ProjectSerializer,
    TaskSerializer
)
from .models import CustomUser, Projects, Task
from .utils import is_admin_user, generate_tokens_for_user, validate_user_password, create_user


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request,email=email,password=password)

        if not user:
            try:
                user = CustomUser.objects.get(email=email)

                if not user.check_password(password):
                    user = None

            except CustomUser.DoesNotExist:
                user = None

        if not user:
            return Response({"error": "Invalid email or password."},status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"error": "User account is disabled."},status=status.HTTP_400_BAD_REQUEST)

        access_token, refresh_token = generate_tokens_for_user(user)

        return Response(
            {
                "success": True,
                "message": "User login successfully",
                "data": {
                    "user": UserSerializer(user).data,
                    "access_token": str(access_token),
                    "refresh_token": str(refresh_token),
                    "is_superadmin": user.is_superuser,
                },
            },
            status=status.HTTP_200_OK
        )


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        data = request.data.copy()

        target_user_type = data.get("user_type", "client")

        if target_user_type not in ["admin", "client"]:
            return Response({"error": "Invalid user_type. Allowed values are 'admin' or 'client'."},status=status.HTTP_400_BAD_REQUEST)

        data["user_type"] = target_user_type

        password = data.get("password")

        try:
            validate_user_password(password)
        except Exception as exc:
            return Response({"password": list(exc.messages)},status=status.HTTP_400_BAD_REQUEST)

        serializer = UserRegistrationSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        user = create_user(serializer.validated_data)

        return Response({"message": "User registered successfully.","user": UserSerializer(user).data},status=status.HTTP_201_CREATED)

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required in the 'refresh' field."},status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"error": "Successfully logged out."}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


