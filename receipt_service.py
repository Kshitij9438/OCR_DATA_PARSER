"""
Core service for processing receipt images.
Handles OCR and LLM-based data structuring.
"""
import os
import asyncio
from datetime import datetime
from typing import Union, Optional

# Pydantic and Pydantic-AI imports
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

# Google Cloud Vision imports
from google.cloud import vision
from google.api_core import exceptions

# Import your configuration
from config import (
    GOOGLE_API_KEY, 
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CLOUD_PROJECT_ID,
    GOOGLE_CLOUD_PRIVATE_KEY,
    GOOGLE_CLOUD_CLIENT_EMAIL,
    GOOGLE_CLOUD_CLIENT_ID
)

# --- 1. Define the Structured Output (Your Pydantic Model) ---
class Expenses(BaseModel):
    amount: float = Field(..., ge=0, description="The total amount of the expense")
    date: Union[datetime, str] = Field(..., description="The date of the expense in YYYY-MM-DDTHH:MM:SS format")
    companions: list[str] = Field(default_factory=list, description="List of companions, if any")
    description: str = Field(default="", description="A brief description of the expense")
    category: str = Field(default="Other", description="The category of the expense")
    subcategory: str = Field(default="", description="The sub-category of the expense")
    paymentMethod: Optional[str] = Field(None, description="The payment method used")

# --- 2. The OCR Function ---
def get_text_from_receipt(image_path: str) -> Optional[str]:
    """Uses Google Cloud Vision to perform OCR on a local image file."""
    try:
        # Initialize client with different credential methods
        client = None
        
        # Method 1: Use JSON credentials file
        if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
            print(f"Using JSON credentials file: {GOOGLE_APPLICATION_CREDENTIALS}")
            client = vision.ImageAnnotatorClient()
        
        # Method 2: Use individual environment variables
        elif all([GOOGLE_CLOUD_PROJECT_ID, GOOGLE_CLOUD_PRIVATE_KEY, GOOGLE_CLOUD_CLIENT_EMAIL]):
            print("Using individual credential environment variables")
            print(f"Project ID: {GOOGLE_CLOUD_PROJECT_ID}")
            print(f"Client Email: {GOOGLE_CLOUD_CLIENT_EMAIL}")
            from google.oauth2 import service_account
            import json
            
            # Create credentials from environment variables
            credentials_info = {
                "type": "service_account",
                "project_id": GOOGLE_CLOUD_PROJECT_ID,
                "private_key_id": GOOGLE_CLOUD_CLIENT_ID or "",
                "private_key": GOOGLE_CLOUD_PRIVATE_KEY.replace('\\n', '\n'),
                "client_email": GOOGLE_CLOUD_CLIENT_EMAIL,
                "client_id": GOOGLE_CLOUD_CLIENT_ID or "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{GOOGLE_CLOUD_CLIENT_EMAIL}"
            }
            
            print("Creating credentials from environment variables...")
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            print("Creating Vision client...")
            client = vision.ImageAnnotatorClient(credentials=credentials)
            print("Vision client created successfully!")
        
        else:
            print("Error: No valid Google Cloud credentials found")
            print("Please set either:")
            print("1. GOOGLE_APPLICATION_CREDENTIALS pointing to a valid JSON file, or")
            print("2. GOOGLE_CLOUD_PROJECT_ID, GOOGLE_CLOUD_PRIVATE_KEY, and GOOGLE_CLOUD_CLIENT_EMAIL")
            return None

        print(f"Reading image from: {image_path}")
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        print("Sending request to Google Cloud Vision API...")
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise exceptions.GoogleAPICallError(response.error.message)

        if response.text_annotations:
            print("OCR successful.")
            return response.text_annotations[0].description
        
        print("No text found in the image.")
        return ""

    except Exception as e:
        print(f"An unexpected error occurred during OCR: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"Full OCR error traceback: {error_details}")
        return None

# --- 3. The LLM Agent for Structuring the Data ---
async def structure_receipt_text(text: str) -> Optional[Expenses]:
    """Uses an LLM agent to parse raw text into the Expenses model."""
    
    SYSTEM_PROMPT = """
    You are an expert receipt-parsing AI. Your task is to extract structured data from the raw OCR text of a receipt and format it as a JSON object matching the `Expenses` schema.

    **Rules and Heuristics:**
    1.  **`amount`**: Find the final total amount. Look for keywords like "Total", "BIL-TOT", or the largest monetary value near the bottom.
    2.  **`date`**: Find the date. If a time is present, combine them. Format the output as "YYYY-MM-DDTHH:MM:SS".
    3.  **`paymentMethod`**: Look for "Cash", "Credit Card", "UPI", "Card". If not found, set to null.
    4.  **`category` & `subcategory`**: Infer these from the merchant's name (e.g., "Biryani Mahal" -> category: "Food", subcategory: "Dining").
    5.  **`description`**: Create a concise summary including the merchant's name and the first few items.
    6.  **`companions`**: This is almost never on a receipt. Leave as an empty list `[]` unless specific names are clearly mentioned.
    """
    
    try:
        provider = GoogleProvider(api_key=GOOGLE_API_KEY)
        model = GoogleModel("gemini-1.5-flash", provider=provider)

        receipt_parsing_agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            output_type=Expenses,
        )

        print("Sending OCR text to LLM for structuring...")
        agent_result = await receipt_parsing_agent.run(text)
        print("LLM structuring successful.")
        
        if agent_result and agent_result.output:
            return agent_result.output
        return None

    except Exception as e:
        print(f"An unexpected error occurred during LLM processing: {e}")
        return None
