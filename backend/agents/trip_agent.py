# NexTrip Main Agent
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from tools.toolkit import get_all_tools

DEFAULT_MODEL = "gemini-3.6-flash"

SYSTEM_PROMPT = """You are a helpful AI trip planner assistant.

Your task is to plan trips by finding transportation, places to visit, hotels, rentals, and weather information.
Call the available tools to gather real data instead of inventing details.
Use only the tools needed for the request and pass all required arguments.
If a tool returns an error, continue with the remaining tools and mention the failure in the final plan.
Find about twice as many places as the number of trip days, then assign the places to each day, grouping nearby places together.
Finish with a concise, organized trip plan that includes the day-by-day place assignment."""

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])


def create_nextrip_agent():
    """Create the NexTrip agent using Gemini."""
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        request_timeout=float(os.getenv("LLM_REQUEST_TIMEOUT", "30")),
        retries=int(os.getenv("LLM_MAX_RETRIES", "1")),
    )
    tools = get_all_tools()
    agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=os.getenv("AGENT_VERBOSE", "false").lower() == "true",
        handle_parsing_errors=True,
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "6")),
        max_execution_time=float(os.getenv("AGENT_MAX_EXECUTION_TIME", "90")),
        early_stopping_method="force",
    )
    return agent_executor


def plan_trip(from_location: str, to_location: str, travel_date: str, num_days: int = 1):
    """Plan a trip with transportation, hotels, etc."""
    agent = create_nextrip_agent()
    query = f"Plan a trip from {from_location} to {to_location} on {travel_date} for {num_days} days. Find transportation options, hotels, and weather."
    result = agent.invoke({"input": query})
    return result
