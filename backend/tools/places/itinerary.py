# Day-by-day itinerary builder for places to visit
import html as html_lib
import math
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from tools.places.places import run_places_search

MAX_PLACES_PER_DAY = 3
DEFAULT_START_MINUTE = 9 * 60
LUNCH_START_MINUTE = 13 * 60
LUNCH_END_MINUTE = 13 * 60 + 30
DAY_END_MINUTE = 21 * 60


class ExtractedPlace(BaseModel):
    name: str
    area: str = ""
    duration_minutes: int = 120
    description: str = ""


class ExtractedPlaces(BaseModel):
    places: List[ExtractedPlace] = Field(default_factory=list)


class PlannedDay(BaseModel):
    day: int
    place_names: List[str] = Field(default_factory=list)


class DayAssignments(BaseModel):
    days: List[PlannedDay] = Field(default_factory=list)


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
        request_timeout=float(os.getenv("LLM_REQUEST_TIMEOUT", "30")),
        retries=int(os.getenv("LLM_MAX_RETRIES", "1")),
    )


def _clean_name(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"^\s*(?:\d+[\.\)]|[-*•])\s*", "", value)
    value = re.split(r"\s[–—-]\s", value)[0]
    value = re.split(r"[.;:?|,/]", value)[0]
    value = re.sub(
        r"^(?:including|include|such as|like|and|or|must[- ]visit)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\s+", " ", value).strip(" ,.-")
    return value


BLOCKED_FIRST_WORDS = {
    "explore", "visit", "these", "this", "final", "top", "best", "staying",
    "from", "with", "there", "here", "you", "your", "find", "book", "quick",
    "full", "see", "things", "tour", "whether", "located", "named",
    "popular", "must", "the", "a", "an", "those", "travel", "related",
    "recommended", "insider", "getting", "practical", "tips", "guide",
    "overview", "conclusion", "faq", "how", "when", "where", "what", "why",
    "go", "get", "be", "take", "dine", "check", "kill", "immerse", "retail",
    "shop", "eat", "drink", "stay", "enjoy", "discover", "experience",
    "wander", "stroll", "relax", "watch", "learn", "make", "meet", "try",
    "sample", "hire", "rent", "buy", "catch", "hop", "ride", "walk", "avoid",
    "skip", "plan", "pack", "bring", "keep", "use", "head", "start", "finish",
    "end",
}

BLOCKED_PHRASES = {
    "find book", "best things", "things to", "top rated", "must see", "must visit",
    "quick easy", "full refund", "tour categories", "cultural experiences",
    "city tours", "adventure activities", "see tripadvisor", "these rankings",
    "located in", "named after", "from historic", "whether you", "traveler reviews",
    "tourist attractions", "popular places", "best tourist", "best places",
}

BLOCKED_LAST_WORDS = {
    "tours", "activities", "experiences", "attractions", "places", "things",
    "safari", "camping", "boating", "trekking",
}

PLACE_SUFFIXES = {
    "beach", "temple", "fort", "cave", "caves", "park", "garden", "gardens",
    "museum", "market", "terminus", "station", "causeway", "link", "drive",
    "face", "district", "island", "lake", "palace", "mosque", "church",
    "dargah", "zoo", "aquarium", "stadium", "bridge", "point", "hill",
    "waterfall", "sanctuary", "tower", "gate", "memorial", "monument",
    "square", "promenade", "street", "road", "chowk", "pier", "port", "bay",
    "coast", "valley", "reserve", "observatory", "planetarium", "gallery",
    "theatre", "theater", "auditorium", "mall", "bazaar", "village", "creek",
    "river", "dam", "lighthouse", "masjid", "gurudwara", "monastery", "ruins",
    "tomb", "cemetery",
}


def _looks_like_place(name: str, destination: str = "") -> bool:
    words = name.split()
    if not (2 <= len(words) <= 7):
        return False
    lowered = name.lower()
    first = words[0].lower()
    if first in BLOCKED_FIRST_WORDS:
        return False
    if destination and first == destination.strip().lower():
        return False
    if bool(set(re.findall(r"\d", name))):
        return False
    if lowered in BLOCKED_PHRASES:
        return False
    if " ".join(word.lower() for word in words[:2]) in BLOCKED_PHRASES:
        return False
    if words[-1].lower() in BLOCKED_LAST_WORDS:
        return False
    return True


