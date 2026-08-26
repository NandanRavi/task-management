# Task Management System

A robust, scalable Task Management Backend built with **Django**, **Django REST Framework (DRF)**, **Django Channels (WebSockets)**, and **Django-Q**.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Features](#features)
- [Database Models](#database-models)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Endpoints Summary](#api-endpoints-summary)
- [WebSocket Support](#websocket-support)
- [Asynchronous Background Tasks](#asynchronous-background-tasks)

---

## 🚀 Overview

The Task Management System enables teams to organize projects and tasks with granular permission controls between **Admin** and **Client** users. It supports real-time task updates via WebSockets and automated background notifications via Django-Q.

---

## 🛠 Architecture & Tech Stack

- **Backend Framework**: Django 6.0 + Django REST Framework (DRF)
- **Authentication**: JWT (JSON Web Tokens via `djangorestframework-simplejwt`)
- **Real-Time Communication**: Django Channels + WebSockets (ASGI with Daphne/Channel Layer)
- **Background Tasks & Scheduling**: Django-Q
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Unique Identifiers**: UUIDv4 primary keys for all models

---

## ✨ Features

- **JWT Authentication**: User registration, login with token generation, and secure token blacklisting on logout.
- **Hierarchical Access Control**:
  - Admins can manage all projects and tasks.
  - Clients are limited to their assigned projects and tasks.
- **Unified Endpoints**: Streamlined RESTful views handling list, retrieve, create, partial update (PATCH), and delete operations.
- **Real-Time Task Collaboration**: Live WebSocket broadcasting of task changes to all participants of a project.
- **Background Automation**: Overdue task checks, email alerts, welcome emails, and daily report generation.

---

## 🗄 Database Models

### 1. `CustomUser`

- `id` (UUID, Primary Key)
- `email` (EmailField, Unique)
- `full_name` (CharField)
- `user_type` (`admin` | `client`)
- `is_staff`, `is_active` (BooleanField)
- `created_at`, `updated_at` (DateTimeField)

### 2. `Projects`

- `id` (UUID, Primary Key)
- `user` (ForeignKey -> CustomUser, Project Owner)
- `name` (CharField)
- `description` (TextField)
- `start_date`, `end_date` (DateField)
- `status` (BooleanField, default=True)
- `created_at`, `updated_at` (DateTimeField)

### 3. `Task`

- `id` (UUID, Primary Key)
- `project` (ForeignKey -> Projects)
- `title` (CharField)
- `description` (TextField)
- `due_date` (DateField)
- `assigned_to` (ForeignKey -> CustomUser)
- `status` (BooleanField, default=True)
- `created_at`, `updated_at` (DateTimeField)

---

## 🔐 Role-Based Access Control (RBAC)

| Resource     | Action          | Superuser | Admin |              Client               |
| :----------- | :-------------- | :-------: | :---: | :-------------------------------: |
| **Auth**     | Register Admin  |    ✅     |  ❌   |                ❌                 |
| **Auth**     | Register Client |    ✅     |  ✅   |    ✅ (Unauthenticated / Self)    |
| **Projects** | View List       |    All    |  All  |      Owned or Assigned Tasks      |
| **Projects** | Create          |    ✅     |  ✅   |                ❌                 |
| **Projects** | Retrieve Detail |    ✅     |  ✅   |      Owned or Assigned Tasks      |
| **Projects** | Update (PATCH)  |    ✅     |  ✅   |                ❌                 |
| **Projects** | Delete          |    ✅     |  ✅   |                ❌                 |
| **Tasks**    | View List       |    All    |  All  | Assigned to user or owned project |
| **Tasks**    | Create          |    ✅     |  ✅   |                ❌                 |
| **Tasks**    | Retrieve Detail |    ✅     |  ✅   | Assigned to user or owned project |
| **Tasks**    | Update (PATCH)  |    ✅     |  ✅   |        Assigned user only         |
| **Tasks**    | Delete          |    ✅     |  ❌   |        Project owner only         |
| **Users**    | View List       |    All    |  All  |               All                 |

---

## ⚙ Installation & Setup

### Prerequisites

- Python 3.10+
- Virtual Environment tool (`venv`)

### Setup Instructions

1. **Clone or Navigate to the project directory**:

   ```bash
   cd task_management
   ```

2. **Create and Activate Virtual Environment**:

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser (Optional)**:
   ```bash
   python manage.py createsuperuser
   ```

---

## 🔑 Environment Variables (`.env`)

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=*
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com
```

---

## 🏃 Running the Application

### 1. Development Server (HTTP + WebSockets)

```bash
python manage.py runserver 8000
```

### 2. Django-Q Background Worker

```bash
python manage.py qcluster
```

---

## 📡 API Endpoints Summary

Base URL: `http://localhost:8000/api/`

### 1. Authentication

- `POST /api/auth/register/` - Register user (`email`, `password`, `full_name`, `user_type`)
- `POST /api/auth/login/` - Login & obtain JWT access + refresh tokens
- `POST /api/auth/logout/` - Blacklist refresh token

### 2. Projects (`ProjectView`)

- `GET /api/projects/` - List projects (Supports `?status=true/false` and `?search=term`)
- `POST /api/projects/` - Create project (Admin only)
- `GET /api/projects/<uuid:pk>/` - Get project details
- `PATCH /api/projects/<uuid:pk>/` - Update project (Admin only)
- `DELETE /api/projects/<uuid:pk>/` - Delete project (Admin only)

### 3. Tasks (`TaskView`)

- `GET /api/tasks/` - List tasks (Supports `?project=<id>`, `?assigned_to=<id>`, `?status=true/false`, `?search=term`, `?ordering=field`)
- `POST /api/tasks/` - Create task (Admin only)
- `GET /api/tasks/<uuid:pk>/` - Get task details
- `PATCH /api/tasks/<uuid:pk>/` - Update task (Admin or Assigned User)
- `DELETE /api/tasks/<uuid:pk>/` - Delete task (Project Owner or Superuser)

### 4. Users (`UserListView`)

- `GET /api/users/` - List all users (Supports `?user_type=admin` or `?user_type=client`)

---

## 🔌 WebSocket Support

- **WebSocket URL**: `ws://localhost:8000/ws/tasks/<project_id>/`
- Connects client to real-time project updates.
- Broadcast payload example:
  ```json
  {
    "type": "task_update",
    "task": {
      "id": "c7a6e11c-d7ab-4958-86d1-cf19a3b68f9a",
      "title": "Design Database Schema",
      "status": true
    }
  }
  ```

---

## ⏱ Asynchronous Background Tasks

Implemented via Django-Q in `app1/tasks.py`:

- `send_task_reminder(task_id)`: Automated email when a task is overdue.
- `check_overdue_tasks()`: Scheduled periodic scan for overdue uncompleted tasks.
- `send_welcome_email(user_id)`: Welcome email upon successful registration.
- `generate_daily_report(user_id)`: Generates daily summary of user projects & task progress.
