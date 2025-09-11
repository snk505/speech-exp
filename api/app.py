# app.py
import os, re
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import boto3

# --- env ---
SPACES_KEY     = os.environ.get("SPACES_KEY", "")
SPACES_SECRET  = os.environ.get("SPACES_SECRET", "")
SPACES_BUCKET  = os.environ.get("SPACES_BUCKET", "")
SPACES_REGION  = os.environ.get("SPACES_REGION", "sgp1")
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"

# --- boto client ---
s3 = boto3.client(
    "s3",
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_KEY,
    aws_secret_access_key=SPACES_SECRET,
)

app = FastAPI()

# same-origin: the app serves both UI and API, so this can be permissive or tightened
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # you can change to ["https://<your app url>"] later
    allow_methods=["POST","OPTIONS"],
    allow_headers=["*"],
)

# ---- Static UI (index at /) ----
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root_index():
    return FileResponse("static/index.html")

# ---- API: presigned PUT (simple) ----
class SignReq(BaseModel):
    pid: str
    key: str
    content_type: str = "application/octet-stream"

def _safe_key(k: str) -> str:
    k = re.sub(r"\s+","_", (k or "").strip())
    k = re.sub(r"[^A-Za-z0-9_\-./]", "", k)[:200] or "rec.webm"
    if not re.search(r"\.(webm|weba|ogg|opus|wav|m4a|mp4|mp3|dat)$", k, re.I):
        k += ".webm"
    return k

@app.post("/sign")
def sign_url(req: SignReq):
    if not req.pid or not req.key:
        raise HTTPException(400, "missing fields")
    key = _safe_key(req.key)
    ct  = (req.content_type or "application/octet-stream").strip()

    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": SPACES_BUCKET, "Key": key, "ContentType": ct},
            ExpiresIn=300,
        )
        return {"url": url, "key": key}
    except Exception as e:
        raise HTTPException(500, f"sign error: {e}")

# (Optional) API: presigned POST (avoids preflight)
class PostReq(BaseModel):
    pid: str
    key: str

@app.post("/sign_post")
def sign_post(req: PostReq):
    if not req.pid or not req.key:
        raise HTTPException(400, "missing fields")
    key = _safe_key(req.key)
    try:
        post = s3.generate_presigned_post(
            Bucket=SPACES_BUCKET,
            Key=key,
            Fields={"success_action_status": "201"},
            Conditions=[{"success_action_status": "201"}],
            ExpiresIn=300,
        )
        return {"url": post["url"], "fields": post["fields"], "key": key}
    except Exception as e:
        raise HTTPException(500, f"sign_post error: {e}")

# Health check (optional)
@app.get("/health")
def health():
    return {"ok": True}
