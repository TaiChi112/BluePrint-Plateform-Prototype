#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web UI for Calendar Agent

Provides a user-friendly web interface for:
- Viewing calendar events
- Creating recurring events
- Handling conflict detection with interactive resolution
- Smart rescheduling with time slot suggestions
- Real-time status updates

Usage:
    pip install flask flask-cors
    python app.py

Access at: http://localhost:5000
"""

import sys
import io
# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta, time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from nl_agent import NLParseError, parse_user_intent, build_events_from_intent

load_dotenv()

try:
    from calendar_integrations import get_calendar_tool
    # Try to import from main
    try:
        from main import (
            CalendarAgent,
            expand_recurring_events,
            check_conflict,
            find_available_slots,
            calculate_time_slot_score,
        )
    except (ImportError, AttributeError):
        # If imports fail, create mock implementations
        CalendarAgent = None
        expand_recurring_events = None
        check_conflict = None
        find_available_slots = None
        calculate_time_slot_score = None
except ImportError as e:
    print(f"⚠️  Warning: Could not import calendar tools: {e}")

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Global agent instance
calendar_agent = None
calendar_tool = None
current_calendar_mode = os.environ.get('CALENDAR_MODE', 'mock').strip().lower()
current_credentials_path = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
backend_state_file = Path(__file__).parent / '.calendar_backend_state.json'


def load_calendar_backend_state():
    """Load persisted backend mode so dev reloader/process splits stay consistent."""
    if backend_state_file.exists():
        try:
            data = json.loads(backend_state_file.read_text(encoding='utf-8'))
            return {
                'mode': str(data.get('mode', current_calendar_mode)).strip().lower(),
                'credentials_path': str(data.get('credentials_path', current_credentials_path)),
            }
        except Exception:
            pass

    return {
        'mode': current_calendar_mode,
        'credentials_path': current_credentials_path,
    }


def persist_calendar_backend_state(mode: str, credentials_path: str):
    backend_state_file.write_text(
        json.dumps({
            'mode': mode,
            'credentials_path': credentials_path,
        }, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def ensure_calendar_backend():
    """Keep in-memory backend aligned with persisted runtime state."""
    state = load_calendar_backend_state()
    desired_mode = state['mode']
    desired_credentials = state['credentials_path']

    if (
        calendar_tool is None
        or current_calendar_mode != desired_mode
        or current_credentials_path != desired_credentials
    ):
        set_calendar_backend(mode=desired_mode, credentials_path=desired_credentials)


def set_calendar_backend(mode: str | None = None, credentials_path: str | None = None):
    """Initialize or switch calendar backend at runtime."""
    global calendar_agent, calendar_tool, current_calendar_mode, current_credentials_path

    selected_mode = (mode or current_calendar_mode or os.environ.get('CALENDAR_MODE', 'mock')).strip().lower()
    selected_credentials = credentials_path or current_credentials_path or os.environ.get('CREDENTIALS_PATH', 'credentials.json')

    try:
        calendar_tool = get_calendar_tool(
            mode=selected_mode,
            credentials_path=selected_credentials,
        )
        if CalendarAgent is not None:
            calendar_agent = CalendarAgent(calendar_tool)
            print(f"[OK] Calendar Agent initialized with {selected_mode} mode")
        else:
            print(f"[WARNING] CalendarAgent not available - using direct calendar tool mode={selected_mode}")

        os.environ['CALENDAR_MODE'] = selected_mode
        os.environ['CREDENTIALS_PATH'] = selected_credentials
        current_calendar_mode = selected_mode
        current_credentials_path = selected_credentials
        persist_calendar_backend_state(selected_mode, selected_credentials)
        return {
            'success': True,
            'mode': selected_mode,
            'credentials_path': selected_credentials,
        }
    except Exception as e:
        calendar_agent = None
        calendar_tool = None
        return {
            'success': False,
            'mode': selected_mode,
            'credentials_path': selected_credentials,
            'error': str(e),
        }


def _to_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    raise ValueError(f"Unsupported datetime value: {value}")


def _event_to_dict(event):
    if hasattr(event, '__dataclass_fields__'):
        event_dict = asdict(event)
    elif isinstance(event, dict):
        event_dict = event
    else:
        event_dict = {
            'summary': getattr(event, 'summary', 'Untitled Event'),
            'start': getattr(event, 'start', None),
            'end': getattr(event, 'end', None),
        }

    start_value = event_dict.get('start')
    end_value = event_dict.get('end')
    if isinstance(start_value, datetime):
        event_dict['start'] = start_value.isoformat()
    if isinstance(end_value, datetime):
        event_dict['end'] = end_value.isoformat()
    return event_dict


def _get_events(start_iso: str, end_iso: str):
    ensure_calendar_backend()
    if calendar_agent is not None and hasattr(calendar_agent, 'get_events'):
        return calendar_agent.get_events(start_iso, end_iso)
    if calendar_tool is not None and hasattr(calendar_tool, 'get_events'):
        return calendar_tool.get_events(_to_datetime(start_iso), _to_datetime(end_iso))
    raise RuntimeError('Calendar backend is not initialized')


def _save_event(event_data):
    ensure_calendar_backend()
    if calendar_agent is not None and hasattr(calendar_agent, 'save_event'):
        return calendar_agent.save_event(event_data)

    if calendar_tool is not None and hasattr(calendar_tool, 'add_event'):
        class EventObj:
            def __init__(self, data):
                self.summary = data.get('summary', 'Untitled Event')
                self.start = _to_datetime(data.get('start'))
                self.end = _to_datetime(data.get('end'))
                self.reminders_minutes_before = data.get('reminders_minutes_before')

        payload = event_data if isinstance(event_data, dict) else _event_to_dict(event_data)
        return calendar_tool.add_event(EventObj(payload))

    raise RuntimeError('Calendar backend is not initialized')


def _delete_event(event_id: str):
    if calendar_agent is not None and hasattr(calendar_agent, 'delete_event'):
        return calendar_agent.delete_event(event_id)
    raise RuntimeError('Delete event is only supported with CalendarAgent backend')


def _expand_events(summary: str, start: datetime, duration_minutes: int, duration_weeks: int):
    if callable(expand_recurring_events):
        return expand_recurring_events(
            summary=summary,
            start=start,
            duration_minutes=duration_minutes,
            duration_weeks=duration_weeks,
        )

    events = []
    for week in range(duration_weeks):
        event_start = start + timedelta(weeks=week)
        event_end = event_start + timedelta(minutes=duration_minutes)
        events.append({
            'summary': summary,
            'start': event_start.isoformat(),
            'end': event_end.isoformat(),
        })
    return events


def _has_conflict(event_a, event_b):
    if callable(check_conflict):
        return check_conflict(event_a, event_b)

    a = _event_to_dict(event_a)
    b = _event_to_dict(event_b)
    a_start = _to_datetime(a['start'])
    a_end = _to_datetime(a['end'])
    b_start = _to_datetime(b['start'])
    b_end = _to_datetime(b['end'])
    return a_start < b_end and b_start < a_end


def _suggest_slots(event, existing_events):
    if callable(find_available_slots):
        return find_available_slots(event, existing_events)

    event_data = _event_to_dict(event)
    start = _to_datetime(event_data['start'])
    duration = _to_datetime(event_data['end']) - _to_datetime(event_data['start'])

    suggestions = []
    for offset in (1, 2, 3):
        candidate_start = start + timedelta(hours=offset)
        candidate_end = candidate_start + duration
        overlap = False
        for existing in existing_events:
            existing_data = _event_to_dict(existing)
            ex_start = _to_datetime(existing_data['start'])
            ex_end = _to_datetime(existing_data['end'])
            if candidate_start < ex_end and ex_start < candidate_end:
                overlap = True
                break
        if not overlap:
            suggestions.append({
                'start': candidate_start.isoformat(),
                'end': candidate_end.isoformat(),
            })
    return suggestions


def _score_slot(slot, preferences):
    if callable(calculate_time_slot_score):
        class SlotObj:
            def __init__(self, data):
                self.start = data.get('start')
                self.end = data.get('end')

        return calculate_time_slot_score(SlotObj(slot), preferences)

    start = _to_datetime(slot['start'])
    score = 70
    if 9 <= start.hour <= 17:
        score += 20
    if start.weekday() < 5:
        score += 10
    return min(score, 100)


def init_app():
    """Initialize the app with calendar tool"""
    mode = os.environ.get('CALENDAR_MODE', 'mock')
    credentials_path = os.environ.get('CREDENTIALS_PATH', 'credentials.json')

    result = set_calendar_backend(mode=mode, credentials_path=credentials_path)
    if result['success']:
        return

    print(f"[WARNING] Calendar Tool initialization: {result['error']}")
    fallback = set_calendar_backend(mode='mock', credentials_path=credentials_path)
    if fallback['success']:
        print("[OK] Falling back to mock mode")
    else:
        print("[ERROR] Could not initialize any calendar tool")


# API Routes

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/calendar-client')
def calendar_client():
    """Serve the calendar client UI"""
    return render_template('calendar_client.html')


@app.route('/quick-test')
def quick_test():
    """Serve a minimal end-to-end test UI for Calendar Agent."""
    return render_template('quick_test.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    state = load_calendar_backend_state()
    return jsonify({
        'status': 'healthy',
        'calendar_mode': state['mode'],
        'gemini_configured': bool(os.environ.get('GEMINI_API_KEY')),
    })


@app.route('/api/calendar-mode', methods=['GET', 'POST'])
def calendar_mode():
    """Get or change the active calendar backend mode."""
    if request.method == 'GET':
        state = load_calendar_backend_state()
        return jsonify({
            'success': True,
            'mode': state['mode'],
            'credentials_path': state['credentials_path'],
        })

    data = request.get_json() or {}
    state = load_calendar_backend_state()
    mode = data.get('mode', state['mode'] or 'mock')
    credentials_path = data.get('credentials_path') or state['credentials_path']
    result = set_calendar_backend(mode=mode, credentials_path=credentials_path)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@app.route('/api/validate-keys', methods=['GET'])
def validate_keys():
    """Validate all API keys and credentials status"""
    import requests

    results = {
        'timestamp': datetime.now().isoformat(),
        'google_oauth': {'status': 'unknown', 'details': ''},
        'gemini_api': {'status': 'unknown', 'details': ''},
    }

    # Check Google OAuth
    try:
        credentials_path = os.getenv('CREDENTIALS_PATH', './credentials.json')
        token_path = os.getenv('TOKEN_PATH', './token.json')

        if not os.path.exists(credentials_path):
            results['google_oauth']['status'] = 'missing'
            results['google_oauth']['details'] = 'credentials.json not found'
        elif not os.path.exists(token_path):
            results['google_oauth']['status'] = 'not_authorized'
            results['google_oauth']['details'] = 'token.json not found, need OAuth flow'
        else:
            # Try to use calendar tool
            try:
                from calendar_integrations import get_calendar_tool
                calendar = get_calendar_tool()
                test_start = datetime.now()
                test_end = datetime.now() + timedelta(days=1)
                events = calendar.get_events(test_start, test_end)
                results['google_oauth']['status'] = 'valid'
                results['google_oauth']['details'] = f'Connected successfully, {len(events)} events in test window'
            except Exception as e:
                results['google_oauth']['status'] = 'error'
                results['google_oauth']['details'] = str(e)
    except Exception as e:
        results['google_oauth']['status'] = 'error'
        results['google_oauth']['details'] = str(e)

    # Check Gemini API
    try:
        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        if not api_key:
            results['gemini_api']['status'] = 'missing'
            results['gemini_api']['details'] = 'GEMINI_API_KEY not configured'
        else:
            # Test with list models endpoint (doesn't consume quota)
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                models = response.json().get('models', [])
                results['gemini_api']['status'] = 'valid'
                results['gemini_api']['details'] = f'Key valid, {len(models)} models available'
            elif response.status_code == 400:
                results['gemini_api']['status'] = 'invalid'
                results['gemini_api']['details'] = 'Invalid API key format'
            elif response.status_code == 403:
                results['gemini_api']['status'] = 'forbidden'
                results['gemini_api']['details'] = 'API key valid but not authorized for this project'
            else:
                results['gemini_api']['status'] = 'error'
                results['gemini_api']['details'] = f'HTTP {response.status_code}: {response.text[:100]}'

            # Test quota with a minimal request
            model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            test_payload = {
                'contents': [{'parts': [{'text': 'test'}]}],
                'generationConfig': {'maxOutputTokens': 1}
            }
            gen_response = requests.post(gen_url, json=test_payload, timeout=10)

            if gen_response.status_code == 429:
                quota_msg = gen_response.json().get('error', {}).get('message', 'Quota exceeded')
                results['gemini_api']['quota_status'] = 'exceeded'
                results['gemini_api']['quota_details'] = quota_msg[:200]
            elif gen_response.status_code == 200:
                results['gemini_api']['quota_status'] = 'available'
                results['gemini_api']['quota_details'] = 'Generation quota available'
            else:
                results['gemini_api']['quota_status'] = 'unknown'

    except requests.exceptions.Timeout:
        results['gemini_api']['status'] = 'timeout'
        results['gemini_api']['details'] = 'Request timeout (network issue)'
    except Exception as e:
        results['gemini_api']['status'] = 'error'
        results['gemini_api']['details'] = str(e)

    # Overall status
    all_valid = (
        results['google_oauth']['status'] == 'valid' and
        results['gemini_api']['status'] == 'valid'
    )
    results['overall'] = 'healthy' if all_valid else 'degraded'

    return jsonify(results)


@app.route('/api/nl-parse', methods=['POST'])
def nl_parse():
    """Parse natural language input into calendar intent"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        feature_type = data.get('feature_type', 'event')
        timezone = data.get('timezone', 'Asia/Bangkok')

        if not text:
            return jsonify({
                'success': False,
                'error': 'Empty input text'
            }), 400

        # Parse intent
        intent = parse_user_intent(text, timezone)

        # Build events with feature type
        events = build_events_from_intent(intent, feature_type)

        return jsonify({
            'success': True,
            'feature_type': feature_type,
            'intent': intent,
            'events': events,
            'count': len(events)
        })

    except NLParseError as e:
        return jsonify({
            'success': False,
            'error': f'Parse error: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/nl-create', methods=['POST'])
def nl_create():
    """Create events from parsed intent"""
    try:
        data = request.get_json()
        events_data = data.get('events', [])

        if not events_data:
            return jsonify({
                'success': False,
                'error': 'No events to create'
            }), 400

        # Get calendar tool
        from calendar_integrations import get_calendar_tool, Event
        calendar = get_calendar_tool()

        success_count = 0
        errors = []
        created_ids = []

        for event_dict in events_data:
            try:
                # Create Event object with all fields
                event = Event(
                    summary=event_dict['summary'],
                    start=datetime.fromisoformat(event_dict['start']),
                    end=datetime.fromisoformat(event_dict['end']),
                    event_type=event_dict.get('event_type', 'event'),
                    location=event_dict.get('location'),
                    description=event_dict.get('description'),
                    is_all_day=event_dict.get('is_all_day', False)
                )

                # Add reminder attribute if present
                if 'reminders_minutes_before' in event_dict:
                    event.reminders_minutes_before = event_dict['reminders_minutes_before']

                # Log event type
                event_type = event_dict.get('event_type', 'event')
                print(f"[CREATE] {event_type}: {event.summary}")

                # Add event to calendar
                result = calendar.add_event(event)
                if result:
                    success_count += 1
                    created_ids.append(event.summary)
                else:
                    errors.append(f"Failed to create: {event.summary}")

            except Exception as e:
                errors.append(f"Error creating {event_dict.get('summary', 'unknown')}: {str(e)}")

        return jsonify({
            'success': True,
            'success_count': success_count,
            'total': len(events_data),
            'created_ids': created_ids,
            'errors': errors if errors else None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/events', methods=['GET'])
def list_events():
    """
    Get calendar events for a date range

    Query parameters:
    - start: ISO 8601 start date (default: today)
    - end: ISO 8601 end date (default: 30 days from start)
    """
    try:
        start = request.args.get('start', datetime.now().isoformat())
        end = request.args.get('end', (datetime.now() + timedelta(days=30)).isoformat())

        events = _get_events(start, end)

        return jsonify({
            'success': True,
            'events': [_event_to_dict(e) for e in events],
            'count': len(events),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/api/create-recurring', methods=['POST'])
def create_recurring_event():
    """
    Create a recurring event

    Request body:
    {
        "summary": "Event title",
        "start": "ISO 8601 datetime",
        "duration_minutes": 60,
        "duration_weeks": 4,
        "day_of_week": 1  // 0=Monday, 6=Sunday (optional)
    }
    """
    try:
        data = request.json

        summary = data.get('summary', 'Untitled Event')
        start_str = data.get('start')
        duration_minutes = data.get('duration_minutes', 60)
        duration_weeks = data.get('duration_weeks', 4)

        if not start_str:
            return jsonify({
                'success': False,
                'error': 'Missing required field: start',
            }), 400

        start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))

        # Expand recurring events
        events = _expand_events(
            summary=summary,
            start=start,
            duration_minutes=duration_minutes,
            duration_weeks=duration_weeks,
        )

        # Check for conflicts
        existing_events = _get_events(
            start.isoformat(),
            (start + timedelta(weeks=duration_weeks + 1)).isoformat(),
        )

        conflicts = []
        safe_events = []

        for event in events:
            has_conflict = False
            for existing in existing_events:
                if _has_conflict(event, existing):
                    conflicts.append({
                        'new_event': _event_to_dict(event),
                        'existing_event': _event_to_dict(existing),
                    })
                    has_conflict = True
                    break

            if not has_conflict:
                safe_events.append(event)

        session['pending_events'] = {
            'safe_events': [_event_to_dict(e) for e in safe_events],
            'conflict_events': [c['new_event'] for c in conflicts],
            'conflicts': conflicts,
        }

        return jsonify({
            'success': True,
            'created_count': len(safe_events),
            'conflict_count': len(conflicts),
            'conflicts': conflicts,
            'safe_events': session['pending_events']['safe_events'],
            'message': f'Created {len(safe_events)} events. Found {len(conflicts)} conflicts.',
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/api/suggest-slots', methods=['POST'])
def suggest_slots():
    """
    Suggest available time slots for a conflicting event

    Request body:
    {
        "event": { ... },
        "preferences": { ... }
    }
    """
    try:
        data = request.json
        conflict_event = data.get('event')
        preferences = data.get('preferences', {})

        if not conflict_event:
            return jsonify({
                'success': False,
                'error': 'Missing event data',
            }), 400

        # Convert event dict back to object-like structure
        class Event:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        event = Event(conflict_event)

        # Get existing events for that day
        start = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
        existing_events = _get_events(
            start.replace(hour=0, minute=0, second=0).isoformat(),
            start.replace(hour=23, minute=59, second=59).isoformat(),
        )

        # Find available slots
        slots = _suggest_slots(event, existing_events)

        # Score slots
        scored_slots = []
        for slot in slots:
            slot_obj = Event(slot) if isinstance(slot, dict) else slot
            score = _score_slot({
                'start': slot['start'] if isinstance(slot, dict) else slot.start,
                'end': slot['end'] if isinstance(slot, dict) else slot.end,
            }, preferences)
            scored_slots.append({
                'start': slot['start'] if isinstance(slot, dict) else slot.start,
                'end': slot['end'] if isinstance(slot, dict) else slot.end,
                'score': score,
            })

        # Sort by score
        scored_slots.sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
            'success': True,
            'suggestions': scored_slots[:5],  # Top 5
            'message': f'Found {len(scored_slots)} available slots',
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/api/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    """
    Resolve conflicts with user choice

    Request body:
    {
        "action": "skip" | "overwrite" | "reschedule" | "cancel",
        "selected_slot": { "start": "...", "end": "..." }  // for reschedule
    }
    """
    try:
        data = request.json
        action = data.get('action', 'skip')
        selected_slot = data.get('selected_slot')

        pending = session.get('pending_events', {})

        created_events = []

        if action == 'skip':
            # Skip conflicting events, create safe ones
            for event in pending.get('safe_events', []):
                _save_event(event)
                created_events.append(event)

        elif action == 'overwrite':
            # Create all events, overwriting conflicts
            for event in pending.get('safe_events', []):
                _save_event(event)
                created_events.append(event)
            for event in pending.get('conflict_events', []):
                _save_event(event)
                created_events.append(event)

        elif action == 'reschedule' and selected_slot:
            # Reschedule conflicting events to suggested slot
            for event in pending.get('conflict_events', []):
                event['start'] = selected_slot['start']
                event['end'] = selected_slot['end']
                _save_event(event)
                created_events.append(event)
            for event in pending.get('safe_events', []):
                _save_event(event)
                created_events.append(event)

        # Clear pending
        session.pop('pending_events', None)

        return jsonify({
            'success': True,
            'action': action,
            'created_count': len(created_events),
            'message': f'Resolved conflicts. Created {len(created_events)} events.',
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/api/event', methods=['DELETE'])
def delete_event():
    """Delete a calendar event"""
    try:
        event_id = request.args.get('id')
        if not event_id:
            return jsonify({
                'success': False,
                'error': 'Missing event ID',
            }), 400

        _delete_event(event_id)

        return jsonify({
            'success': True,
            'message': f'Event {event_id} deleted',
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400


@app.route('/api/nl/plan', methods=['POST'])
def plan_natural_language_event():
    """Parse natural language input into a structured plan."""
    try:
        data = request.json or {}
        text = data.get('text', '')
        timezone_name = data.get('timezone', os.environ.get('TIMEZONE', 'Asia/Bangkok'))

        intent = parse_user_intent(text=text, timezone=timezone_name)
        events = build_events_from_intent(intent)

        return jsonify({
            'success': True,
            'intent': intent,
            'events_preview': events,
            'message': f"Parsed '{intent['intent_type']}' with {len(events)} event(s)",
        })
    except NLParseError as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@app.route('/api/nl/execute', methods=['POST'])
def execute_natural_language_event():
    """Parse natural language and save events to calendar backend."""
    try:
        data = request.json or {}
        text = data.get('text', '')
        timezone_name = data.get('timezone', os.environ.get('TIMEZONE', 'Asia/Bangkok'))
        skip_conflicts = bool(data.get('skip_conflicts', True))

        intent = parse_user_intent(text=text, timezone=timezone_name)
        events = build_events_from_intent(intent)

        all_starts = [_to_datetime(event['start']) for event in events]
        all_ends = [_to_datetime(event['end']) for event in events]
        range_start = min(all_starts).replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = max(all_ends).replace(hour=23, minute=59, second=59, microsecond=0)

        existing_events = _get_events(range_start.isoformat(), range_end.isoformat())

        created = []
        conflicts = []

        for event in events:
            conflict_hit = False
            for existing in existing_events:
                if _has_conflict(event, existing):
                    conflicts.append({
                        'new_event': event,
                        'existing_event': _event_to_dict(existing),
                    })
                    conflict_hit = True
                    break

            if conflict_hit and skip_conflicts:
                continue

            _save_event(event)
            created.append(event)

        return jsonify({
            'success': True,
            'intent': intent,
            'created_count': len(created),
            'conflict_count': len(conflicts),
            'created_events': created,
            'conflicts': conflicts,
            'message': f"Created {len(created)} event(s), conflicts {len(conflicts)}",
        })
    except NLParseError as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    init_app()

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print(f"""
========================================
    Calendar Agent Web Interface
========================================

Starting server on http://localhost:{port}
API docs: http://localhost:{port}/api/health

Press Ctrl+C to stop the server.
    """)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
    )
