# Bulk Certificate Generator

A Python REST API that accepts a batch of recipients, creates one PDF certificate per recipient, tracks success/failure, and supports individual and ZIP downloads.

## Tech stack

- FastAPI and Pydantic for REST APIs and input validation
- SQLAlchemy with SQLite for persistent job and recipient records
- ReportLab for PDF generation
- Pytest and HTTPX for automated tests

## Requirements

- Python 3.10+
- pip

## Setup

```bash
python -m venv venv
```

Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the API from the project root:
```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Submit a bulk request

`POST /api/jobs/`

Example JSON:
```json
{
  "event_name": "AI Workshop 2026",
  "issue_date": "2026-10-09",
  "recipients": [
    {"name": "Ananya Rao", "email": "ananya@example.com"},
    {"name": "Rahul Kumar", "email": "rahul@example.com"}
  ]
}
```

The response includes a job ID, final status, total count, processed count, successes, and failures. This initial implementation processes synchronously, so the response is returned after the batch is processed.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/jobs/` | Validate recipients and generate certificates |
| GET | `/api/jobs/{job_id}/` | Get job status and counts |
| GET | `/api/jobs/{job_id}/certificates/` | List recipient results and download links |
| GET | `/api/certificates/{recipient_id}/download/` | Download one PDF |
| GET | `/api/jobs/{job_id}/download/` | Download successful PDFs in a ZIP |

## Run tests

```bash
pytest -q
```

Tests cover job creation, input validation, status/progress fields, individual PDF retrieval, ZIP retrieval, and continuing after one recipient's PDF generation fails.

## Architecture and processing flow

1. The route validates the request using Pydantic.
2. SQLAlchemy stores one generation job and one recipient record per recipient.
3. The service processes each recipient independently.
4. ReportLab generates a PDF for each successful recipient.
5. Recipient status and job counts are committed to SQLite.
6. The client can query the job and retrieve PDFs or a ZIP of successful files.

## Design decisions

- **FastAPI:** provides typed request validation and interactive OpenAPI documentation.
- **SQLite:** simple local relational storage with no separate database server. PostgreSQL would be suitable for a deployed multi-user system.
- **One record per recipient:** makes it possible to report individual failures and download results.
- **Independent error handling:** a single certificate failure does not abort the entire batch.
- **Synchronous processing:** chosen to keep the initial version easy to run and explain. For large or time-consuming jobs, return a job ID immediately and process using a durable background queue such as Celery with Redis.
- **Single predefined template:** ReportLab draws a consistent certificate design; a template editor is outside the assignment scope.
- **File storage:** PDFs are stored on local disk for this assignment. Production deployment should use managed object storage, access controls, retention policies, and authentication.

## Learning outcomes

- REST API design and request validation
- Relational data modeling with SQLAlchemy
- PDF and ZIP file generation
- Partial failure handling
- API testing and test isolation
- Background processing trade-offs

## Future scope

- Background workers and retry support
- PostgreSQL and database migrations
- Authentication and tenant-level authorization
- Cloud object storage
- Email delivery and certificate verification QR codes
- Structured logging, monitoring, and deployment with Docker

## Security and production notes

This is an educational starter implementation. Before public production use, add authentication and authorization, rate and batch-size limits, durable background processing, secure file storage, database migrations, and operational logging. The API currently limits a request to 5,000 recipients and stores generated files locally.