CONNECTOR_WORDS = {
    "of", "the", "and", "&", "de", "del", "da", "di", "van", "von", "la",
    "le", "at", "in", "on",
}


def _looks_like_proper_place(name: str) -> bool:
    words = name.split()
    if not words:
        return False
    for word in words:
        if word.lower() in CONNECTOR_WORDS:
            continue
        if not word[:1].isupper():
            return False
    return True


def _is_place_heading(text: str, name: str, destination: str) -> bool:
    if not re.match(r"^\s*\d+[\.\)]\s+", text):
        return False
    if not _looks_like_place(name, destination):
        return False
    return _looks_like_proper_place(name)


def _heuristic_extract(text: str, limit: int) -> List[ExtractedPlace]:
    candidates: List[str] = []

    for line in text.splitlines():
        match = re.match(r"^\s*(?:\d+[\.\)]|[-*•])\s+(.{3,80})$", line)
        if match:
            candidates.append(match.group(1))

    for match in re.finditer(
        r"(?:include|including|such as|popular places)[^.]{3,240}",
        text,
        re.IGNORECASE,
    ):
        for part in re.split(r",| and | to ", match.group(0)):
            candidates.append(part)

    for match in re.finditer(
        r"\b([A-Z][a-zA-Z'’&.-]+(?:\s+(?:of|the|and|&|[A-Z][a-zA-Z'’&.-]+)){1,5})\b",
        text,
    ):
        candidates.append(match.group(1))

    places: List[ExtractedPlace] = []
    seen = set()
    for candidate in candidates:
        name = _clean_name(candidate)
        if not _looks_like_place(name) or not _looks_like_proper_place(name):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        places.append(ExtractedPlace(name=name))
        if len(places) >= limit:
            break
    return places


def _fetch_page_places(destination: str, limit: int) -> List[ExtractedPlace]:
    try:
        from tools.places.places import search_tool

        results = search_tool.api_wrapper.results(
            f"top 10 places to visit in {destination}", max_results=8
        )
    except Exception:
        return []

    places: List[ExtractedPlace] = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NexTrip/1.0)"}
    for result in results[:5]:
        link = result.get("link")
        if not link:
            continue
        try:
            response = requests.get(link, timeout=8, headers=headers)
            response.raise_for_status()
        except Exception:
            continue

        for tag in ("h2", "h3"):
            headings = re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", response.text, re.S | re.I)
            for heading in headings:
                text = re.sub(r"<[^>]+>", " ", heading)
                text = html_lib.unescape(text)
                text = re.sub(r"\s+", " ", text).strip()
                name = _clean_name(text)
                if not _is_place_heading(text, name, destination):
                    continue
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                places.append(ExtractedPlace(name=name))
                if len(places) >= limit:
                    return places
    return places


def extract_places(
    destination: str, search_text: str, target: int
) -> Tuple[List[ExtractedPlace], bool]:
    places: List[ExtractedPlace] = []
    used_llm = False
    try:
        structured_llm = _get_llm().with_structured_output(ExtractedPlaces)
        prompt = (
            f"Extract the distinct tourist places worth visiting in {destination} "
            f"from the search results below. Return up to {target} places. "
            "For each place include its name, the area or neighborhood if known, "
            "an estimated visit duration in minutes between 60 and 240, and a one-line description. "
            "Only use places mentioned in the text. Do not invent places.\n\n"
            f"Search results:\n{search_text}"
        )
        parsed = structured_llm.invoke(prompt)
        used_llm = True
        if isinstance(parsed, ExtractedPlaces):
            places = list(parsed.places)
        elif isinstance(parsed, dict):
            places = [ExtractedPlace(**item) for item in parsed.get("places", [])]
    except Exception:
        places = []

    if len(places) < target:
        places.extend(_fetch_page_places(destination, target))
    if len(places) < min(target, 3):
        places.extend(_heuristic_extract(search_text, target))

    deduped: List[ExtractedPlace] = []
    seen = set()
    for place in places:
        name = _clean_name(place.name)
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        place.name = name
        place.area = (place.area or "").strip()
        try:
            duration = int(place.duration_minutes or 120)
        except (TypeError, ValueError):
            duration = 120
        place.duration_minutes = max(45, min(240, duration))
        place.description = (place.description or "").strip()
        deduped.append(place)
    return deduped[:target], used_llm


