"""
FastAPI application to expose the receipt processing service as a web API.
"""
import uvicorn
import shutil
import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import the core processing functions and your Pydantic model
from receipt_service import get_text_from_receipt, structure_receipt_text, Expenses
from config import PORT, DEBUG

# Initialize the FastAPI app
app = FastAPI(
    title="Receipt Processing API",
    description="An API to extract structured expense data from receipt images.",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your friend's web app (running on a different domain/port)
# to make requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", tags=["Health Check"])
async def root():
    """A simple health check endpoint to confirm the API is running."""
    return {
        "message": "Receipt Processing API is running.",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug-env", tags=["Debug"])
async def debug_env():
    """Debug endpoint to check environment variables directly."""
    import os
    return {
        "GOOGLE_CLOUD_PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT_ID", "NOT_SET"),
        "GOOGLE_CLOUD_PRIVATE_KEY": "SET" if os.getenv("GOOGLE_CLOUD_PRIVATE_KEY") else "NOT_SET",
        "GOOGLE_CLOUD_CLIENT_EMAIL": os.getenv("GOOGLE_CLOUD_CLIENT_EMAIL", "NOT_SET"),
        "GOOGLE_CLOUD_CLIENT_ID": os.getenv("GOOGLE_CLOUD_CLIENT_ID", "NOT_SET"),
        "GOOGLE_API_KEY": "SET" if os.getenv("GOOGLE_API_KEY") else "NOT_SET"
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Detailed health check endpoint for Railway monitoring."""
    try:
        # Check if required environment variables are present
        from config import (
            GOOGLE_API_KEY, 
            GOOGLE_APPLICATION_CREDENTIALS,
            GOOGLE_CLOUD_PROJECT_ID,
            GOOGLE_CLOUD_PRIVATE_KEY,
            GOOGLE_CLOUD_CLIENT_EMAIL
        )
        
        # Check Google Vision credentials
        vision_configured = False
        if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
            vision_configured = True
        elif all([GOOGLE_CLOUD_PROJECT_ID, GOOGLE_CLOUD_PRIVATE_KEY, GOOGLE_CLOUD_CLIENT_EMAIL]):
            vision_configured = True
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "api": "operational",
                "google_vision": "operational" if vision_configured else "not_configured",
                "google_ai": "operational" if GOOGLE_API_KEY else "not_configured"
            },
            "debug": {
                "has_project_id": bool(GOOGLE_CLOUD_PROJECT_ID),
                "has_private_key": bool(GOOGLE_CLOUD_PRIVATE_KEY),
                "has_client_email": bool(GOOGLE_CLOUD_CLIENT_EMAIL),
                "has_credentials_file": bool(GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS))
            }
        }
            
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e) if DEBUG else "Health check failed"
        }

@app.post("/process-receipt/", response_model=Expenses, tags=["Receipt Processing"])
async def process_receipt_endpoint(file: UploadFile = File(...)):
    """
    Accepts an uploaded receipt image, performs OCR and LLM structuring,
    and returns the extracted expense data as JSON.
    """
    # Create a temporary path to save the uploaded file in /tmp (Railway allows writing here)
    temp_file_path = f"/tmp/temp_{file.filename}"
    
    try:
        # Save the uploaded file to disk
        contents = await file.read()
        with open(temp_file_path, "wb") as buffer:
            buffer.write(contents)

        # --- Step 1: Perform OCR ---
        raw_text = get_text_from_receipt(temp_file_path)
        if raw_text is None:
            raise HTTPException(status_code=500, detail="OCR processing failed.")
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="No text could be found in the image.")

        # --- Step 2: Structure Text with LLM ---
        expense_data = await structure_receipt_text(raw_text)
        if not expense_data:
            raise HTTPException(status_code=500, detail="LLM failed to structure the receipt data.")
            
        # Return the final structured data
        return expense_data

    except Exception as e:
        # If any unexpected error occurs, return a generic 500 error
        # In debug mode, we can return the specific error message
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing receipt: {e}")
        print(f"Full traceback: {error_details}")
        
        detail = str(e)  # Always show the actual error for now
        raise HTTPException(status_code=500, detail=detail)
    finally:
        # --- Step 3: Clean up the temporary file ---
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    # This allows you to run the API directly using `python api.py`
    print(f"Starting API server on http://0.0.0.0:{PORT}")
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, reload=True)
