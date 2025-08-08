import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import tenacity
import logging
import json
from typing import List, Dict, Any

# Load .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Retry on API/network errors or blocked content
RETRY_EXCEPTIONS = (
    google_exceptions.GoogleAPIError,
    ValueError,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(RETRY_EXCEPTIONS),
    before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
    reraise=True
)
def generate_gemini_response(prompt: str, tools: List[Dict[str, Any]] = None) -> str:
    """
    Generate response from Gemini 2.5 Flash with optional tool calling support.
    
    Args:
        prompt: The input prompt
        tools: List of tool definitions for function calling
    
    Returns:
        Generated response text
    """
    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        safety_settings={
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
    )

    logger.info("Attempting to generate Gemini 2.5 Flash response...")

    if tools:
        # Enable tool calling
        model = model.with_tools(tools)
        response = model.generate_content(prompt)
        
        # Handle tool calls if present
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call'):
                    # Return tool call information
                    return {
                        "type": "tool_call",
                        "function_name": part.function_call.name,
                        "arguments": part.function_call.args
                    }
        
        return response.text
    else:
        # Standard text generation
        response = model.generate_content(prompt)
        
        if not response.parts:
            logger.warning("⚠️ Gemini response was blocked due to safety concerns.")
            raise ValueError("Gemini output was blocked by safety settings.")

        return response.text

def create_tool_definition(name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a tool definition for Gemini function calling.
    
    Args:
        name: Tool name
        description: Tool description
        parameters: Tool parameters schema
    
    Returns:
        Tool definition dictionary
    """
    return {
        "function_declarations": [{
            "name": name,
            "description": description,
            "parameters": parameters
        }]
    }
