# speech-exp

Static frontend (MediaRecorder) + FastAPI `/sign` for DigitalOcean Spaces presigned uploads.

## Deploy (DigitalOcean App Platform)
- Component 1: **Static Site** → directory `static/`
- Component 2: **Service (Python)** → directory `api/`
  - Env vars: `SPACES_KEY`, `SPACES_SECRET`, `SPACES_BUCKET` (psycho-audio), `SPACES_REGION` (nyc3)

After deploy:
- Take your API URL and put it into `static/index.html` as `API_BASE = "https://...app.ondigitalocean.app"`.
- Ensure Spaces CORS allows PUT from your site origin.
