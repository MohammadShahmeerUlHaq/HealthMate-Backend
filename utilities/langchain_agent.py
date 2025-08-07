# from langchain.agents import create_tool_calling_agent, AgentExecutor
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.tools import Tool
# from utilities.langchain_tools import ALL_TOOLS
# from constants.systemPrompt import system_prompt
# import os

# # Gemini LLM setup
# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     google_api_key=os.environ.get("GEMINI_API_KEY"),
#     temperature=0.2,
# )

# # Bind the tools to the model
# llm_with_tools = llm.bind_tools(ALL_TOOLS)

# # Create a prompt template. Note the use of `MessagesPlaceholder` for the agent's scratchpad.
# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", system_prompt),
#         MessagesPlaceholder("chat_history", optional=True),
#         ("human", "{input}"),
#         MessagesPlaceholder("agent_scratchpad"),
#     ]
# )

# # Agent setup using the new recommended method
# agent = create_tool_calling_agent(llm_with_tools, ALL_TOOLS, prompt)

# # Create the AgentExecutor
# agent_executor = AgentExecutor(agent=agent, tools=ALL_TOOLS, verbose=True)

# def run_langchain_agent(user_message: str, db, user_id: int, **kwargs):
#     """
#     Run the LangChain agent with the given user message, db session, and user_id.
#     Returns the agent's response (string).
#     """
#     # The `db` and `user_id` are passed as part of the input dictionary.
#     # The `AgentExecutor` will automatically pass them to the tools as needed.
#     return agent_executor.invoke({
#         "input": user_message,
#         "db": db,
#         "user_id": user_id,
#         **kwargs
#     })

from langchain.agents import initialize_agent, AgentType
# from langchain.llms import GoogleGenerativeAI
from langchain_google_genai import ChatGoogleGenerativeAI as GoogleGenerativeAI
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
from langchain.tools import Tool
from utilities.langchain_tools import ALL_TOOLS
from constants.systemPrompt import system_prompt
import os

# Gemini LLM setup
llm = GoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0.2,
)

# System prompt as a true system message
system_prompt_template = SystemMessagePromptTemplate.from_template(system_prompt)

# Agent setup
agent = initialize_agent(
    tools=ALL_TOOLS,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    system_message=system_prompt_template,
)

def run_langchain_agent(user_message: str, db, user_id: int, **kwargs):
    """
    Run the LangChain agent with the given user message, db session, and user_id.
    Returns the agent's response (string).
    """
    # Pass db and user_id as part of the tool input context
    # The agent will call tools as needed
    return agent.run(user_message, db=db, user_id=user_id, **kwargs) 