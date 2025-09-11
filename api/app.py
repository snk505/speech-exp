from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3, os

SPACES_KEY     = os.environ.get("SPACES_KEY","")
SPACES_SECRET  = os.environ.get("SPACES_SECRET","")
SPACES_BUCKET  = os.environ.get("SPACES_BUCKET","psycho-audio")
SPACES_REGION  = os.environ.get("SPACES_REGION","nyc3")
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
    allow_origins=["*"],  # tighten later to your frontend origin
    allow_methods=["POST","OPTIONS"],
    allow_headers=["*"],
)

class SignReq(BaseModel):
    pid: str
    key: str
    content_type: str = "audio/webm"

ALLOWED_EXTS = (".webm", ".weba", ".ogg", ".opus", ".wav", ".mp4", ".m4a", ".mp3", ".dat")

CT_EXT_MAP = {
    "audio/webm": ".webm",
    "audio/webm;codecs=opus": ".webm",
    "audio/weba": ".weba",
    "audio/ogg": ".ogg",
    "audio/ogg;codecs=opus": ".ogg",
    "audio/opus": ".opus",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/m4a": ".m4a",
}

def _ext_from_content_type(ct: str):
    if not ct: return None
    ct_l = ct.strip().lower()
    if ct_l in CT_EXT_MAP:
        return CT_EXT_MAP[ct_l]
    if ";" in ct_l:
        base = ct_l.split(";", 1)[0].strip()
        return CT_EXT_MAP.get(base)
    return None

@app.post("/sign")
def sign_url(req: SignReq):
    if not req.pid or not req.key:
        raise HTTPException(400, "missing fields")

    key = req.key.strip()
    ct  = (req.content_type or "").strip()
    k_low = key.lower()

    # ensure allowed extension; infer and append if missing
    if not any(k_low.endswith(ext) for ext in ALLOWED_EXTS):
        ext = _ext_from_content_type(ct) or ".webm"
        key = f"{key}{ext}"
        k_low = key.lower()

    if not any(k_low.endswith(ext) for ext in ALLOWED_EXTS):
        raise HTTPException(400, f"unsupported extension on key: {key}")

    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": SPACES_BUCKET,
            "Key": key,
            "ContentType": ct or "application/octet-stream",
            "ACL": "private",
        },
        ExpiresIn=60 * 5,
    )
    return {"url": url, "key": key}


@app.get("/health")
def health():
    return {"ok": True, "bucket": SPACES_BUCKET, "region": SPACES_REGION}

