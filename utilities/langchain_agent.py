from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from utilities.langchain_tools import ALL_TOOLS, set_tool_context
from constants.systemPrompt import system_prompt
import os

# Gemini 2.5 Flash LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0.2,
    convert_system_message_to_human=True,
)

# Bind the tools to the model
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Create a prompt template with system message
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# Agent setup using the new recommended method
agent = create_tool_calling_agent(llm_with_tools, ALL_TOOLS, prompt)

# Create the AgentExecutor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=ALL_TOOLS, 
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10
)

def run_langchain_agent(user_message: str, db, user_id: int, **kwargs):
    """
    Run the LangChain agent with the given user message, db session, and user_id.
    Returns the agent's response (string).
    """
    try:
        set_tool_context(db, user_id)
        result = agent_executor.invoke({
            "input": user_message,
            **kwargs
        })
        return result.get("output", "I couldn't process your request. Please try again.")
    except Exception as e:
        print(f"Agent execution error: {e}")
        return f"I encountered an error while processing your request: {str(e)}" 