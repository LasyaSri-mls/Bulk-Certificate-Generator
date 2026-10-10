import os
import tempfile
import zipfile
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import CertificateRecipient, GenerationJob
from .schemas import (
    GenerationRequest, JobResponse, RecipientListResponse, RecipientResponse
)
from .services import create_and_process_job

router = APIRouter(prefix="/api", tags=["Certificates"])


@router.post("/jobs/", response_model=JobResponse, status_code=201)
def create_job(payload: GenerationRequest, db: Session = Depends(get_db)):
    return create_and_process_job(db, payload)


@router.get("/jobs/{job_id}/", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return job


@router.get("/jobs/{job_id}/certificates/", response_model=RecipientListResponse)
def list_certificates(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    recipients = db.query(CertificateRecipient).filter(
        CertificateRecipient.job_id == job_id
    ).all()

    items = [
        RecipientResponse(
            id=r.id,
            name=r.name,
            email=r.email,
            status=r.status,
            error_message=r.error_message,
            download_url=f"/api/certificates/{r.id}/download/" if r.status == "SUCCESS" else None,
        )
        for r in recipients
    ]
    return RecipientListResponse(job_id=job_id, total=len(items), recipients=items)


@router.get("/certificates/{recipient_id}/download/")
def download_certificate(recipient_id: str, db: Session = Depends(get_db)):
    recipient = db.get(CertificateRecipient, recipient_id)
    if not recipient or recipient.status != "SUCCESS" or not recipient.file_path:
        raise HTTPException(status_code=404, detail="Generated certificate not found")

    path = Path(recipient.file_path).resolve()
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Certificate file is missing")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"certificate-{recipient.id}.pdf",
    )


@router.get("/jobs/{job_id}/download/")
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    recipients = db.query(CertificateRecipient).filter(
        CertificateRecipient.job_id == job_id,
        CertificateRecipient.status == "SUCCESS",
    ).all()

    if not recipients:
        raise HTTPException(status_code=404, detail="No successful certificates to download")

    output_dir = Path(os.getenv("CERTIFICATE_OUTPUT_DIR", "generated_certificates")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"job-{job.id}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for recipient in recipients:
            if recipient.file_path:
                path = Path(recipient.file_path).resolve()
                if path.is_file():
                    archive.write(path, arcname=f"{recipient.name[:60]}-{recipient.id}.pdf")

    if zip_path.stat().st_size == 0:
        raise HTTPException(status_code=404, detail="No certificate files were found")

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"certificates-{job.id}.zip",
    )
