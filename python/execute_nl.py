#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive CLI for Natural Language Calendar Agent
ใช้แบบ: python execute_nl.py
"""

import sys
import io

# Only wrap stdout/stderr once per process
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from nl_agent import parse_user_intent, build_events_from_intent, NLParseError
from calendar_integrations import get_calendar_tool

sys.path.insert(0, str(Path(__file__).parent))


def print_header():
    """Print welcome message"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Natural Language Calendar Agent CLI v1.0            ║
║                                                              ║
║ สั่งตารางเวลาด้วยภาษาธรรมชาติ (Thai/English)               ║
║ หรือพิมพ์ 'quit' เพื่อออก                                   ║
╚══════════════════════════════════════════════════════════════╝
""")


def format_event(event: dict) -> str:
    """Format event for display"""
    try:
        summary = event['summary']
        if isinstance(summary, bytes):
            summary = summary.decode('utf-8', errors='ignore')
    except:
        summary = "(Untitled)"

    return (
        f"  - {summary}\n"
        f"    Start: {event['start']}\n"
        f"    End: {event['end']}\n"
        f"    Reminder: {event.get('reminders_minutes_before', 60)} minutes before"
    )


def confirm_and_save(intent: dict, events: list, calendar_tool) -> bool:
    """Show preview and ask for confirmation"""
    print("\n[PREVIEW] Events to be created:")
    for i, evt in enumerate(events, 1):
        print(f"\n{i}. {format_event(evt)}")

    print(f"\n[INFO] Found {len(events)} event(s) to save")
    print(f"[INFO] Intent type: {intent['intent_type']}")
    print(f"[INFO] Reminder: {intent.get('reminder_minutes_before', 60)} minutes")

    while True:
        choice = input("\n[INPUT] Save to calendar? (y/n): ").strip().lower()
        if choice in ('y', 'yes'):
            return True
        elif choice in ('n', 'no'):
            return False
        else:
            print("[ERROR] Please answer 'y' or 'n'")


def save_events(events: list, calendar_tool) -> int:
    """Save events to calendar and return count"""
    saved = 0
    for event in events:
        try:
            # Convert dict to event object
            class Event:
                def __init__(self, data):
                    self.summary = data.get('summary', '')
                    self.start = datetime.fromisoformat(str(data['start']).replace('Z', '+00:00'))
                    self.end = datetime.fromisoformat(str(data['end']).replace('Z', '+00:00'))
                    self.reminders_minutes_before = data.get('reminders_minutes_before', 60)

            evt = Event(event)
            if calendar_tool.add_event(evt):
                saved += 1
        except Exception as e:
            print(f"[ERROR] Failed to save event: {e}")

    return saved


def main():
    """Main interactive loop"""
    print_header()

    mode = os.environ.get('CALENDAR_MODE', 'mock')
    try:
        calendar_tool = get_calendar_tool(mode=mode)
        print(f"[OK] Calendar backend: {mode}\n")
    except Exception as e:
        print(f"[ERROR] Could not initialize calendar: {e}")
        sys.exit(1)

    while True:
        try:
            text = input("\n[INPUT] Enter event description (or 'quit'): ").strip()

            if text.lower() in ('quit', 'exit', 'q'):
                print("\n[INFO] Goodbye!")
                break

            if not text:
                print("[WARNING] Please enter something")
                continue

            print("[LOADING] Parsing input...")
            intent = parse_user_intent(text=text, timezone=os.environ.get('TIMEZONE', 'Asia/Bangkok'))
            events = build_events_from_intent(intent)

            print(f"[SUCCESS] Parsed as '{intent['intent_type']}' with {len(events)} event(s)")

            if confirm_and_save(intent, events, calendar_tool):
                saved = save_events(events, calendar_tool)
                print(f"\n[SUCCESS] Saved {saved}/{len(events)} events to {mode} calendar")
            else:
                print("[INFO] Cancelled")

        except NLParseError as e:
            print(f"[ERROR] Could not understand: {e}")
        except KeyboardInterrupt:
            print("\n\n[INFO] Interrupted by user")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")


if __name__ == '__main__':
    main()
