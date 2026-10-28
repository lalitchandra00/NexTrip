# NexTrip Main Agent
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

from tools.toolkit import get_all_tools

REACT_PROMPT = PromptTemplate.from_template("""You are a helpful AI trip planner assistant.

Your task is to plan trips by finding transportation, hotels, rentals, and weather information.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input

Question: {input}
Thought:{agent_scratchpad}""")


def create_nextrip_agent():
    """Create the NexTrip ReAct agent using Gemini."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        # max_tokens=20,
    )
    tools = get_all_tools()
    agent = create_react_agent(llm, tools, REACT_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    return agent_executor


def plan_trip(from_location: str, to_location: str, travel_date: str, num_days: int = 1):
    """Plan a trip with transportation, hotels, etc."""
    agent = create_nextrip_agent()
    query = f"Plan a trip from {from_location} to {to_location} on {travel_date} for {num_days} days. Find transportation options, hotels, and weather."
    result = agent.invoke({"input": query})
    return result
