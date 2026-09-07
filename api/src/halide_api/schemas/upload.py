# schemas/upload.py
import uuid
from typing import Literal

from pydantic import BaseModel, Field

AllowedMime = Literal["image/jpeg", "image/png", "image/heic", "image/webp"]


class PrepareFile(BaseModel):
    client_ref: str = Field(max_length=100)
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$")
    filename: str = Field(max_length=255)
    mime: AllowedMime
    size_bytes: int = Field(gt=0, le=50 * 1024 * 1024)


class PrepareRequest(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    files: list[PrepareFile] = Field(min_length=1, max_length=200)


class PrepareResult(BaseModel):
    client_ref: str
    status: Literal["upload", "duplicate"]
    asset_id: uuid.UUID | None = None
    upload_url: str | None = None


class PrepareResponse(BaseModel):
    batch_id: uuid.UUID
    results: list[PrepareResult]
    
class ConfirmRequest(BaseModel):
    batch_id: uuid.UUID
    asset_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)

class ConfirmResult(BaseModel):
    asset_id: uuid.UUID
    status: Literal["verified", "missing", "size_mismatch", "unknown"]

class ConfirmResponse(BaseModel):
    batch_id: uuid.UUID
    results: list[ConfirmResult]
    batch_verified: bool
    verified_count: int
    total_count: int
    