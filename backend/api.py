from fastapi import APIRouter, HTTPException
from schemas import TripRequest, TripResponse
from agents.trip_agent import create_nextrip_agent

router = APIRouter()


@router.post("/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest):
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
        result = agent.invoke({"input": query})
        return TripResponse(status="success", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok"}
