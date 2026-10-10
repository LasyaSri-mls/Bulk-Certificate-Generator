from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from sqlalchemy.orm import Session
from . import certificates
from .models import CertificateRecipient, GenerationJob
from .schemas import GenerationRequest


def create_and_process_job(db: Session, payload: GenerationRequest) -> GenerationJob:
    job = GenerationJob(
        id=str(uuid4()),
        event_name=payload.event_name,
        issue_date=payload.issue_date,
        status="PROCESSING",
        total=len(payload.recipients),
        processed=0,
        successful=0,
        failed=0,
    )
    db.add(job)

    recipients = [
        CertificateRecipient(
            id=str(uuid4()),
            job_id=job.id,
            name=item.name,
            email=str(item.email),
            status="PENDING",
        )
        for item in payload.recipients
    ]
    db.add_all(recipients)
    db.commit()
    db.refresh(job)

    # Each recipient is isolated: one PDF failure does not stop the rest.
    for recipient in recipients:
        try:
            path = certificates.generate_certificate_pdf(
                recipient_name=recipient.name,
                event_name=job.event_name,
                issue_date=job.issue_date,
                recipient_id=recipient.id,
            )
            recipient.file_path = str(Path(path).resolve())
            recipient.status = "SUCCESS"
            recipient.error_message = None
            job.successful += 1
        except Exception:
            recipient.status = "FAILED"
            recipient.error_message = "Certificate generation failed."
            job.failed += 1

        job.processed += 1
        db.commit()

    if job.failed == 0:
        job.status = "COMPLETED"
    elif job.successful == 0:
        job.status = "FAILED"
    else:
        job.status = "PARTIALLY_COMPLETED"

    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job
