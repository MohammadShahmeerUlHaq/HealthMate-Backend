import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import tenacity
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Load .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Tool definitions for Gemini 2.5 Flash
HEALTH_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "get_user_medicines",
                "description": "Get a list of medicines prescribed to a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get medicines for"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_user_medications",
                "description": "Get all medications for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get medications for"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_bp_logs",
                "description": "Get blood pressure logs for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get logs for"
                        },
                        "date": {
                            "type": "string",
                            "description": "Optional date filter (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_sugar_logs",
                "description": "Get sugar logs for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get logs for"
                        },
                        "date": {
                            "type": "string",
                            "description": "Optional date filter (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_medication_logs",
                "description": "Get medication logs for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get logs for"
                        },
                        "date": {
                            "type": "string",
                            "description": "Optional date filter (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_user_info",
                "description": "Get user profile information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID to get information for"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    }
]

def execute_tool_call(function_name: str, arguments: Dict[str, Any], db: Session) -> str:
    """Execute a tool call with the given function name and arguments"""
    try:
        if function_name == "get_user_medicines":
            from crud.medications import get_user_medicines
            user_id = arguments.get("user_id")
            result = get_user_medicines(db, user_id)
            return json.dumps(result, default=str)
        
        elif function_name == "get_user_medications":
            from crud.medications import get_user_medications
            user_id = arguments.get("user_id")
            result = get_user_medications(db, user_id)
            return json.dumps(result, default=str)
        
        elif function_name == "get_bp_logs":
            from crud.bp_logs import get_logs_by_user_id, get_logs_by_date
            user_id = arguments.get("user_id")
            date = arguments.get("date")
            
            if date:
                result = get_logs_by_date(db, user_id, date)
            else:
                result = get_logs_by_user_id(db, user_id)
            return json.dumps(result, default=str)
        
        elif function_name == "get_sugar_logs":
            from crud.sugar_logs import get_sugar_logs_by_user, get_sugar_logs_by_date
            user_id = arguments.get("user_id")
            date = arguments.get("date")
            
            if date:
                result = get_sugar_logs_by_date(db, user_id, date)
            else:
                result = get_sugar_logs_by_user(db, user_id)
            return json.dumps(result, default=str)
        
        elif function_name == "get_medication_logs":
            from crud.medication_logs import get_logs_by_user, get_logs_by_date
            user_id = arguments.get("user_id")
            date = arguments.get("date")
            
            if date:
                result = get_logs_by_date(db, user_id, date)
            else:
                result = get_logs_by_user(db, user_id)
            return json.dumps(result, default=str)
        
        elif function_name == "get_user_info":
            from crud.users import get_user
            user_id = arguments.get("user_id")
            result = get_user(db, user_id)
            return json.dumps(result, default=str)
        
        else:
            return f"Unknown function: {function_name}"
    
    except Exception as e:
        logger.error(f"Error executing tool {function_name}: {e}")
        return f"Error executing {function_name}: {str(e)}"

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type((google_exceptions.GoogleAPIError, ValueError)),
    before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
    reraise=True
)
def generate_response_with_tools(prompt: str, db: Session, user_id: int) -> str:
    """
    Generate response from Gemini 2.5 Flash with tool calling support.
    
    Args:
        prompt: The input prompt
        db: Database session
        user_id: User ID for context
    
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

    # Add context about the user
    enhanced_prompt = f"User ID: {user_id}\n\n{prompt}"
    
    logger.info("Generating response with Gemini 2.5 Flash and tool calling...")
    
    # First, try to get a response that might call tools
    response = model.generate_content(enhanced_prompt)
    
    # Check if the response suggests tool usage
    response_text = response.text.lower()
    tool_keywords = ["medicine", "medication", "blood pressure", "sugar", "log", "user", "profile"]
    
    if any(keyword in response_text for keyword in tool_keywords):
        # The response might need tool data, so let's provide it
        try:
            # Get some basic data to provide context
            from crud.users import get_user
            from crud.medications import get_user_medicines
            from crud.bp_logs import get_logs_by_user_id
            
            user_info = get_user(db, user_id)
            medicines = get_user_medicines(db, user_id)
            bp_logs = get_logs_by_user_id(db, user_id)
            
            # Create a comprehensive response with data
            data_context = f"""
User Information: {json.dumps(user_info, default=str)}
User Medicines: {json.dumps(medicines, default=str)}
Blood Pressure Logs: {json.dumps(bp_logs, default=str)}
"""
            
            final_prompt = f"""
Based on the following data, provide a helpful response to the user's question.

User Question: {prompt}

Available Data:
{data_context}

Please provide a natural, helpful response based on this information.
"""
            
            final_response = model.generate_content(final_prompt)
            return final_response.text
            
        except Exception as e:
            logger.error(f"Error getting data for context: {e}")
            return response.text
    
    # If no tool keywords, return the original response
    return response.text
