#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test NL agent with 10 real-world Thai sentences."""

import subprocess
import time
import requests
import json
from datetime import datetime

TEST_CASES = [
    {
        "name": "Single event with reminder",
        "text": "10/01/2027 10:00-11:00 นัดทำฟัน แจ้งเตือนก่อน 1 ชั่วโมง",
    },
    {
        "name": "Recurring weekly class 6 months",
        "text": "เทอม 1 ปี 69 เรียนวันจันทร์ 09:30-12:30 เป็นเวลา 6 เดือน แจ้งเตือนก่อนเรียน 1 ชม",
    },
    {
        "name": "Next Wednesday meeting",
        "text": "พุธหน้า 14:00-15:00 ประชุมทีม หาร solution bug ตัวhot",
    },
    {
        "name": "Exam prep with 15 min reminder",
        "text": "19/03/2026 09:00-10:00 สอบคณิตศาสตร์ เตือนก่อน 15 นาที",
    },
    {
        "name": "Recurring Friday gym",
        "text": "ทุกศุกร์ 17:30-18:30 โยคะ เป็นเวลา 8 สัปดาห์",
    },
    {
        "name": "Year-end party",
        "text": "31/12/2027 20:00-23:00 ปาร์ตี้ปีใหม่อย่างอบอุ่น",
    },
    {
        "name": "ISO date format",
        "text": "2027-03-15 13:00-14:00 ประชุมสำนักงาน",
    },
    {
        "name": "Monday recurring without duration",
        "text": "เรียนวันจันทร์ 10:00-12:00 วิชาโปรแกรมมิ่ง",
    },
    {
        "name": "Event with Thai month/year",
        "text": "วันที่ 5 มีนาคม 2564 09:00-10:00 ตรวจสุขภาพประจำปี",
    },
    {
        "name": "Simple meeting without reminder",
        "text": "18/06/2026 15:00-16:00 ประชุมเพื่ออัปเดตโปรเจ็กต์",
    },
]


def run_tests(base_url="http://localhost:5000"):
    """Run all test cases and report results."""
    print("=" * 80)
    print("NL AGENT TEST SUITE - 10 Real-World Sentences")
    print("=" * 80)

    results = []
    passed = 0
    failed = 0

    for idx, test_case in enumerate(TEST_CASES, 1):
        name = test_case["name"]
        text = test_case["text"]

        print(f"\n[Test {idx}/10] {name}")
        print(f"Input: {text}")

        try:
            response = requests.post(
                f"{base_url}/api/nl/plan",
                json={"text": text, "timezone": "Asia/Bangkok"},
                timeout=10,
            )

            if response.status_code != 200:
                print(f"❌ FAILED - Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                failed += 1
                results.append({
                    "name": name,
                    "status": "FAILED",
                    "reason": f"HTTP {response.status_code}",
                })
                continue

            data = response.json()
            if not data.get("success"):
                print(f"❌ FAILED - API returned success=false")
                print(f"   Error: {data.get('error', 'Unknown')}")
                failed += 1
                results.append({
                    "name": name,
                    "status": "FAILED",
                    "reason": data.get("error", "Unknown"),
                })
                continue

            intent = data.get("intent", {})
            events = data.get("events_preview", [])

            print(f"✓ PASSED")
            print(
                f"   Type: {intent.get('intent_type')} | Events: {len(events)} | Source: {intent.get('source')}"
            )
            print(f"   Summary: {intent.get('summary')}")
            if events:
                first = events[0]
                print(f"   Start: {first.get('start')}")
                print(f"   Reminder: {first.get('reminders_minutes_before')}min")

            passed += 1
            results.append({
                "name": name,
                "status": "PASSED",
                "intent_type": intent.get("intent_type"),
                "event_count": len(events),
            })

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - {e}")
            failed += 1
            results.append({
                "name": name,
                "status": "FAILED",
                "reason": str(e),
            })

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} Passed, {failed} Failed ({100*passed//10}% pass rate)")
    print("=" * 80)

    if failed > 0:
        print("\n⚠️  FAILURES:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"  • {r['name']}: {r.get('reason', 'Unknown')}")

    return results


if __name__ == "__main__":
    print("\n⏳ Waiting for Flask server to start (5 seconds)...\n")
    time.sleep(5)

    try:
        results = run_tests()

        print("\n📊 Detailed Results:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
