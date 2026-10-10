from fastapi import FastAPI
from .database import Base, engine
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate, track, and download certificates in bulk.",
    version="1.0.0",
)
app.include_router(router)


@app.get("/", tags=["Health"])
def home():
    return {"message": "Bulk Certificate Generator API", "status": "running"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
