#!/usr/bin/env python3
"""
Test script for Gemini 2.5 Flash tool calling functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utilities.gemini_tool_calling import generate_response_with_tools
from database import get_db

def test_gemini_tool_calling():
    """Test Gemini 2.5 Flash tool calling with database"""
    print("Testing Gemini 2.5 Flash tool calling with database...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test 1: Get user medicines
        print("\n--- Test 1: Get user medicines ---")
        response1 = generate_response_with_tools(
            "What medicines are prescribed to user 1?",
            db=db,
            user_id=1
        )
        print(f"Response: {response1}")
        
        # Test 2: Get blood pressure logs
        print("\n--- Test 2: Get blood pressure logs ---")
        response2 = generate_response_with_tools(
            "Show me the blood pressure logs for user 1",
            db=db,
            user_id=1
        )
        print(f"Response: {response2}")
        
        # Test 3: Get user information
        print("\n--- Test 3: Get user information ---")
        response3 = generate_response_with_tools(
            "What is the profile information for user 1?",
            db=db,
            user_id=1
        )
        print(f"Response: {response3}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_simple_gemini():
    """Test simple Gemini 2.5 Flash without tools"""
    print("\nTesting simple Gemini 2.5 Flash response...")
    
    try:
        from utilities.gemini_client import generate_gemini_response
        
        response = generate_gemini_response(
            "Hello! I'm testing Gemini 2.5 Flash. Can you confirm you're working?"
        )
        print(f"Simple Response: {response}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main test function"""
    load_dotenv()
    
    print("🚀 Testing Gemini 2.5 Flash Tool Calling")
    print("=" * 50)
    
    # Test 1: Simple Gemini response
    success1 = test_simple_gemini()
    
    # Test 2: Tool calling with database
    success2 = test_gemini_tool_calling()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed! Gemini 2.5 Flash tool calling is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return success1 and success2

if __name__ == "__main__":
    main()
