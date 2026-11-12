# NexTrip API Reference

This document covers both the NexTrip application endpoints and the external provider endpoints used by the backend tools.

## NexTrip Application APIs

The backend runs on port `8000` by default and mounts these routes under `/api` unless noted otherwise.

### `GET /`

Returns basic service information.

#### Response

```json
{
  "message": "NexTrip API",
  "docs": "/docs"
}
```

### `GET /api/health`

Checks whether the backend process is responding. This endpoint does not call the AI model or external travel providers.

#### Response

```json
{
  "status": "ok"
}
```

### `POST /api/plan-trip`

Creates a trip plan using the requested travel details.

#### Request body

```json
{
  "from_location": "New Delhi",
  "to_location": "Mumbai",
  "travel_date": "2026-09-01",
  "num_days": 3,
  "return_date": "2026-09-04",
  "adults": 1,
  "cabin_class": "economy",
  "currency": "INR",
  "include_hotels": true,
  "include_rentals": false,
  "country_of_residence": "in"
}
```

`from_location`, `to_location`, and `travel_date` are required. The remaining fields have defaults defined by the backend request model.

#### Successful response

```json
{
  "status": "success",
  "result": {},
  "itinerary": {
    "destination": "Mumbai",
    "num_days": 3,
    "places": [],
    "days": [
      {
        "day": 1,
        "date": "2026-09-01",
        "title": "Colaba & Fort",
        "slots": [
          {
            "start_time": "09:00",
            "end_time": "11:00",
            "place": "Gateway of India",
            "area": "Colaba",
            "notes": "Iconic waterfront landmark.",
            "kind": "place"
          }
        ]
      }
    ],
    "error": null
  },
  "error": null
}
```

The `result` value contains the agent-generated plan and provider data. Its exact contents depend on the tools selected for the request.

The `itinerary` value contains the structured places plan. The backend extracts about twice as many places as the number of requested days, then asks Gemini to assign the places to days while grouping nearby stops. Each day is scheduled into time slots from 09:00 with travel buffers and a lunch break. If fewer places are available than requested days, a day is returned with no slots and a free-day title.

If the planning agent fails or times out but the itinerary succeeds, the endpoint returns `200` with `status: "partial"`, the agent error in `error`, and the itinerary in `itinerary`.

#### Error responses

- `422` — request validation failed.
- `503` — `GOOGLE_API_KEY` is not configured.
- `500` — an unexpected error occurred before either task completed.

## External Provider APIs

All provider credentials must be supplied through environment variables. No API key should be stored in this file or committed to source control.

- RapidAPI integrations read `RAPID_API_KEY` or `RAPIDAPI_KEY`.
- Weatherstack reads `WEATHER_STACK_API`.
- DuckDuckGo places search requires no API key.

The backend sends credentials in request headers or query parameters as required by each provider.

## 1. Train Search

Provider host: `rail-info-api-india1.p.rapidapi.com`

### Search stations

```http
GET https://rail-info-api-india1.p.rapidapi.com/v1/stations/search
```

Query parameters used by the backend:

| Parameter | Description |
|---|---|
| `q` | Station or location name to search |

The backend searches both locations, selects station results, and extracts station codes.

### Search trains between stations

```http
GET https://rail-info-api-india1.p.rapidapi.com/v1/trains/between
```

Query parameters:

| Parameter | Description |
|---|---|
| `from` | Departure station code |
| `to` | Destination station code |
| `via` | Optional intermediate station code |

The response contains train identifiers, names, station details, times, distance, and stop information.

## 2. Flight Search

Provider host: `sky-scrapper.p.rapidapi.com`

### Search airports

```http
GET https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport
```

Query parameters:

| Parameter | Description |
|---|---|
| `query` | Departure or destination location |
| `locale` | Locale used for the search; the backend defaults to `en-US` |

The backend extracts `skyId` and `entityId` from the first matching airport.

### Search flights

```http
GET https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlights
```

Query parameters:

