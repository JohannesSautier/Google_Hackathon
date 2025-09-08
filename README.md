# Google_Hackathon

## Timeline Management API (FastAPI + Firebase)

This project includes a FastAPI server that stores and retrieves session documents in Firebase Firestore using a service account.

### Setup

1) Create a Python virtual environment and install dependencies

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
```

2) Provide Firebase service account credentials via one of the following (values can be placed in a `.env` file at the repo root or set in the shell):

- Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your JSON file

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
```

- OR set `FIREBASE_SERVICE_ACCOUNT_FILE` to the path of your JSON file

```powershell
$env:FIREBASE_SERVICE_ACCOUNT_FILE = "C:\path\to\service-account.json"
```

- OR set `FIREBASE_SERVICE_ACCOUNT_BASE64` to a base64-encoded JSON string of the service account

```powershell
$json = Get-Content "C:\path\to\service-account.json" -Raw
$env:FIREBASE_SERVICE_ACCOUNT_BASE64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
```

### Run the API

```powershell
uvicorn timeline_management.api:app --host 0.0.0.0 --port 8000 --reload
```

Then open http://localhost:8000/docs for the Swagger UI.

### Endpoints

- `GET /health` – health check
- `POST /sessions` – create a session (auto-id if `sessionId` missing)
- `GET /sessions/{session_id}` – get one session
- `GET /sessions?limit=50` – list sessions
- `PUT /sessions/{session_id}` – upsert full session
- `PATCH /sessions/{session_id}` – partial update
- `DELETE /sessions/{session_id}` – delete session

- `POST /timelines` – create a timeline (auto-id if `timelineId` missing)
- `GET /timelines/{timeline_id}` – get timeline
- `GET /timelines?userId=...` – list timelines (optionally filter by user)
- `PUT /timelines/{timeline_id}` – upsert full timeline
- `PATCH /timelines/{timeline_id}` – partial update
- `DELETE /timelines/{timeline_id}` – delete timeline

### Data model

See `timeline_management/models.py`. It's a Pydantic translation of the provided C# classes.
