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

@app.post("/sign")
def sign_url(req: SignReq):
    if not req.pid or not req.key:
        raise HTTPException(400, "missing fields")
    if not req.key.endswith((".webm",".ogg",".wav",".mp4",".m4a",".dat")):
        raise HTTPException(400, "unsupported extension")
    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": SPACES_BUCKET, "Key": req.key, "ContentType": req.content_type, "ACL": "private"},
            ExpiresIn=60*5,
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(500, f"sign error: {e}")
