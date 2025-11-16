import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Player, Testimonial, ContactSubmission
from datetime import datetime
import re

app = FastAPI(title="Player Landing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Player Landing Backend running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# ------------------- Utility --------------------
slug_regex = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def collection_name(model_cls):
    return model_cls.__name__.lower()

# ------------------- Players --------------------
@app.post("/api/players", response_model=Player)
def create_player(player: Player):
    if not slug_regex.match(player.slug):
        raise HTTPException(status_code=400, detail="Invalid slug. Use lowercase letters, numbers and dashes.")
    # Ensure slug unique
    existing = list(db[collection_name(Player)].find({"slug": player.slug}).limit(1)) if db else []
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")
    _id = create_document(collection_name(Player), player)
    created = db[collection_name(Player)].find_one({"_id": db[collection_name(Player)]._Database__client.get_default_database().codec_options.document_class()._id}) if False else None
    # Fetch freshly created document
    created = db[collection_name(Player)].find_one({"slug": player.slug})
    created["_id"] = str(created["_id"])  # convert id for response safety
    return Player(**{k: v for k, v in created.items() if k != "_id"})

@app.get("/api/players/{slug}", response_model=Player)
def get_player(slug: str):
    doc = db[collection_name(Player)].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Player not found")
    doc.pop("_id", None)
    return Player(**doc)

# ---------------- Testimonials ------------------
@app.get("/api/players/{slug}/testimonials", response_model=List[Testimonial])
def list_testimonials(slug: str):
    docs = db[collection_name(Testimonial)].find({"player_slug": slug})
    res = []
    for d in docs:
        d.pop("_id", None)
        res.append(Testimonial(**d))
    return res

@app.post("/api/players/{slug}/testimonials", response_model=Testimonial)
def add_testimonial(slug: str, testimonial: Testimonial):
    if testimonial.player_slug != slug:
        raise HTTPException(status_code=400, detail="player_slug mismatch")
    create_document(collection_name(Testimonial), testimonial)
    return testimonial

# ----------------- Contact Form -----------------
class ContactEmailPayload(BaseModel):
    player_slug: str
    name: str
    role: str
    club_name: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    country: Optional[str] = None
    message: Optional[str] = None


def send_email_background(to_email: str, subject: str, content: str):
    """Simple email sender using SMTP if configured. This is optional; if not configured, we just store submission."""
    import smtplib
    from email.mime.text import MIMEText

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or to_email)

    if not (smtp_host and smtp_user and smtp_pass):
        # SMTP not configured; skip sending.
        return

    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [to_email], msg.as_string())
    except Exception:
        # swallow errors to not fail request
        pass

@app.post("/api/players/{slug}/contact")
def submit_contact(slug: str, payload: ContactSubmission, background_tasks: BackgroundTasks):
    if payload.player_slug != slug:
        raise HTTPException(status_code=400, detail="player_slug mismatch")

    # Store submission
    create_document(collection_name(ContactSubmission), payload)

    # Lookup player email
    player = db[collection_name(Player)].find_one({"slug": slug})
    if player and player.get("contact_email"):
        subject = f"New Contact/Trial Request for {player.get('name')}"
        lines = [
            f"Name: {payload.name}",
            f"Role: {payload.role}",
            f"Club: {payload.club_name or '-'}",
            f"Email: {payload.email or '-'}",
            f"WhatsApp: {payload.whatsapp or '-'}",
            f"Country: {payload.country or '-'}",
            "",
            f"Message:\n{payload.message or '-'}",
            "",
            f"Submitted at: {datetime.utcnow().isoformat()} UTC"
        ]
        content = "\n".join(lines)
        background_tasks.add_task(send_email_background, player.get("contact_email"), subject, content)

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
