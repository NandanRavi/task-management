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



class ProjectView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk, user):
        try:
            if is_admin_user(user):
                return Projects.objects.get(pk=pk)

            return Projects.objects.filter(
                Q(user=user) |
                Q(tasks__assigned_to=user)
            ).distinct().get(pk=pk)

        except Projects.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            project = self.get_object(pk, request.user)

            if not project:
                return Response(
                    {"error": "Project not found."},status=status.HTTP_404_NOT_FOUND)

            serializer = ProjectSerializer(project)

            return Response({"success": True,"message": "Project fetched successfully","data": serializer.data},status=status.HTTP_200_OK)

        status_param = request.query_params.get("status")
        search = request.query_params.get("search")

        current_page = request.query_params.get("current_page")
        limit = request.query_params.get("limit")

        if is_admin_user(request.user):
            projects = Projects.objects.all()

            if status_param and status_param.lower() != "all":

                if status_param.lower() == "true":
                    projects = projects.filter(status=True)

                elif status_param.lower() == "false":
                    projects = projects.filter(status=False)

        else:
            projects = Projects.objects.filter(
                Q(user=request.user) |
                Q(tasks__assigned_to=request.user)
            ).distinct()
            if status_param and status_param.lower() != "all":

                if status_param.lower() == "true":
                    projects = projects.filter(status=True)

                elif status_param.lower() == "false":
                    projects = projects.filter(status=False)
            projects = projects.annotate(
                latest_task_created_at=Max("tasks__created_at")
            ).order_by(
                "-latest_task_created_at",
                "-created_at"
            )
        if search:
            projects = projects.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        if is_admin_user(request.user):
            projects = projects.order_by("-created_at")

        total_items = projects.count()

        if current_page and limit:
            try:
                page = int(current_page)
                page_size = int(limit)

                if page < 1 or page_size < 1:
                    raise ValueError

                total_pages = (total_items + page_size - 1) // page_size

                start = (page - 1) * page_size
                end = start + page_size
                has_next = page < total_pages
                projects = projects[start:end]
                serializer = ProjectSerializer(projects,many=True)
                return Response(
                    {
                        "success": True,
                        "message": "Projects fetched successfully",
                        "data": serializer.data,
                        "current_page": page,
                        "limit": page_size,
                        "total_pages": total_pages,
                        "total_items": total_items,
                        "has_next": has_next
                    },
                    status=status.HTTP_200_OK
                )

            except (ValueError, TypeError):
                pass
        serializer = ProjectSerializer(projects,many=True)
        return Response(
            {
                "success": True,
                "message": "Projects fetched successfully",
                "data": serializer.data,
                "total_items": total_items
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        if not is_admin_user(request.user):
            return Response({"error": "Only admin users can create projects."},status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()

        if not data.get("user"):
            data["user"] = request.user.id
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            project = serializer.save()
            data = {
                "success": True,
                "message": "Project created successfully",
                "data": serializer.data
            }
            return Response(data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        if not pk:
            return Response({"error": "Project ID is required for update."},status=status.HTTP_400_BAD_REQUEST)
        if not is_admin_user(request.user):
            return Response({'error': 'Only admin users can update projects.'},status=status.HTTP_403_FORBIDDEN)
        try:
            project = Projects.objects.get(pk=pk)
        except Projects.DoesNotExist:
            return Response({"error": "Project not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            data = {
                "success": True,
                "message": "Project updated successfully",
                "data": serializer.data
            }
            return Response(data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if not pk:
            return Response({"error": "Project ID is required for deletion."},status=status.HTTP_400_BAD_REQUEST)

        if not is_admin_user(request.user):
            return Response({'error': 'Only admin users can delete projects.'},status=status.HTTP_403_FORBIDDEN)

        try:
            project = Projects.objects.get(pk=pk)
        except Projects.DoesNotExist:
            return Response({"error": "Project not found."},status=status.HTTP_404_NOT_FOUND)

        project.delete()
        return Response(status=status.HTTP_200_OK)


class TaskView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk, user):
        try:
            if is_admin_user(user):
                return Task.objects.get(pk=pk)
            return Task.objects.filter(
                Q(assigned_to=user) | Q(project__user=user)
            ).distinct().get(pk=pk)
        except Task.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk is not None:
            task = self.get_object(pk, request.user)
            if not task:
                return Response({"error": "Task not found."},status=status.HTTP_404_NOT_FOUND)
            serializer = TaskSerializer(task)
            data = {
                "success": True,
                "message": "Task fetched successfully",
                "data": serializer.data
            }
            return Response(data,status=status.HTTP_200_OK)

        if is_admin_user(request.user):
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(
                Q(assigned_to=request.user) | Q(project__user=request.user)
            ).distinct()

        project_id = request.query_params.get('project')
        if project_id:
            tasks = tasks.filter(project__id=project_id)

        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            tasks = tasks.filter(assigned_to__id=assigned_to)

        status_param = request.query_params.get('status')
        if status_param is not None:
            if status_param.lower() == 'true':
                tasks = tasks.filter(status=True)
            elif status_param.lower() == 'false':
                tasks = tasks.filter(status=False)

        search = request.query_params.get('search')
        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        ordering = request.query_params.get('ordering', '-created_at')
        tasks = tasks.order_by(ordering)

        serializer = TaskSerializer(tasks, many=True)
        data = {
            "success": True,
            "message": "Tasks fetched successfully",
            "data": serializer.data
        }
        return Response(data,status=status.HTTP_200_OK)

    def post(self, request):
        if not is_admin_user(request.user):
            return Response({"error": "Only admin users can create tasks."},status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save()
        data = {
            "success": True,
            "message": "Task created successfully",
            "data": TaskSerializer(task).data
        }

        return Response(data,status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None):
        if not pk:
            return Response({"error": "Task ID is required for update."},status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."},status=status.HTTP_404_NOT_FOUND)

        if task.assigned_to != request.user and not is_admin_user(request.user):
            return Response({'error': 'You do not have permission to update this task. Only the assigned user or an admin can update it.'},status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            data = {
                "success": True,
                "message": "Task updated successfully",
                "data": TaskSerializer(task).data
            }
            return Response(data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if not pk:
            return Response({"error": "Task ID is required for deletion."},status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."},status=status.HTTP_404_NOT_FOUND)

        if task.project.user != request.user and not request.user.is_superuser:
            return Response({'error': 'Only the project owner (project.user) can delete this task.'},status=status.HTTP_403_FORBIDDEN)

        task.delete()
        return Response(status=status.HTTP_200_OK)


class UserListView(APIView):
    def get(self, request):
        user_type = request.query_params.get("user_type")
        if user_type:
            if user_type not in ["admin", "client"]:
                return Response({"success": True,"message": "No users found","data": []},status=status.HTTP_200_OK)
            users = CustomUser.objects.filter(user_type=user_type)
        else:
            users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({"success": True,"message": "Users fetched successfully","data": serializer.data},status=status.HTTP_200_OK)