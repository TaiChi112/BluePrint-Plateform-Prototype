from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

THAI_WEEKDAYS = {
    "จันทร์": 0,
    "อังคาร": 1,
    "พุธ": 2,
    "พฤหัส": 3,
    "พฤหัสบดี": 3,
    "ศุกร์": 4,
    "เสาร์": 5,
    "อาทิตย์": 6,
}


class NLParseError(ValueError):
    pass


def parse_user_intent(text: str, timezone: str = "Asia/Bangkok") -> Dict[str, Any]:
    """Parse natural language into calendar intent.

    Returns schema:
    {
      "intent_type": "single_event" | "recurring_weekly",
      "summary": str,
      "start": ISO datetime,
      "end": ISO datetime,
      "duration_weeks": int,
      "reminder_minutes_before": int,
      "timezone": str,
      "source": "gemini" | "rule-based"
    }
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise NLParseError("Empty input")

    gemini_intent = _parse_with_gemini(cleaned, timezone)
    if gemini_intent:
        gemini_intent["source"] = "gemini"
        return gemini_intent

    rule_intent = _parse_with_rules(cleaned, timezone)
    rule_intent["source"] = "rule-based"
    return rule_intent


def build_events_from_intent(intent: Dict[str, Any], feature_type: str = "event") -> List[Dict[str, Any]]:
    start = _to_datetime(intent["start"])
    end = _to_datetime(intent["end"])
    summary = intent.get("summary", "Untitled Event")
    reminder = int(intent.get("reminder_minutes_before", 60))
    intent_type = intent.get("intent_type", "single_event")

    if intent_type == "single_event":
        return [{
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "reminders_minutes_before": reminder,
            "event_type": feature_type,
        }]

    duration_weeks = int(intent.get("duration_weeks", 1))
    events: List[Dict[str, Any]] = []
    for week in range(duration_weeks):
        event_start = start + timedelta(weeks=week)
        event_end = end + timedelta(weeks=week)
        events.append({
            "summary": f"{summary} (W{week + 1})",
            "start": event_start.isoformat(),
            "end": event_end.isoformat(),
            "reminders_minutes_before": reminder,
            "event_type": feature_type,
        })
    return events


def _parse_with_gemini(text: str, timezone: str) -> Optional[Dict[str, Any]]:
    """Parse with Gemini AI, includes retry policy and quota fallback."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[NL] ℹ️  ไม่พบ GEMINI_API_KEY → ใช้ rule-based parser")
        return None

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )

    prompt = (
        "Convert Thai/English calendar command into strict JSON only. "
        "No markdown, no explanations. "
        "JSON keys: intent_type(single_event|recurring_weekly), summary, start, end, "
        "duration_weeks, reminder_minutes_before, timezone. "
        "Use ISO datetime with timezone offset if possible. "
        f"timezone={timezone}. Input: {text}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    max_retries = 3
    retry_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=12)

            # Handle quota exceeded (429)
            if response.status_code == 429:
                error_body = response.json()
                error_msg = error_body.get("error", {}).get("message", "Quota exceeded")
                print(f"[NL] ⚠️  Gemini quota หมด: {error_msg}")
                print("[NL] 🔄 สลับใช้ rule-based parser อัตโนมัติ")
                return None

            # Handle other HTTP errors
            if response.status_code != 200:
                print(f"[NL] ⚠️  Gemini API error {response.status_code} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                return None

            body = response.json()
            candidates = body.get("candidates", [])
            if not candidates:
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None

            raw_text = parts[0].get("text", "").strip()
            if not raw_text:
                return None

            data = json.loads(raw_text)
            print(f"[NL] ✅ Gemini parsed successfully")
            return _normalize_intent(data, timezone)

        except requests.exceptions.Timeout:
            print(f"[NL] ⏱️  Gemini timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            return None
        except Exception as e:
            print(f"[NL] ❌ Gemini error: {type(e).__name__}")
            return None

    return None


def _parse_english_date(text: str) -> Optional[Dict[str, Any]]:
    """Parse English date formats like 'March 20, 2026' or 'April 10 every year'."""
    # Month name mapping
    months = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    text_lower = text.lower()

    # Pattern 1: "March 25-29, 2026" (date range)
    range_match = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+"
        r"(\d{1,2})\s*-\s*(\d{1,2})\s*,?\s*(\d{4})",
        text_lower
    )
    if range_match:
        month_name, start_day, end_day, year = range_match.groups()
        month = months[month_name]
        start_day = int(start_day)
        end_day = int(end_day)
        year = int(year)

        # Multi-day event (00:00 to 23:59 each day)
        start = datetime(year, month, start_day, 0, 0)
        end = datetime(year, month, end_day, 23, 59)

        summary = _extract_summary(text)
        reminder = _extract_reminder_minutes(text)

        return {
            "intent_type": "single_event",
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_weeks": 1,
            "reminder_minutes_before": reminder,
            "timezone": "Asia/Bangkok",
        }

    # Pattern 2: "March 20, 2026 at 17:00" or "April 10 every year"
    single_match = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+"
        r"(\d{1,2}),?\s*(?:(\d{4}))?",
        text_lower
    )
    if single_match:
        month_name, day, year_str = single_match.groups()
        month = months[month_name]
        day = int(day)
        year = int(year_str) if year_str else datetime.now().year

        # Check for "at HH:MM" time
        time_at_match = re.search(r"at\s+(\d{1,2}):(\d{2})", text_lower)
        if time_at_match:
            hour = int(time_at_match.group(1))
            minute = int(time_at_match.group(2))
        else:
            # Default to 09:00 if no time specified
            hour, minute = 9, 0

        start = datetime(year, month, day, hour, minute)

        # Check if it's a task/deadline (single point in time)
        is_task = bool(re.search(r"\b(task|deadline|due|submit)\b", text_lower))

        if is_task:
            # Task: use same time for start and end (no duration)
            end = start
        else:
            # Regular event: default 1-hour duration
            end = start + timedelta(hours=1)

        summary = _extract_summary(text)
        reminder = _extract_reminder_minutes(text)

        # Check for yearly recurrence
        is_yearly = bool(re.search(r"\bevery\s+year\b", text_lower))

        return {
            "intent_type": "yearly_recurring" if is_yearly else "single_event",
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_weeks": 1,
            "reminder_minutes_before": reminder,
            "timezone": "Asia/Bangkok",
        }

    return None


