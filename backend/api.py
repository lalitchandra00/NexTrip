import os
import asyncio
from functools import partial

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from schemas import TripRequest, TripResponse
from agents.trip_agent import create_nextrip_agent

load_dotenv()

router = APIRouter()

def _ensure_llm_ready():
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY is not set. Add it to backend/.env and restart the server.",
        )


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest):
    _ensure_llm_ready()
    try:
        agent = create_nextrip_agent()
        query_parts = [
            f"Plan a trip from {request.from_location} to {request.to_location}",
            f"on {request.travel_date} for {request.num_days} days",
            f"with {request.adults} adults, cabin class {request.cabin_class}, currency {request.currency}"
        ]
        if request.return_date:
            query_parts.append(f"return date {request.return_date}")
        if request.include_hotels:
            query_parts.append("Find suitable hotels at destination")
        if request.include_rentals:
            query_parts.append("Find car rentals")
        query_parts.append("Find transportation options (trains/flights/buses) and weather information")
        
        query = ". ".join(query_parts) + "."
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, partial(agent.invoke, {"input": query})),
            timeout=120.0  # 2-minute timeout
        )
        return TripResponse(status="success", result=result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out after 120 seconds. Try a simpler query.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
