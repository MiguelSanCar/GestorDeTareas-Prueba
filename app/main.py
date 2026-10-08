from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.routes import router
from app.database.connection import get_db_path, init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(get_db_path())
    yield


app = FastAPI(title="Gestor de tareas", version="1.0.0", lifespan=lifespan)
register_error_handlers(app)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
