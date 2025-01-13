from fastapi import FastAPI
from app.routers import payments
from pathlib import Path
from app.database import create_database
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, HTTPException
from app.utils import normalize_csv_and_save_to_db
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Payment Management API")

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(payments.router)
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
async def startup():
    create_database()

@app.get("/")
async def root():
    return {"message": "Payment Management API is running"}

@app.post("/normalize-csv/")
async def normalize_csv(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    try:
        file_location = UPLOAD_DIR / file.filename
        with open(file_location, "wb") as f:
            f.write(await file.read())
        
        result = normalize_csv_and_save_to_db(str(file_location))
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
app.mount("/evidence", StaticFiles(directory='app/uploads/evidence_files'), name="evidence")