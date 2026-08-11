"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import secrets
import time

app = FastAPI(title="Slalom Capabilities Management API",
              description="API for managing consulting capabilities and consultant expertise")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE_NAME = "practice_lead_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
PASSWORD_HASH_ITERATIONS = 600_000
audit_logger = logging.getLogger("capability_audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    audit_handler = logging.StreamHandler()
    audit_handler.setFormatter(logging.Formatter("AUDIT %(message)s"))
    audit_logger.addHandler(audit_handler)
audit_logger.propagate = False
active_sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def load_practice_leads():
    credentials_path = current_dir / "practice_leads.json"
    with credentials_path.open(encoding="utf-8") as credentials_file:
        configured_leads = json.load(credentials_file)

    for lead in configured_leads:
        environment_variable = lead.pop("password_hash_env", None)
        if environment_variable:
            lead["password_hash"] = os.getenv(environment_variable, "")
    return configured_leads


practice_leads = load_practice_leads()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = encoded_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)


def get_active_session(session_token: str | None):
    if not session_token:
        return None
    session = active_sessions.get(session_token)
    if not session or session["expires_at"] <= time.time():
        active_sessions.pop(session_token, None)
        return None
    return session


def require_practice_lead(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    session = get_active_session(session_token)
    if not session or session["role"] != "practice_lead":
        raise HTTPException(status_code=401, detail="Practice lead authentication required")
    return session


def record_audit_event(action: str, actor: str, target: str):
    audit_logger.info(json.dumps({
        "action": action,
        "actor": actor,
        "target": target,
        "timestamp": int(time.time()),
    }))

# In-memory capabilities database
capabilities = {
    "Cloud Architecture": {
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,  # hours per week available across team
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"]
    },
    "Data Analytics": {
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology", 
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"]
    },
    "DevOps Engineering": {
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"], 
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"]
    },
    "Digital Strategy": {
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"]
    },
    "Change Management": {
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"]
    },
    "UX/UI Design": {
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"]
    },
    "Cybersecurity": {
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"]
    },
    "Business Intelligence": {
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"]
    },
    "Agile Coaching": {
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/capabilities")
def get_capabilities():
    return capabilities


@app.post("/auth/login")
def login(login_request: LoginRequest, response: Response):
    lead = next(
        (candidate for candidate in practice_leads
         if candidate["username"] == login_request.username),
        None,
    )
    if not lead or not verify_password(login_request.password, lead.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = {
        "username": lead["username"],
        "display_name": lead["display_name"],
        "role": "practice_lead",
        "practice_areas": lead["practice_areas"],
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="strict",
        secure=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    )
    record_audit_event("login", lead["username"], "session")
    return {key: active_sessions[session_token][key] for key in
            ("username", "display_name", "role", "practice_areas")}


@app.get("/auth/session")
def get_session(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    session = get_active_session(session_token)
    if not session:
        return {"authenticated": False}
    return {
        "authenticated": True,
        **{key: session[key] for key in
           ("username", "display_name", "role", "practice_areas")},
    }


@app.post("/auth/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    session = active_sessions.pop(session_token, None) if session_token else None
    response.delete_cookie(SESSION_COOKIE_NAME)
    if session:
        record_audit_event("logout", session["username"], "session")
    return {"message": "Signed out"}


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, email: str):
    """Register a consultant for a capability"""
    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Get the specific capability
    capability = capabilities[capability_name]

    # Validate consultant is not already registered
    if email in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is already registered for this capability"
        )

    # Add consultant
    capability["consultants"].append(email)
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(
    capability_name: str,
    email: str,
    practice_lead=Depends(require_practice_lead),
):
    """Unregister a consultant from a capability"""
    # Validate capability exists
    if capability_name not in capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Get the specific capability
    capability = capabilities[capability_name]

    if capability["practice_area"] not in practice_lead["practice_areas"]:
        raise HTTPException(
            status_code=403,
            detail="Practice lead is not authorized for this practice area",
        )

    # Validate consultant is registered
    if email not in capability["consultants"]:
        raise HTTPException(
            status_code=400,
            detail="Consultant is not registered for this capability"
        )

    # Remove consultant
    capability["consultants"].remove(email)
    record_audit_event(
        "unregister_consultant",
        practice_lead["username"],
        f"{capability_name}:{email}",
    )
    return {"message": f"Unregistered {email} from {capability_name}"}
