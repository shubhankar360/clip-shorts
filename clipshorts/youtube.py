"""Upload/schedule Shorts with the official YouTube Data API v3 (free quota, ~6 uploads/day).

Setup once: Google Cloud Console -> enable "YouTube Data API v3" -> OAuth client ID (Desktop app)
-> download JSON to ~/ClipShorts/secrets/client_secret.json. First upload opens a browser to sign in.
"""
import datetime as dt

from . import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    secret = config.SECRETS / "client_secret.json"
    token = config.SECRETS / "token.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not secret.exists():
                raise RuntimeError(f"Missing {secret}. See README → 'YouTube upload setup'.")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(path: str, title: str, description: str = "", tags=None, publish_at: str | None = None) -> str:
    from googleapiclient.http import MediaFileUpload

    if "#shorts" not in (title + description).lower():
        description = (description + "\n\n#shorts").strip()
    status = {"selfDeclaredMadeForKids": False}
    if publish_at:  # scheduled uploads stay private until publishAt
        status.update(privacyStatus="private", publishAt=publish_at)
    else:
        status["privacyStatus"] = "public"
    body = {"snippet": {"title": title[:100], "description": description[:5000],
                        "tags": list(tags or []), "categoryId": "24"},
            "status": status}
    req = _service().videos().insert(part="snippet,status", body=body,
                                     media_body=MediaFileUpload(str(path), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return f"https://youtube.com/shorts/{resp['id']}"


def next_slots(n: int = 4, hours=config.POST_HOURS, now: dt.datetime | None = None) -> list:
    """Next n posting slots at the given local hours, as RFC3339 UTC strings."""
    now = (now or dt.datetime.now().astimezone())
    slots, day = [], now.date()
    while len(slots) < n:
        for h in hours:
            t = dt.datetime.combine(day, dt.time(h), tzinfo=now.tzinfo)
            if t > now + dt.timedelta(minutes=20) and len(slots) < n:
                slots.append(t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        day += dt.timedelta(days=1)
    return slots
