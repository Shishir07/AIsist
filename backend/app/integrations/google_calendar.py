import json
import logging

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import GoogleToken

logger = logging.getLogger(__name__)
router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.events.freebusy",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri],
    }
}

# Single-user POC: store flow in memory between login and callback
_pending_flow: Flow | None = None


@router.get("/google/login")
async def google_login():
    """Redirect user to Google OAuth consent screen."""
    global _pending_flow
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    _pending_flow = flow  # store for callback
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(code: str, state: str = None):
    """Handle Google OAuth callback, store tokens in DB."""
    global _pending_flow

    if _pending_flow is None:
        return {"error": "No pending OAuth flow. Please visit /api/auth/google/login first."}

    _pending_flow.fetch_token(code=code)
    creds = _pending_flow.credentials
    _pending_flow = None  # clear after use

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GoogleToken).limit(1))
        token_row = result.scalar_one_or_none()

        if token_row is None:
            token_row = GoogleToken()
            db.add(token_row)

        token_row.access_token = creds.token
        token_row.refresh_token = creds.refresh_token
        token_row.token_uri = creds.token_uri
        token_row.client_id = creds.client_id
        token_row.client_secret = creds.client_secret
        token_row.scopes = json.dumps(list(creds.scopes))
        token_row.expiry = creds.expiry

        await db.commit()

    # Redirect back to the app with success
    return HTMLResponse("""
        <html><body>
        <script>window.location.href = 'http://localhost:5173';</script>
        <p>Google Calendar connected ✅ Redirecting back to AIsist...</p>
        </body></html>
    """)


async def get_calendar_service():
    """Build and return an authenticated Google Calendar service."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GoogleToken).limit(1))
        token_row = result.scalar_one_or_none()

    if token_row is None:
        raise ValueError(
            "Google Calendar not connected. Please visit /api/auth/google/login first."
        )

    creds = Credentials(
        token=token_row.access_token,
        refresh_token=token_row.refresh_token,
        token_uri=token_row.token_uri,
        client_id=token_row.client_id,
        client_secret=token_row.client_secret,
        scopes=json.loads(token_row.scopes),
    )

    service = build("calendar", "v3", credentials=creds)
    return service
