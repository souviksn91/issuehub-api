# IssueHub API
IssueHub is an Issue Tracking System built with Django REST Framework and PostgreSQL. This project focuses on backend engineering best practices without a frontend. 

**What This API Does:**
IssueHub enables authenticated users to create and manage issues within a collaborative environment.
A user who creates an issue becomes its reporter, while another user can be assigned as the assignee responsible for progressing it.
The assignee controls status updates (open, in_progress, resolved), while the reporter manages assignment and archival.
Users can collaborate through comments, with strict permission rules ensuring controlled and accountable workflows.

**It demonstrates:**
- Clean RESTful API design
- JWT authentication
- Custom object-level permissions
- Nested routing
- Advanced filtering (status, priority, assignee, reporter)
- Search & ordering
- Per-view pagination
- Throttling (rate limiting)
- Production-aware architecture decisions

## Tech Stack
- Python
- Django
- Django REST Framework
- PostgreSQL
- SimpleJWT (JWT authentication)
- drf-spectacular (Swagger documentation)

## Core Features

**User System:** 
- User registration with password confirmation
- Unique username and email validation
- Read-only user listing (excluding superusers)
- JWT authentication
- Rate-limited registration endpoint

**Issue Management:** 
- UUID primary key
- Title & description
- Reporter (auto-set)
- Single assignee
- Status (open, in_progress, and resolved)
- Priority (low, medium, high)
- Archive (soft freeze)
- Created & updated timestamps
- Only reporter can edit or assign
- Only assignee can change status
- Status cannot change without assignee
- Archived issues are read-only

**Comment System:** 
- Nested under issues
- Only comment author can edit/delete
- Comments blocked if issue is archived
- Paginated separately

**Advanced Query Support:** 
- Filtering
- Search
- Ordering

**Pagination**
- custom paginations

**Throttling**
- Scoped Throttling
- Anonymous: 20 requests/min
- Authenticated users: 100 requests/min
- Registration endpoint: 5 requests/min


## Setup Instructions

1. **Clone the repository:**
   ```bash
    git clone <repo>
    cd issuehub-api
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
   ```

2. **Create .env:**
    ```ini
    SECRET_KEY=your_secret_key
    DEBUG=True
    DB_NAME=issuehub_db
    DB_USER=youruser
    DB_PASSWORD=yourpassword
    DB_HOST=localhost
    DB_PORT=5432
    ```

3. **Run:**
   ```bash
    python manage.py migrate
    python manage.py runserver
   ```

4. **Swagger available at:**
    ```ini
    /api/docs/
    ```


Author: **Souvik Sinha**