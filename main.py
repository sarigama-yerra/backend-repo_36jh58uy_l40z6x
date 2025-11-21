import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database import db, create_document, get_documents
from schemas import User, TestResult, Professional, Session, Message, Plan

app = FastAPI(title="Wisp API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Wisp backend is live"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Helper response models
class CreateUserRequest(User):
    pass


class CreateResultRequest(TestResult):
    pass


class CreateSessionRequest(Session):
    pass


class CreateMessageRequest(Message):
    pass


# Public content endpoints
@app.get("/plans", response_model=List[Plan])
def get_plans():
    existing = get_documents("plan")
    if not existing:
        # Seed default plans if empty
        defaults = [
            Plan(id="free", name="Free", price=0.0, features=["Color test", "Basic insights"]),
            Plan(id="plus", name="Plus", price=9.0, features=["Deeper insights", "Chatbot guidance", "History"]),
            Plan(id="pro", name="Pro", price=29.0, features=["All Plus", "Sessions with professionals", "Advanced analytics"]) 
        ]
        for p in defaults:
            create_document("plan", p)
        return defaults
    # Convert raw docs to Plan
    out: List[Plan] = []
    for d in existing:
        try:
            out.append(Plan(**{k: d[k] for k in ["id","name","price","interval","features"]}))
        except Exception:
            continue
    return out


# Users
@app.post("/users")
def create_user(payload: CreateUserRequest):
    user_id = create_document("user", payload)
    return {"id": user_id}


# Test results
@app.post("/results")
def create_result(payload: CreateResultRequest):
    # auto timestamp if not provided
    data = payload.model_dump()
    if not data.get("taken_at"):
        data["taken_at"] = datetime.utcnow().isoformat()
    inserted_id = create_document("testresult", data)
    return {"id": inserted_id}


@app.get("/results/{user_id}")
def list_results(user_id: str):
    docs = get_documents("testresult", {"user_id": user_id}, limit=50)
    # Normalize ObjectId
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return {"items": docs}


# Professionals and sessions
@app.get("/professionals")
def list_professionals():
    items = get_documents("professional", {}, limit=50)
    if not items:
        seed = [
            Professional(name="Dr. Riley Shaw", specialty="Therapist", bio="CBT, mindfulness", availability=[]),
            Professional(name="Avery Chen", specialty="Life Coach", bio="Habits, goals", availability=[]),
            Professional(name="Samir Patel", specialty="Counselor", bio="Stress, burnout", availability=[]),
        ]
        for s in seed:
            create_document("professional", s)
        items = [s.model_dump() for s in seed]
    for d in items:
        d["id"] = str(d.get("_id", ""))
        d.pop("_id", None)
    return {"items": items}


@app.post("/sessions")
def create_session(payload: CreateSessionRequest):
    session_id = create_document("session", payload)
    return {"id": session_id}


@app.get("/sessions/{user_id}")
def get_sessions(user_id: str):
    items = get_documents("session", {"user_id": user_id}, limit=50)
    for d in items:
        d["id"] = str(d.get("_id", ""))
        d.pop("_id", None)
    return {"items": items}


# Chat messages (simple history store)
@app.post("/messages")
def post_message(payload: CreateMessageRequest):
    message_id = create_document("message", payload)
    return {"id": message_id}


@app.get("/messages/{user_id}")
def get_messages(user_id: str):
    items = get_documents("message", {"user_id": user_id}, limit=100)
    for d in items:
        d["id"] = str(d.get("_id", ""))
        d.pop("_id", None)
    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
