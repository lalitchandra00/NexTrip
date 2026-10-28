# NexTrip Backend

This directory contains the backend service that receives trip-planning requests, coordinates the AI agent, and exposes the NexTrip HTTP API.

## Technical Approach

### Application entry point

[`main.py`](./main.py) creates the FastAPI application, enables permissive CORS for the current client integration, and mounts the API router under `/api`.

The application also exposes a root endpoint that identifies the service and links to the interactive API documentation.

### Request and response models

[`schemas.py`](./schemas.py) defines the API contract:

- `TripRequest` contains the departure, destination, dates, traveler count, cabin class, currency, and optional hotel/rental preferences.
- `TripResponse` wraps the planner result with a status and optional error field.

FastAPI and Pydantic validate incoming JSON before the planning workflow runs.

### AI planning agent

[`agents/trip_agent.py`](./agents/trip_agent.py) builds a ReAct-style LangChain agent. The agent:

1. Receives the normalized trip request as a natural-language planning prompt.
2. Selects from the available travel tools.
3. Calls tools for transportation, hotels, rentals, and weather as needed.
4. Uses the tool observations to produce the final trip-planning response.

The backend uses the configured `ChatGoogleGenerativeAI` Gemini model as the only language model. The Google credential is read from `GOOGLE_API_KEY`.

### Tool orchestration

[`tools/toolkit.py`](./tools/toolkit.py) gathers all domain tools into the agent tool list:

- Train search
- Flight search
- Bus search
- Hotel search
- Car rental search
- Weather lookup

Each tool is isolated in its domain module and returns JSON-compatible dictionaries. HTTP failures from provider calls are surfaced through `requests` exceptions rather than silently converted into successful results.

### External service integrations

The domain modules under [`tools/`](./tools/) call external travel services:

- RapidAPI rail service for stations and trains
- RapidAPI Sky Scrapper for airports and flights
- RapidAPI FlixBus for bus stations and trips
- RapidAPI Booking.com services for destinations, hotels, and car rentals
- Weatherstack for current weather

Provider credentials are loaded from environment variables. RapidAPI integrations use `RAPID_API_KEY` or `RAPIDAPI_KEY`; weather uses `WEATHER_STACK_API`; Gemini uses `GOOGLE_API_KEY`.

See [`apis.md`](./apis.md) for the application endpoints and the complete provider endpoint reference.

### Trip request workflow

The `/api/plan-trip` handler:

1. Verifies that `GOOGLE_API_KEY` is configured.
2. Builds a planning prompt from the request fields.
3. Creates the agent and invokes it with the prompt.
4. Returns the agent result in a `TripResponse`.

The `/api/health` handler provides a lightweight service availability check without calling external providers.

### Configuration and execution

Dependencies are maintained in the repository-level [`requirements.txt`](../requirements.txt). The backend expects environment variables to be supplied through the runtime environment or a local `.env` file.

From this directory, the service can be started with:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The interactive OpenAPI documentation is available at `/docs` when the service is running.
