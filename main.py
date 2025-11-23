from __future__ import annotations

import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host=settings.uvicorn_host, port=settings.uvicorn_port, reload=True)