def _llm_assign_days(
    destination: str, places: List[ExtractedPlace], num_days: int
) -> Optional[List[List[ExtractedPlace]]]:
    if not places or num_days <= 0:
        return None

    per_day = max(1, min(MAX_PLACES_PER_DAY, math.ceil(len(places) / num_days)))
    place_lines = []
    for index, place in enumerate(places, 1):
        details = f"{index}. {place.name}"
        if place.area:
            details += f" | area: {place.area}"
        if place.duration_minutes:
            details += f" | suggested minutes: {place.duration_minutes}"
        place_lines.append(details)

    prompt = (
        f"You are planning a {num_days}-day trip to {destination}.\n"
        f"Here are {len(places)} places:\n" + "\n".join(place_lines) + "\n\n"
        f"Assign every place to exactly one day across days 1 to {num_days}. "
        f"Use at most {MAX_PLACES_PER_DAY} places per day and aim for about {per_day} per day. "
        "Group places in the same area or neighborhood on the same day to reduce travel. "
        "Keep the place names exactly as listed."
    )

    try:
        planner = _get_llm().with_structured_output(DayAssignments)
        parsed = planner.invoke(prompt)
    except Exception:
        return None

    if isinstance(parsed, dict):
        try:
            parsed = DayAssignments(**parsed)
        except Exception:
            return None
    if not isinstance(parsed, DayAssignments):
        return None

    by_name = {_clean_name(place.name).lower(): place for place in places}
    assigned: List[List[ExtractedPlace]] = [[] for _ in range(num_days)]
    seen = set()
    for planned in parsed.days:
        index = max(0, min(num_days - 1, int(planned.day) - 1))
        for raw_name in planned.place_names:
            key = _clean_name(raw_name).lower()
            place = by_name.get(key)
            if place is None or key in seen:
                continue
            if len(assigned[index]) >= MAX_PLACES_PER_DAY:
                continue
            assigned[index].append(place)
            seen.add(key)

    if not any(assigned):
        return None

    leftovers = [place for place in places if _clean_name(place.name).lower() not in seen]
    for place in leftovers:
        candidates = [index for index in range(num_days) if len(assigned[index]) < MAX_PLACES_PER_DAY]
        if not candidates:
            candidates = list(range(num_days))
        index = min(candidates, key=lambda item: len(assigned[item]))
        assigned[index].append(place)

    return assigned


