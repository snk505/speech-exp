# api/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3, os, re

SPACES_KEY     = os.environ["SPACES_KEY"]
SPACES_SECRET  = os.environ["SPACES_SECRET"]
SPACES_BUCKET  = os.environ["SPACES_BUCKET"]       # e.g., "psycho-audio"
SPACES_REGION  = os.environ["SPACES_REGION"]       # e.g., "sgp1"
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"

s3 = boto3.client(
    "s3",
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_KEY,
    aws_secret_access_key=SPACES_SECRET,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten to your frontend origin later
    allow_methods=["POST","OPTIONS"],
    allow_headers=["*"],
)

class PostReq(BaseModel):
    pid: str
    key: str  # we’ll return the final key back

def _safe_key(k: str) -> str:
    k = re.sub(r"\s+", "_", k.strip())
    k = re.sub(r"[^A-Za-z0-9_\-./]", "", k)
    if not re.search(r"\.(webm|weba|ogg|opus|wav|m4a|mp4|mp3)$", k, re.I):
        k += ".webm"
    return k[:200]

@app.post("/sign_post")
def sign_post(req: PostReq):
    if not req.pid or not req.key:
        raise HTTPException(400, "missing fields")
    key = _safe_key(req.key)

    try:
        # You can add conditions to enforce size limits, etc.
        # DO NOT include Content-Type condition so the browser doesn't need to set it.
        post = s3.generate_presigned_post(
            Bucket=SPACES_BUCKET,
            Key=key,
            Fields={
                # Return 201 for easier client-side success detection
                "success_action_status": "201",
            },
            Conditions=[
                {"success_action_status": "201"},
                # Example: ["content-length-range", 1, 50 * 1024 * 1024],  # up to 50 MB
            ],
            ExpiresIn=300,
        )
        # post = { "url": "https://<bucket>.<region>.digitaloceanspaces.com", "fields": {...} }
        return {"url": post["url"], "fields": post["fields"], "key": key}
    except Exception as e:
        raise HTTPException(500, f"sign_post error: {e}")
