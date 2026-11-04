import os
import asyncio
from functools import partial

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from schemas import TripRequest, TripResponse
from agents.trip_agent import create_nextrip_agent
from llm_config import model_names
from tools.places.itinerary import build_places_itinerary
from tools.transportation.summary import build_transport_summary

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
        places_target = request.num_days * 2
        query_parts.append(
            f"Find about {places_target} places to visit at the destination"
        )
        query_parts.append(
            f"Then make a {request.num_days}-day plan that assigns the places to each day, "
            "grouping nearby places together"
        )
        query_parts.append("Find weather information; transportation is handled separately")
        
        query = ". ".join(query_parts) + "."
        timeout = float(os.getenv("PLAN_TRIP_TIMEOUT", "120"))
        itinerary_timeout = float(os.getenv("ITINERARY_TIMEOUT", "90"))

        async def run_agent():
            names = model_names()
            per_attempt = max(30.0, timeout / len(names))
            last_error = None
            for model_name in names:
                try:
                    agent = create_nextrip_agent(model_name)
                    return await asyncio.wait_for(
                        asyncio.to_thread(partial(agent.invoke, {"input": query})),
                        timeout=per_attempt,
                    )
                except Exception as exc:
                    last_error = exc
            raise last_error

        async def run_itinerary():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        build_places_itinerary,
                        request.to_location,
                        request.num_days,
                        request.travel_date,
                    ),
                    timeout=itinerary_timeout,
                )
            except Exception:
                return None

        async def run_transport():
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        build_transport_summary,
                        request.from_location,
                        request.to_location,
                        request.travel_date,
                        request.num_days,
                        request.return_date,
                        request.adults,
                        request.cabin_class,
                        request.include_rentals,
                        request.country_of_residence,
                    ),
                    timeout=itinerary_timeout,
                )
            except Exception:
                return None

        result, itinerary, transport = await asyncio.gather(
            run_agent(), run_itinerary(), run_transport(), return_exceptions=True
        )
        if isinstance(itinerary, Exception):
            itinerary = None
        if isinstance(transport, Exception):
            transport = None

        if isinstance(result, Exception):
            message = "Agent timed out" if isinstance(result, asyncio.TimeoutError) else str(result)
            return TripResponse(
                status="partial",
                result={"error": message},
                itinerary=itinerary,
                transport=transport,
                error=message,
            )

        return TripResponse(
            status="success",
            result=result,
            itinerary=itinerary,
            transport=transport,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
