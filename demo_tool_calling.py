#!/usr/bin/env python3
"""
Demo script for Gemini 2.5 Flash Tool Calling - Presentation Ready
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utilities.gemini_tool_calling import generate_response_with_tools
from database import get_db

def demo_gemini_tool_calling():
    """Demo Gemini 2.5 Flash tool calling capabilities"""
    print("🚀 HealthMate AI Assistant - Gemini 2.5 Flash Tool Calling Demo")
    print("=" * 70)
    print()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Demo 1: Medicine Information
        print("📋 Demo 1: Medicine Information")
        print("-" * 40)
        question1 = "What medicines are prescribed to user 1?"
        print(f"User Question: {question1}")
        print()
        
        response1 = generate_response_with_tools(question1, db=db, user_id=1)
        print(f"AI Response: {response1}")
        print()
        
        # Demo 2: Health Logs
        print("📊 Demo 2: Health Logs")
        print("-" * 40)
        question2 = "Show me the blood pressure logs for user 1"
        print(f"User Question: {question2}")
        print()
        
        response2 = generate_response_with_tools(question2, db=db, user_id=1)
        print(f"AI Response: {response2}")
        print()
        
        # Demo 3: User Profile
        print("👤 Demo 3: User Profile")
        print("-" * 40)
        question3 = "What is the profile information for user 1?"
        print(f"User Question: {question3}")
        print()
        
        response3 = generate_response_with_tools(question3, db=db, user_id=1)
        print(f"AI Response: {response3}")
        print()
        
        # Demo 4: Complex Query
        print("🔍 Demo 4: Complex Health Query")
        print("-" * 40)
        question4 = "Can you analyze the health data for user 1 and provide insights?"
        print(f"User Question: {question4}")
        print()
        
        response4 = generate_response_with_tools(question4, db=db, user_id=1)
        print(f"AI Response: {response4}")
        print()
        
        print("=" * 70)
        print("✅ Demo completed successfully!")
        print("🎯 Key Features Demonstrated:")
        print("   • Direct database integration")
        print("   • Natural language processing")
        print("   • Contextual health data analysis")
        print("   • Real-time tool calling")
        print("   • Gemini 2.5 Flash capabilities")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main demo function"""
    load_dotenv()
    
    # Check if API key is available
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in environment variables.")
        print("Please set your Gemini API key in the .env file.")
        return False
    
    try:
        demo_gemini_tool_calling()
        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    main()
