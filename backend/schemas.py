from pydantic import BaseModel
from typing import Optional, Any


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


class TripResponse(BaseModel):
    status: str
    result: Any = None
    error: Optional[str] = None
