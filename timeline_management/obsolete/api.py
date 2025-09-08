from __future__ import annotations

import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import SessionStorageItem, Timeline

try:
	import firebase_admin
	from firebase_admin import credentials, firestore
except Exception as e:  # pragma: no cover - dependency not yet installed
	firebase_admin = None  # type: ignore
	credentials = None  # type: ignore
	firestore = None  # type: ignore


try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	pass


app = FastAPI(title="Timeline Management API", version="0.2.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


def init_firebase():
	"""Initialize Firebase Admin SDK using a service account.

	Looks for either:
	- FIREBASE_SERVICE_ACCOUNT_BASE64: base64-encoded JSON
	- GOOGLE_APPLICATION_CREDENTIALS: path to JSON file
	- FIREBASE_SERVICE_ACCOUNT_FILE: alternative path variable
	"""
	if firebase_admin is None:
		return None

	if not firebase_admin._apps:
		sa_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
		sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
			"FIREBASE_SERVICE_ACCOUNT_FILE"
		)

		cred = None
		if sa_b64:
			import base64
			import json

			try:
				data = base64.b64decode(sa_b64)
				cred_info = json.loads(data)
				cred = credentials.Certificate(cred_info)
			except Exception as e:  # noqa: F841
				raise RuntimeError("Invalid FIREBASE_SERVICE_ACCOUNT_BASE64")
		elif sa_path and os.path.exists(sa_path):
			cred = credentials.Certificate(sa_path)
		else:
			# Fall back to default creds if available
			cred = credentials.ApplicationDefault()

		firebase_admin.initialize_app(cred)

	return firestore.client()  # type: ignore


def sessions_collection():
	db = init_firebase()
	if db is None:
		raise HTTPException(status_code=500, detail="Firebase not initialized. Install dependencies and set service account.")
	return db.collection("sessions")


def timelines_collection():
	db = init_firebase()
	if db is None:
		raise HTTPException(status_code=500, detail="Firebase not initialized. Install dependencies and set service account.")
	return db.collection("timelines")


@app.get("/health")
def health() -> dict:
	return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/sessions", response_model=SessionStorageItem)
def create_session(item: SessionStorageItem) -> SessionStorageItem:
	if not item.sessionId:
		# use Firestore auto-id if not provided
		doc_ref = sessions_collection().document()
		item.sessionId = doc_ref.id
	else:
		doc_ref = sessions_collection().document(item.sessionId)

	now = datetime.utcnow()
	item.createdAt = item.createdAt or now
	item.lastUpdatedAt = now
	doc_ref.set(item.model_dump())
	return item


@app.get("/sessions/{session_id}", response_model=SessionStorageItem)
def get_session(session_id: str) -> SessionStorageItem:
	doc = sessions_collection().document(session_id).get()
	if not doc.exists:
		raise HTTPException(status_code=404, detail="Session not found")
	data = doc.to_dict() or {}
	return SessionStorageItem.model_validate(data)


@app.get("/sessions", response_model=List[SessionStorageItem])
def list_sessions(limit: int = 50) -> List[SessionStorageItem]:
	docs = sessions_collection().limit(limit).get()
	return [SessionStorageItem.model_validate(d.to_dict()) for d in docs]


@app.put("/sessions/{session_id}", response_model=SessionStorageItem)
def update_session(session_id: str, item: SessionStorageItem) -> SessionStorageItem:
	doc_ref = sessions_collection().document(session_id)
	if not doc_ref.get().exists:
		raise HTTPException(status_code=404, detail="Session not found")
	item.sessionId = session_id
	item.lastUpdatedAt = datetime.utcnow()
	doc_ref.set(item.model_dump(), merge=True)
	return item


@app.patch("/sessions/{session_id}", response_model=SessionStorageItem)
def patch_session(session_id: str, partial: dict) -> SessionStorageItem:
	doc_ref = sessions_collection().document(session_id)
	snap = doc_ref.get()
	if not snap.exists:
		raise HTTPException(status_code=404, detail="Session not found")
	doc_ref.set({**partial, "lastUpdatedAt": datetime.utcnow()}, merge=True)
	data = doc_ref.get().to_dict() or {}
	return SessionStorageItem.model_validate(data)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict:
	doc_ref = sessions_collection().document(session_id)
	if not doc_ref.get().exists:
		raise HTTPException(status_code=404, detail="Session not found")
	doc_ref.delete()
	return {"deleted": True, "sessionId": session_id}


# Timeline CRUD
@app.post("/timelines", response_model=Timeline)
def create_timeline(item: Timeline) -> Timeline:
	if not item.timelineId:
		doc_ref = timelines_collection().document()
		item.timelineId = doc_ref.id
	else:
		doc_ref = timelines_collection().document(item.timelineId)
	item.lastUpdatedAt = datetime.utcnow()
	doc_ref.set(item.model_dump())
	return item


@app.get("/timelines/{timeline_id}", response_model=Timeline)
def get_timeline(timeline_id: str) -> Timeline:
	snap = timelines_collection().document(timeline_id).get()
	if not snap.exists:
		raise HTTPException(status_code=404, detail="Timeline not found")
	return Timeline.model_validate(snap.to_dict() or {})


@app.get("/timelines", response_model=List[Timeline])
def list_timelines(userId: Optional[str] = None, limit: int = 50) -> List[Timeline]:
	col = timelines_collection()
	if userId:
		q = col.where("userId", "==", userId).limit(limit)
		docs = q.get()
	else:
		docs = col.limit(limit).get()
	return [Timeline.model_validate(d.to_dict()) for d in docs]


@app.put("/timelines/{timeline_id}", response_model=Timeline)
def update_timeline(timeline_id: str, item: Timeline) -> Timeline:
	doc_ref = timelines_collection().document(timeline_id)
	if not doc_ref.get().exists:
		raise HTTPException(status_code=404, detail="Timeline not found")
	item.timelineId = timeline_id
	item.lastUpdatedAt = datetime.utcnow()
	doc_ref.set(item.model_dump(), merge=True)
	return item


@app.patch("/timelines/{timeline_id}", response_model=Timeline)
def patch_timeline(timeline_id: str, partial: dict) -> Timeline:
	doc_ref = timelines_collection().document(timeline_id)
	if not doc_ref.get().exists:
		raise HTTPException(status_code=404, detail="Timeline not found")
	doc_ref.set({**partial, "lastUpdatedAt": datetime.utcnow()}, merge=True)
	data = doc_ref.get().to_dict() or {}
	return Timeline.model_validate(data)


@app.delete("/timelines/{timeline_id}")
def delete_timeline(timeline_id: str) -> dict:
	doc_ref = timelines_collection().document(timeline_id)
	if not doc_ref.get().exists:
		raise HTTPException(status_code=404, detail="Timeline not found")
	doc_ref.delete()
	return {"deleted": True, "timelineId": timeline_id}


# Optional: Uvicorn entrypoint
if __name__ == "__main__":
	import uvicorn

	uvicorn.run("timeline_management.api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

