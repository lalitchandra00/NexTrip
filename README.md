# NexTrip

NexTrip is an AI-powered trip planner that helps travelers explore and organize a journey from one place to another.

## What NexTrip Does

NexTrip brings together the information a traveler needs when planning a trip:

- Transportation options by train, flight, and bus
- Hotel recommendations at the destination
- Optional car rental suggestions
- Current weather information for the destination
- Trip details based on travel dates, number of days, travelers, cabin class, and preferred currency

The planner accepts a starting location, destination, and travel details, then produces a consolidated trip plan. Travelers can choose whether hotels and car rentals should be included.

## Typical Trip-Planning Flow

1. Enter the departure location and destination.
2. Select the travel date and, optionally, a return date.
3. Choose the number of days and number of adults.
4. Select a cabin class and display currency.
5. Choose whether to include hotels and car rentals.
6. Submit the request to receive transportation, accommodation, rental, and weather information.

## Travel Options

### Trains

NexTrip looks for railway stations near the requested locations and returns train options between the selected stations.

### Flights

NexTrip finds relevant airports for the departure and destination locations and uses them to search available flights for the selected date and cabin class.

### Buses

NexTrip searches for bus stations near both locations and returns available bus trips for the requested date and number of adults.

### Hotels

NexTrip finds the destination and presents available hotels using the selected arrival and departure dates, number of adults, and currency.

### Car Rentals

When enabled, NexTrip finds the requested pickup location and presents rental options for the selected pickup and drop-off schedule.

### Weather

NexTrip includes current weather information for the destination to help travelers prepare for the journey.

## Result

The completed trip plan is shown as a structured response containing the requested travel recommendations and supporting information. If a service cannot find suitable results, the response identifies the affected category so the traveler can adjust the request.