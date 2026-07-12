# AI Student Assistant System

A Django-based intelligent academic support platform for university students.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create the PostgreSQL database first, then run:

```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## PostgreSQL database setup

The project uses the proposal database stack: PostgreSQL, Django ORM, and the `psycopg` PostgreSQL adapter.

Create a PostgreSQL database named `ai_student_assistant` in pgAdmin or psql. You can run the SQL in `database_setup.sql`:

```sql
CREATE DATABASE ai_student_assistant;
```

Then set these environment variables before running migrations:

```powershell
$env:POSTGRES_DB="ai_student_assistant"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="your_password"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
python manage.py migrate
```

If you keep the default values, only `POSTGRES_PASSWORD` usually needs to be changed for your local PostgreSQL installation.

User Management database module:

- `auth_user`: login credentials, email, password hash, first name, last name
- `core_studentprofile`: registration/profile details, university, department, semester, skills, learning goals, career goal, photo
- `core_useractivity`: registration, login, logout, and profile update activity records
