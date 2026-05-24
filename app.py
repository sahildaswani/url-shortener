import os
import random
import string
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

app = FastAPI()

SHORT_CODE_LENGTH = 6
SHORT_CODE_ALPHABET = string.ascii_letters + string.digits

store: dict[str, dict] = {}


def is_valid_url(url: str) -> bool:
    if not isinstance(url, str) or not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def generate_short_code() -> str:
    while True:
        code = "".join(random.choices(SHORT_CODE_ALPHABET, k=SHORT_CODE_LENGTH))
        if code not in store:
            return code


@app.post("/api/shorten")
async def shorten(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid URL provided"})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid URL provided"})

    url = body.get("url")
    if not is_valid_url(url):
        return JSONResponse(status_code=400, content={"error": "Invalid URL provided"})

    code = generate_short_code()
    store[code] = {
        "originalUrl": url,
        "clickCount": 0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    host = request.headers.get("host", "localhost")
    scheme = request.url.scheme
    short_url = f"{scheme}://{host}/{code}"

    return JSONResponse(
        status_code=201,
        content={
            "shortCode": code,
            "shortUrl": short_url,
            "originalUrl": url,
        },
    )


@app.get("/api/stats/{short_code}")
async def stats(short_code: str):
    entry = store.get(short_code)
    if entry is None:
        return JSONResponse(status_code=404, content={"error": "Short code not found"})
    return {
        "shortCode": short_code,
        "clickCount": entry["clickCount"],
        "originalUrl": entry["originalUrl"],
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/{short_code}")
async def redirect(short_code: str):
    entry = store.get(short_code)
    if entry is None:
        return JSONResponse(status_code=404, content={"error": "Short code not found"})
    entry["clickCount"] += 1
    return RedirectResponse(url=entry["originalUrl"], status_code=302)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
