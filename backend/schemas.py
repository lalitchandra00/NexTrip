from pydantic import BaseModel, Field
from typing import Optional, Any, List


class TripRequest(BaseModel):
    from_location: str
    to_location: str
    travel_date: str
    num_days: int = 1
    return_date: Optional[str] = None
    adults: int = 1
    cabin_class: str = "economy"
    currency: str = "INR"
    include_hotels: bool = True
    include_rentals: bool = False
    country_of_residence: str = "in"


class ItineraryPlace(BaseModel):
    name: str
    area: str = ""
    duration_minutes: int = 120
    description: str = ""


class ItinerarySlot(BaseModel):
    start_time: str
    end_time: str
    place: str
    area: str = ""
    notes: str = ""
    kind: str = "place"


class ItineraryDay(BaseModel):
    day: int
    date: Optional[str] = None
    title: str
    slots: List[ItinerarySlot] = Field(default_factory=list)


class ItineraryPlan(BaseModel):
    destination: str
    num_days: int
    places: List[ItineraryPlace] = Field(default_factory=list)
    days: List[ItineraryDay] = Field(default_factory=list)
    error: Optional[str] = None


class TripResponse(BaseModel):
    status: str
    result: Any = None
    itinerary: Optional[ItineraryPlan] = None
    error: Optional[str] = None
