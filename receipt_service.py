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
from config import GOOGLE_API_KEY, GOOGLE_APPLICATION_CREDENTIALS

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
        # Check for authentication credentials
        if not GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
            print(f"Error: Google Cloud credentials not found or path is invalid: {GOOGLE_APPLICATION_CREDENTIALS}")
            return None

        client = vision.ImageAnnotatorClient()
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
