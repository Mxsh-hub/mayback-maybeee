from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["frontend"])
static_dir = Path(__file__).resolve().parent.parent / "static"


@router.get("/", include_in_schema=False)
def index_page() -> FileResponse:
    return FileResponse(static_dir / "index.html")
