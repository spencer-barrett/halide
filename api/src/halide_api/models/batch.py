# models/batch.py
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, BigInteger, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from halide_api.db import Base

class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    label: Mapped[str | None] = mapped_column(String(255))
    asset_count: Mapped[int | None]
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))