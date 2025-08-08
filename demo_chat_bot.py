#!/usr/bin/env python3
"""
Comprehensive Demo for HealthMate Chat Bot with Gemini 2.5 Flash Tool Calling
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crud.messages import create_message_with_ai
from database import get_db
from schemas.messages import MessageCreate

def demo_chat_bot():
    """Demo the integrated chat bot with tool calling capabilities"""
    print("🚀 HealthMate AI Chat Bot - Gemini 2.5 Flash Tool Calling Demo")
    print("=" * 80)
    print()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Simulate a conversation flow
        conversation_context = ""
        
        # Demo 1: Initial Greeting
        print("👋 Demo 1: Initial Greeting")
        print("-" * 50)
        message1 = MessageCreate(
            chat_id=1,
            request="Hello! I'm feeling a bit unwell today."
        )
        
        response1 = create_message_with_ai(db, user_id=1, message=message1, message_context=conversation_context)
        print(f"User: {message1.request}")
        print(f"AI: {response1.response}")
        print()
        
        # Update conversation context
        conversation_context = f"User greeted and mentioned feeling unwell. AI responded with initial assessment."
        
        # Demo 2: Medicine Query
        print("💊 Demo 2: Medicine Query")
        print("-" * 50)
        message2 = MessageCreate(
            chat_id=1,
            request="What medicines am I currently taking? I want to make sure I'm not missing any doses."
        )
        
        response2 = create_message_with_ai(db, user_id=1, message=message2, message_context=conversation_context)
        print(f"User: {message2.request}")
        print(f"AI: {response2.response}")
        print()
        
        # Update conversation context
        conversation_context += f" User asked about current medications and adherence."
        
        # Demo 3: Blood Pressure Check
        print("🩺 Demo 3: Blood Pressure Check")
        print("-" * 50)
        message3 = MessageCreate(
            chat_id=1,
            request="Can you check my recent blood pressure readings? I'm concerned about my numbers."
        )
        
        response3 = create_message_with_ai(db, user_id=1, message=message3, message_context=conversation_context)
        print(f"User: {message3.request}")
        print(f"AI: {response3.response}")
        print()
        
        # Update conversation context
        conversation_context += f" User requested BP reading analysis due to concerns."
        
        # Demo 4: Health Advice
        print("🏥 Demo 4: Health Advice")
        print("-" * 50)
        message4 = MessageCreate(
            chat_id=1,
            request="I have a headache and some dizziness. Should I be worried?"
        )
        
        response4 = create_message_with_ai(db, user_id=1, message=message4, message_context=conversation_context)
        print(f"User: {message4.request}")
        print(f"AI: {response4.response}")
        print()
        
        # Update conversation context
        conversation_context += f" User reported headache and dizziness symptoms."
        
        # Demo 5: Data Analysis Request
        print("📊 Demo 5: Data Analysis Request")
        print("-" * 50)
        message5 = MessageCreate(
            chat_id=1,
            request="Can you analyze my overall health data and give me some insights?"
        )
        
        response5 = create_message_with_ai(db, user_id=1, message=message5, message_context=conversation_context)
        print(f"User: {message5.request}")
        print(f"AI: {response5.response}")
        print()
        
        # Demo 6: Follow-up Question
        print("❓ Demo 6: Follow-up Question")
        print("-" * 50)
        message6 = MessageCreate(
            chat_id=1,
            request="Based on my data, what should I focus on improving?"
        )
        
        response6 = create_message_with_ai(db, user_id=1, message=message6, message_context=conversation_context)
        print(f"User: {message6.request}")
        print(f"AI: {response6.response}")
        print()
        
        print("=" * 80)
        print("✅ Chat Bot Demo completed successfully!")
        print()
        print("🎯 Key Features Demonstrated:")
        print("   • Natural conversation flow")
        print("   • Real-time health data access")
        print("   • Contextual responses")
        print("   • Medical safety guidelines")
        print("   • Personalized health insights")
        print("   • Tool calling integration")
        print("   • Conversation memory")
        print()
        print("🚀 Technical Highlights:")
        print("   • Gemini 2.5 Flash model")
        print("   • Direct database integration")
        print("   • Tool calling capabilities")
        print("   • Medical safety protocols")
        print("   • Scalable architecture")
        
    except Exception as e:
        print(f"❌ Chat bot demo error: {e}")
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
        demo_chat_bot()
        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    main()
