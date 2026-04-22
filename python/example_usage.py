#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน Calendar Agent กับ Integration ต่างๆ

รัน:
    python example_usage.py --mode mock          # Mock (demo)
    python example_usage.py --mode api           # Google Calendar API
    python example_usage.py --mode mcp           # MCP Server
"""

import argparse
from datetime import datetime
from main import CalendarAgent, Event
from calendar_integrations import get_calendar_tool, print_setup_guide

def main():
    parser = argparse.ArgumentParser(description="Calendar Agent Demo")
    parser.add_argument(
        "--mode",
        choices=["mock", "api", "mcp"],
        default="mock",
        help="Calendar integration mode"
    )
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to Google OAuth credentials (for 'api' mode)"
    )
    parser.add_argument(
        "--setup-guide",
        action="store_true",
        help="แสดงคู่มือการติดตั้ง"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="เปิดใช้งาน Interactive mode (รับ input จากผู้ใช้)"
    )

    args = parser.parse_args()

    # แสดงคู่มือถ้าขอ
    if args.setup_guide:
        print_setup_guide(args.mode)
        return

    print(f"\n{'='*60}")
    print(f"  📅 Calendar Agent - Mode: {args.mode.upper()}")
    if args.interactive:
        print(f"  🎮 Interactive Mode: ON")
    print(f"{'='*60}\n")

    # สร้าง calendar tool
    try:
        if args.mode == "api":
            calendar = get_calendar_tool("api", credentials_path=args.credentials)
        else:
            calendar = get_calendar_tool(args.mode)
    except Exception as e:
        print(f"❌ Error: {e}\n")
        print(f"💡 ดูคู่มือการติดตั้ง: python {__file__} --mode {args.mode} --setup-guide")
        return

    # สร้าง agent
    agent = CalendarAgent(calendar)

    # ตัวอย่างคำสั่ง: ลงตารางเรียน 1 เทอม
    print("📝 User Intent: ลงตาราง CS301: Data Mining ทุกวันจันทร์ 09:30 (4 สัปดาห์)")
    print("   เริ่ม: 1 มิถุนายน 2026\n")

    user_intent = {
        "summary": "📘 CS301: Data Mining",
        "start": datetime(2026, 6, 1, 9, 30),
        "duration_weeks": 4
    }

    # Process request (with or without interaction)
    response = agent.process_recurring_request(user_intent, interactive=args.interactive)

    # แสดงผลลัพธ์ (ถ้าไม่ใช่ interactive mode หรือมี response)
    if not args.interactive or (isinstance(response, str) and "เสร็จสมบูรณ์" not in response):
        print("\n" + "="*60)
        print("📊 Result:")
        print("="*60)
        print(response)
        print("\n")

    # แสดงสถิติ (ถ้า mode = mock)
    if args.mode == "mock":
        print(f"📈 Mock Database: มี {len(calendar.db)} events ทั้งหมด")
        print("\nรายการ Events:")
        for i, ev in enumerate(calendar.db, 1):
            print(f"  {i}. {ev.summary}")
            print(f"     {ev.start.strftime('%Y-%m-%d %H:%M')} - {ev.end.strftime('%H:%M')}")

if __name__ == "__main__":
    main()