| Parameter | Description |
|---|---|
| `originSkyId` | Origin airport Sky ID |
| `destinationSkyId` | Destination airport Sky ID |
| `originEntityId` | Origin airport entity ID |
| `destinationEntityId` | Destination airport entity ID |
| `date` | Travel date in `YYYY-MM-DD` format |
| `cabinClass` | Cabin class, such as `economy` |
| `adults` | Number of adults |
| `sortBy` | Result ordering; backend default is `best` |
| `currency` | Display currency; backend default is `INR` |
| `market` | Market locale; backend default is `en-US` |
| `countryCode` | Market country; backend default is `US` |

## 3. Bus Search

Provider host: `flixbus2.p.rapidapi.com`

### Autocomplete bus stations

```http
GET https://flixbus2.p.rapidapi.com/autocomplete
```

Query parameters:

| Parameter | Description |
|---|---|
| `query` | Departure or destination location |
| `locale` | Search locale; backend default is `en` |

The backend extracts a station identifier from the first result.

### Search bus trips

```http
GET https://flixbus2.p.rapidapi.com/trips
```

Query parameters:

| Parameter | Description |
|---|---|
| `from_id` | Departure station identifier |
| `to_id` | Destination station identifier |
| `date` | Travel date |
| `adult` | Number of adults |

## 4. Hotel Search

Provider host: `booking-com15.p.rapidapi.com`

### Search hotel destination

```http
GET https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination
```

Query parameters:

| Parameter | Description |
|---|---|
| `query` | Destination name |

The backend uses the first destination result and extracts its `dest_id`.

### Search hotels

```http
GET https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels
```

Query parameters used by the backend:

| Parameter | Description |
|---|---|
| `dest_id` | Destination identifier |
| `search_type` | Search type; backend default is `CITY` |
| `adults` | Number of adults |
| `children_age` | Child age values; backend default is `0,17` |
| `room_qty` | Number of rooms |
| `page_number` | Result page |
| `units` | Unit system; backend default is `metric` |
| `temperature_unit` | Temperature unit; backend default is `c` |
| `languagecode` | Response language; backend default is `en-us` |
| `currency_code` | Display currency; backend default is `INR` |
| `location` | Provider location context |
| `arrival_date` | Optional arrival date |
| `departure_date` | Optional departure date |

## 5. Car Rental Search

Provider host: `booking-com15.p.rapidapi.com`

### Search pickup destination

```http
GET https://booking-com15.p.rapidapi.com/api/v2/cars/searchDestination
```

Query parameters:

| Parameter | Description |
|---|---|
| `term` | Pickup location, such as an airport or railway station |
| `countryOfResidence` | Customer country; backend default is `us` |

The backend extracts latitude and longitude from the first matching location.

### Search car rentals

```http
GET https://booking-com15.p.rapidapi.com/api/v2/cars/searchCarRentals
```

Query parameters:

| Parameter | Description |
|---|---|
| `pick_up_latitude` | Pickup latitude |
| `pick_up_longitude` | Pickup longitude |
| `pick_up_date` | Pickup date |
| `pick_up_time` | Pickup time |
| `drop_off_date` | Drop-off date |
| `drop_off_time` | Drop-off time |
| `countryOfResidence` | Customer country |

## 6. Weather

Provider: Weatherstack

### Current weather

```http
GET http://api.weatherstack.com/current
```

Query parameters:

| Parameter | Description |
|---|---|
| `access_key` | Loaded from `WEATHER_STACK_API` |
| `query` | Destination name |
| `units` | Unit system; backend default is `m` |
| `language` | Response language; backend default is `en` |

The backend returns the provider's current-weather response for the requested location.

## 7. Places to Visit Search

Provider: DuckDuckGo (through `langchain_community` and the `ddgs` package)

The places tool needs no endpoint configuration or credentials. The backend searches the web using the query format `top 10 places to visit in <destination>` and returns the search results together with the destination and query used. The agent uses this tool to include recommended places in the final trip plan.
