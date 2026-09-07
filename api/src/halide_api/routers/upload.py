from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from halide_api.schemas.upload import PrepareRequest, PrepareResponse, PrepareResult, ConfirmRequest, ConfirmResponse, ConfirmResult
from halide_api.db import SessionDep
from sqlalchemy import func, select
from halide_api.models.asset import Asset
from halide_api.models.batch import Batch
import uuid
from halide_api.services.auth import CurrentUser
from halide_api.services.storage import presign_put, get_meta_object

router = APIRouter(prefix="/api/upload")

@router.post("/prepare", response_model=PrepareResponse)
def prepare_upload(req: PrepareRequest, db: SessionDep, user: CurrentUser) -> PrepareResponse:
    hashes = [f.sha256 for f in req.files]
    stmt = select(Asset.sha256).where(Asset.sha256.in_(hashes), Asset.owner_id == user)
    existing_hashes = set(db.scalars(stmt).all())
    
    batch = Batch(label=req.label, owner_id=user)
    db.add(batch)
    db.flush()
    
    batched_results: list[PrepareResult] = []
    
    for f in req.files:
        if f.sha256 in existing_hashes:
            batched_results.append(PrepareResult(client_ref=f.client_ref, status="duplicate"))
        else:
            asset_id = uuid.uuid4()
            upload_url = presign_put(f"assets/{asset_id}")
            batched_results.append(PrepareResult(client_ref=f.client_ref, status="upload", asset_id=asset_id, upload_url=upload_url))
            asset = Asset(id=asset_id, sha256=f.sha256, original_filename=f.filename, mime=f.mime, size_bytes=f.size_bytes, batch_id=batch.id, owner_id=user)
            db.add(asset)
            existing_hashes.add(f.sha256)
    
    
    db.commit()
    
    return PrepareResponse(batch_id=batch.id, results=batched_results)

@router.post("/confirm", response_model=ConfirmResponse)
def confirm_upload(req: ConfirmRequest, db:SessionDep, user:CurrentUser) -> ConfirmResponse:
    
    batch = db.get(Batch, req.batch_id)
    if batch is None or batch.owner_id!= user:
        raise HTTPException(status_code=404, detail="batch not found")
    
    stmt = select(Asset).where(Asset.id.in_(req.asset_ids), Asset.batch_id == req.batch_id, Asset.owner_id == user)
    assets = db.scalars(stmt).all()
    batched_verified = False
    
    batched_results: list[ConfirmResult] = []
    by_id = {a.id: a for a in assets}
    
    for asset_id in req.asset_ids:
        if asset_id not in by_id:
            batched_results.append(ConfirmResult(asset_id=asset_id, status="unknown"))
            continue
        
        meta_object = get_meta_object(f"assets/{asset_id}")
        if meta_object is None:
            batched_results.append(ConfirmResult(asset_id=asset_id, status="missing"))
            continue
        if meta_object["ContentLength"] != by_id[asset_id].size_bytes:
            batched_results.append(ConfirmResult(asset_id=asset_id, status="size_mismatch"))
            continue

        by_id[asset_id].verified_at = datetime.now(timezone.utc)
        batched_results.append(ConfirmResult(asset_id=asset_id, status="verified"))
    
    db.flush()
    
    total_stmt = select(func.count()).select_from(Asset).where(Asset.batch_id == req.batch_id, Asset.owner_id == user)
    total_count = db.scalar(total_stmt) or 0
    
    unverified_stmt = select(func.count()).select_from(Asset).where(Asset.batch_id == req.batch_id, Asset.verified_at.is_(None), Asset.owner_id == user)
    unverified_count = db.scalar(unverified_stmt) or 0
    
    verified_count = total_count - unverified_count
    
    if (unverified_count == 0) and (total_count > 0):
       batch.verified_at = datetime.now(timezone.utc)
       batched_verified = True
           
            
    db.commit()
            
    return ConfirmResponse(batch_id=batch.id, results=batched_results, batch_verified=batched_verified, verified_count=verified_count, total_count=total_count)
            