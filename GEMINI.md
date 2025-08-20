# GEMINI Project Analysis

## Project Overview

This is a full-stack web application built with a separated frontend and backend architecture.

*   **Frontend:** The frontend is a single-page application (SPA) built with [Vue.js](https://vuejs.org/) 3, using [Vite](https://vitejs.dev/) for the build tooling. It uses [Vue Router](https://router.vuejs.org/) for client-side routing and [Pinia](https://pinia.vuejs.org/) for state management. The frontend is written in [TypeScript](https://www.typescriptlang.org/).

*   **Backend:** The backend is a RESTful API built with the [FastAPI](https://fastapi.tiangolo.com/) framework in Python. It uses [SQLAlchemy](https://www.sqlalchemy.org/) as an ORM to interact with the database. The API provides endpoints for managing users and items.

*   **Database:** The application uses a [PostgreSQL](https://www.postgresql.org/) database to store data.

*   **Containerization:** The entire application is containerized using [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/), which allows for easy setup and deployment.

## Building and Running

There are three ways to run this project:

### 1. Docker Mode (Recommended)

This is the easiest way to get the application running.

```bash
docker-compose up -d
```

This will start the frontend, backend, and database services in detached mode.

*   **Frontend:** [http://localhost:5173](http://localhost:5173)
*   **Backend API:** [http://localhost:8000](http://localhost:8000)
*   **PostgreSQL:** `localhost:5432`

### 2. Debug Mode (for development)

The project is configured to be easily debugged in Visual Studio Code.

1.  Open the project in VS Code.
2.  Press **F5** to start debugging.
3.  Select the "Python: FastAPI Debug" launch configuration.

For more details, see the `DEBUG_GUIDE.md` file.

### 3. Manual Mode

You can also run the frontend and backend services manually.

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Development Conventions

*   **Backend:**
    *   The backend code is located in the `backend/app` directory.
    *   Dependencies are managed with `uv` and are listed in `backend/pyproject.toml`.
    *   The main application entry point is `backend/app/main.py`.
    *   API routes are defined in the `backend/app/routers` directory.
    *   Database models are defined in `backend/app/models.py`.
    *   Data validation is handled using Pydantic schemas in `backend/app/schemas.py`.

*   **Frontend:**
    *   The frontend code is located in the `frontend/src` directory.
    *   Dependencies are managed with `npm` and are listed in `frontend/package.json`.
    *   The main application entry point is `frontend/src/main.ts`.
    *   Views are defined in the `frontend/src/views` directory.
    *   Routing is configured in `frontend/src/router/index.ts`.
    *   API requests are handled by the `frontend/src/services/api.ts` service.
