from fastapi import FastAPI
from halide_api.services.storage import presign_put
from halide_api.db import get_db, SessionDep
from sqlalchemy import select, func
from halide_api.models.batch import Batch
from halide_api.routers import upload



app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World!"}


@app.get("/api/debug/presign")
async def debug_presign(key: str):
    return {"url": presign_put(key)}

@app.get("/api/debug/db")
def db_retrieve(db: SessionDep):
    stmt = select(func.count()).select_from(Batch)
    count = db.execute(stmt).scalar()
    return {"count": count}

app.include_router(upload.router)