def _parse_with_rules(text: str, timezone: str) -> Dict[str, Any]:
    reminder = _extract_reminder_minutes(text)

    # Try English date format first (e.g., "March 20, 2026" or "April 10")
    english_date = _parse_english_date(text)
    if english_date:
        return english_date

    date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    iso_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    time_range_match = re.search(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", text)
    weekday = _extract_weekday(text)

    summary = _extract_summary(text)

    if date_match:
        day, month, year = map(int, date_match.groups())
        start_hour, start_min = (9, 0)
        end_hour, end_min = (10, 0)
        if time_range_match:
            start_hour, start_min = map(int, time_range_match.group(1).split(":"))
            end_hour, end_min = map(int, time_range_match.group(2).split(":"))
        start = datetime(year, month, day, start_hour, start_min)
        end = datetime(year, month, day, end_hour, end_min)

        return {
            "intent_type": "single_event",
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_weeks": 1,
            "reminder_minutes_before": reminder,
            "timezone": timezone,
        }

    if iso_match:
        year, month, day = map(int, iso_match.groups())
        start_hour, start_min = (9, 0)
        end_hour, end_min = (10, 0)
        if time_range_match:
            start_hour, start_min = map(int, time_range_match.group(1).split(":"))
            end_hour, end_min = map(int, time_range_match.group(2).split(":"))
        start = datetime(year, month, day, start_hour, start_min)
        end = datetime(year, month, day, end_hour, end_min)

        return {
            "intent_type": "single_event",
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_weeks": 1,
            "reminder_minutes_before": reminder,
            "timezone": timezone,
        }

    if weekday is not None and time_range_match:
        duration_weeks = _extract_duration_weeks(text)
        now = datetime.now()
        start_time = time_range_match.group(1)
        end_time = time_range_match.group(2)
        start_hour, start_min = map(int, start_time.split(":"))
        end_hour, end_min = map(int, end_time.split(":"))

        start = _next_weekday_datetime(now, weekday, start_hour, start_min)
        end = start.replace(hour=end_hour, minute=end_min)

        if end <= start:
            end = end + timedelta(days=1)

        return {
            "intent_type": "recurring_weekly",
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_weeks": duration_weeks,
            "reminder_minutes_before": reminder,
            "timezone": timezone,
        }

    raise NLParseError(
        "ไม่สามารถตีความคำสั่งได้ กรุณาระบุอย่างน้อยวัน/เวลา เช่น '10/01/2027 10:00-11:00 นัดทำฟัน'"
    )


def _extract_summary(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()

    # Check for explicit prefixes
    task_match = re.search(r"^task:\s*(.+?)(?:deadline|due|,|$)", cleaned, flags=re.IGNORECASE)
    if task_match:
        return task_match.group(1).strip()

    birthday_match = re.search(r"birthday of\s+(.+?)(?:on|,|$)", cleaned, flags=re.IGNORECASE)
    if birthday_match:
        return f"Birthday: {birthday_match.group(1).strip()}"

    marker_patterns = [
        r"นัด(.+)$",
        r"เรียน(.+)$",
        r"schedule(.+)$",
        r"event(.+)$",
    ]
    for pattern in marker_patterns:
        m = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if m:
            suffix = m.group(1).strip()
            if "นัด" in pattern:
                return f"นัด{suffix}" if suffix else "นัดหมาย"
            if "เรียน" in pattern:
                return f"เรียน{suffix}" if suffix else "ตารางเรียน"

    return cleaned[:120]


def _extract_weekday(text: str) -> Optional[int]:
    for thai_day, index in THAI_WEEKDAYS.items():
        if thai_day in text:
            return index
    english = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    lowered = text.lower()
    for day, index in english.items():
        if day in lowered:
            return index
    return None


def _extract_duration_weeks(text: str) -> int:
    # Thai patterns
    months_match = re.search(r"(\d+)\s*เดือน", text)
    if months_match:
        months = int(months_match.group(1))
        return max(1, int(round(months * 4.33)))

    weeks_match = re.search(r"(\d+)\s*สัปดาห์", text)
    if weeks_match:
        return max(1, int(weeks_match.group(1)))

    # English patterns
    english_months_match = re.search(r"(\d+)\s*months?", text, flags=re.IGNORECASE)
    if english_months_match:
        months = int(english_months_match.group(1))
        return max(1, int(round(months * 4.33)))

    english_weeks_match = re.search(r"(\d+)\s*weeks?", text, flags=re.IGNORECASE)
    if english_weeks_match:
        return max(1, int(english_weeks_match.group(1)))

    # "for X weeks/months"
    for_weeks_match = re.search(r"for\s+(\d+)\s*weeks?", text, flags=re.IGNORECASE)
    if for_weeks_match:
        return max(1, int(for_weeks_match.group(1)))

    for_months_match = re.search(r"for\s+(\d+)\s*months?", text, flags=re.IGNORECASE)
    if for_months_match:
        months = int(for_months_match.group(1))
        return max(1, int(round(months * 4.33)))

    return 16


def _extract_reminder_minutes(text: str) -> int:
    # Thai patterns
    hour_match = re.search(r"ก่อน[^\d]*(\d+)\s*(ชม|ชั่วโมง|hour)", text, flags=re.IGNORECASE)
    if hour_match:
        return int(hour_match.group(1)) * 60

    minute_match = re.search(r"ก่อน[^\d]*(\d+)\s*(นาที|min)", text, flags=re.IGNORECASE)
    if minute_match:
        return int(minute_match.group(1))

    # English patterns: "2 hours before", "30 minutes before", "1 day before"
    day_before_match = re.search(r"(\d+)\s*days?\s+before", text, flags=re.IGNORECASE)
    if day_before_match:
        return int(day_before_match.group(1)) * 24 * 60

    hour_before_match = re.search(r"(\d+)\s*hours?\s+before", text, flags=re.IGNORECASE)
    if hour_before_match:
        return int(hour_before_match.group(1)) * 60

    minute_before_match = re.search(r"(\d+)\s*(?:minutes?|mins?)\s+before", text, flags=re.IGNORECASE)
    if minute_before_match:
        return int(minute_before_match.group(1))

    # "remind me X hours/minutes before"
    remind_hour_match = re.search(r"remind\s+me\s+(\d+)\s*hours?\s+before", text, flags=re.IGNORECASE)
    if remind_hour_match:
        return int(remind_hour_match.group(1)) * 60

    remind_minute_match = re.search(r"remind\s+me\s+(\d+)\s*(?:minutes?|mins?)\s+before", text, flags=re.IGNORECASE)
    if remind_minute_match:
        return int(remind_minute_match.group(1))

    remind_day_match = re.search(r"remind\s+me\s+(\d+)\s*days?\s+before", text, flags=re.IGNORECASE)
    if remind_day_match:
        return int(remind_day_match.group(1)) * 24 * 60

    return int(os.getenv("NL_DEFAULT_REMINDER_MINUTES", "60"))


def _next_weekday_datetime(base: datetime, weekday: int, hour: int, minute: int) -> datetime:
    days_ahead = (weekday - base.weekday()) % 7
    candidate = base + timedelta(days=days_ahead)
    return candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise NLParseError(f"Invalid datetime value: {value}")


def _normalize_intent(raw: Dict[str, Any], timezone: str) -> Dict[str, Any]:
    intent_type = raw.get("intent_type", "single_event")
    summary = str(raw.get("summary", "Untitled Event"))

    if "start" not in raw or "end" not in raw:
        raise NLParseError("LLM response missing start/end")

    start = _to_datetime(raw["start"])
    end = _to_datetime(raw["end"])

    if end <= start:
        end = start + timedelta(hours=1)

    duration_weeks = int(raw.get("duration_weeks", 1))
    reminder = int(raw.get("reminder_minutes_before", os.getenv("NL_DEFAULT_REMINDER_MINUTES", "60")))

    if intent_type not in {"single_event", "recurring_weekly"}:
        intent_type = "single_event"

    return {
        "intent_type": intent_type,
        "summary": summary,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_weeks": max(1, duration_weeks),
        "reminder_minutes_before": max(0, reminder),
        "timezone": str(raw.get("timezone", timezone) or timezone),
    }