def _chunks(items: List[ExtractedPlace], size: int) -> List[List[ExtractedPlace]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _assign_days(places: List[ExtractedPlace], num_days: int) -> List[List[ExtractedPlace]]:
    if num_days <= 0:
        return []
    if not places:
        return [[] for _ in range(num_days)]

    per_day = max(1, min(MAX_PLACES_PER_DAY, round(len(places) / num_days)))
    grouped: Dict[str, List[ExtractedPlace]] = {}
    order: List[str] = []
    for place in places:
        area = place.area.strip().lower() or "city center"
        if area not in grouped:
            grouped[area] = []
            order.append(area)
        grouped[area].append(place)

    buckets: List[List[ExtractedPlace]] = []
    for area in order:
        buckets.extend(_chunks(grouped[area], per_day))

    days: List[List[ExtractedPlace]] = [[] for _ in range(num_days)]
    day_areas = [set() for _ in range(num_days)]

    def assign_one(place: ExtractedPlace, area: str) -> None:
        candidates = [index for index in range(num_days) if len(days[index]) < MAX_PLACES_PER_DAY]
        if not candidates:
            candidates = list(range(num_days))
        index = min(
            candidates,
            key=lambda item: (
                0 if area and area in day_areas[item] else 1,
                len(days[item]),
            ),
        )
        days[index].append(place)
        if area:
            day_areas[index].add(area)

    for bucket in buckets:
        area = bucket[0].area.strip().lower() if bucket else ""
        candidates = [
            index for index in range(num_days)
            if len(days[index]) + len(bucket) <= MAX_PLACES_PER_DAY
        ]
        same_area = [index for index in candidates if area and area in day_areas[index]]
        if same_area:
            index = min(same_area, key=lambda item: len(days[item]))
            days[index].extend(bucket)
            day_areas[index].add(area)
        elif candidates:
            index = min(candidates, key=lambda item: len(days[item]))
            days[index].extend(bucket)
            if area:
                day_areas[index].add(area)
        else:
            for place in bucket:
                assign_one(place, area)

    return days


def _format_time(minutes: int) -> str:
    minutes = max(0, minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _build_slots(places: List[ExtractedPlace]) -> List[Dict[str, Any]]:
    slots: List[Dict[str, Any]] = []
    current = DEFAULT_START_MINUTE
    lunch_done = False
    previous_area = ""

    for place in places:
        duration = max(45, min(240, int(place.duration_minutes or 120)))
        start = current
        end = min(start + duration, DAY_END_MINUTE)
        if start >= DAY_END_MINUTE or end <= start:
            break
        slots.append({
            "start_time": _format_time(start),
            "end_time": _format_time(end),
            "place": place.name,
            "area": place.area,
            "notes": place.description,
            "kind": "place",
        })

        area = place.area.strip().lower()
        same_area = bool(area) and area == previous_area
        travel = 15 if same_area else 30
        current = end + travel

        if not lunch_done and end >= LUNCH_START_MINUTE:
            lunch_start = max(end, LUNCH_START_MINUTE)
            lunch_end = lunch_start + (LUNCH_END_MINUTE - LUNCH_START_MINUTE)
            slots.append({
                "start_time": _format_time(lunch_start),
                "end_time": _format_time(lunch_end),
                "place": "Lunch break",
                "area": "",
                "notes": "Recharge before the next stop.",
                "kind": "break",
            })
            current = lunch_end + travel
            lunch_done = True

        previous_area = area
        if current >= DAY_END_MINUTE:
            break

    return slots


def _day_dates(travel_date: Optional[str], num_days: int) -> List[Optional[str]]:
    try:
        start = datetime.strptime(travel_date, "%Y-%m-%d")
        return [(start + timedelta(days=index)).strftime("%Y-%m-%d") for index in range(num_days)]
    except (TypeError, ValueError):
        return [None] * num_days


def build_places_itinerary(destination: str, num_days: int, travel_date: Optional[str] = None) -> Dict[str, Any]:
    """Find places at the destination and build a day-by-day itinerary with time slots."""
    num_days = max(1, min(30, int(num_days or 1)))
    target = min(30, num_days * MAX_PLACES_PER_DAY, max(num_days * 2, num_days + 3))

    queries = [
        f"top {target} places to visit in {destination}",
        f"best tourist attractions and things to do in {destination}",
    ]

    texts: List[str] = []
    errors: List[str] = []
    for query in queries:
        result = run_places_search(query)
        if result.get("error"):
            errors.append(result["error"])
        elif result.get("results"):
            texts.append(str(result["results"]))

    search_text = "\n\n".join(texts)
    if not search_text:
        return {
            "destination": destination,
            "num_days": num_days,
            "places": [],
            "days": [],
            "error": "; ".join(errors) or "No places found",
        }

    places, used_llm = extract_places(destination, search_text, target)

    assigned: Optional[List[List[ExtractedPlace]]] = None
    if used_llm:
        assigned = _llm_assign_days(destination, places, num_days)
    if not assigned:
        assigned = _assign_days(places, num_days)

    dates = _day_dates(travel_date, num_days)

    days: List[Dict[str, Any]] = []
    for index, day_places in enumerate(assigned):
        areas = []
        for place in day_places:
            area = place.area.strip()
            if area and area not in areas:
                areas.append(area)
        if areas:
            title = " & ".join(areas)
        elif day_places:
            title = f"Explore {destination}"
        else:
            title = "Free day / explore at leisure"
        days.append({
            "day": index + 1,
            "date": dates[index],
            "title": title,
            "slots": _build_slots(day_places),
        })

    warning = None
    if len(places) < num_days:
        warning = (
            f"Only {len(places)} place(s) could be extracted, so some days are free. "
            "Try again when the AI model is available for a fuller plan."
        )

    return {
        "destination": destination,
        "num_days": num_days,
        "places": [place.model_dump() for place in places],
        "days": days,
        "error": warning,
    }
