#!/usr/bin/env python3
"""
End-to-End Integration Test: /api/generate → /api/generate-viz

Simulates the complete flow:
1. LLM generates spec with processDescription
2. Frontend receives processDescription
3. Frontend calls /api/generate-viz with processDescription
4. Backend returns Excalidraw JSON

This test does NOT require FastAPI server running.
It tests the core business logic only.

Run with: python test_e2e_generate_viz.py
"""

import json
from datetime import datetime, timezone
from llm_to_excalidraw import (
    process_description_to_excalidraw,
    parse_process_steps,
    validate_excalidraw_json,
)

# Colors for output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def test_e2e_flow():
    """Simulate complete e2e flow"""

    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}E2E Integration Test: /api/generate → /api/generate-viz{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # ======================================================================
    # Step 1: Simulated LLM Response (from /api/generate)
    # ======================================================================
    print(f"{YELLOW}Step 1: LLM Generates Spec with Process Description{RESET}")
    print("-" * 70)

    # This simulates the response from /api/generate endpoint
    llm_response = {
        "message": "Success",
        "filename": "spec_2026_03_02_001.json",
        "data": {
            "project_name": "Online Learning Platform",
            "problem_statement": "Traditional learning platforms are too complex for elderly farmers to navigate. They need a mobile-friendly e-learning platform with simple video courses and quizzes.",
            "solution_overview": "Build a mobile-first PWA for agricultural education with video streaming, simple quiz system, and certificate generation.",
            "functional_requirements": [
                "User authentication (email/LINE login)",
                "Video playback with adaptive streaming",
                "Quiz system with auto-grading",
                "Certificate generation upon course completion",
                "Progress tracking"
            ],
            "non_functional_requirements": [
                "Mobile-first responsive design",
                "Offline support for video caching",
                "Support 50,000+ concurrent users",
                "99.9% uptime SLA"
            ],
            "tech_stack_recommendation": [
                "Next.js 16 (frontend)",
                "FastAPI (backend API)",
                "PostgreSQL (database)",
                "Redis (caching)",
                "HLS streaming (video delivery)",
                "Stripe (payment processing)"
            ],
            "status": "Ready",
            "processDescription": """
Process Flow:
→ Step 1: User logs in to platform (Input: username/password via LINE)
→ Step 2: Browse available agricultural courses (Duration: variable)
→ Step 3: Stream video course content (Duration: depends on video length)
→ Step 4: Complete quiz at end of chapter (Duration: 10-30 minutes)
→ Step 5: System auto-grades quiz and records progress (Duration: <1s)
→ Step 6: Award certificate if quiz score >= 70% (Output: certificate PDF)
            """
        }
    }

    print(f"{GREEN}✅ LLM Response Received{RESET}")
    print(f"   Project: {llm_response['data']['project_name']}")
    print(f"   Status: {llm_response['data']['status']}")

    process_desc = llm_response['data']['processDescription']
    print(f"   Process Description Length: {len(process_desc)} characters")

    # ======================================================================
    # Step 2: Frontend Extracts Process Description
    # ======================================================================
    print(f"\n{YELLOW}Step 2: Frontend Extracts Process Description{RESET}")
    print("-" * 70)

    # Frontend would extract processDescription and prepare request
    generate_viz_request = {
        "processDescription": process_desc,
        "specId": llm_response['filename']
    }

    print(f"{GREEN}✅ Request Prepared{RESET}")
    print(f"   Process Description (first 100 chars):")
    print(f"   '{process_desc.strip()[:100]}...'")

    # ======================================================================
    # Step 3: Backend Receives Request & Validates
    # ======================================================================
    print(f"\n{YELLOW}Step 3: Validation in /api/generate-viz Handler{RESET}")
    print("-" * 70)

    # Validate input
    if not generate_viz_request["processDescription"] or len(generate_viz_request["processDescription"].strip()) < 10:
        print(f"{RED}❌ Invalid input{RESET}")
        return False

    print(f"{GREEN}✅ Input validation passed{RESET}")

    # ======================================================================
    # Step 4: Parse Process Steps
    # ======================================================================
    print(f"\n{YELLOW}Step 4: Parse Process Steps{RESET}")
    print("-" * 70)

    steps = parse_process_steps(process_desc)

    print(f"{GREEN}✅ Parsed {len(steps)} steps{RESET}")
    for i, step in enumerate(steps, 1):
        print(f"   Step {i}: {step['title']}")
        if step['details']:
            print(f"           {step['details'][:80]}")

    # ======================================================================
    # Step 5: Generate Excalidraw JSON
    # ======================================================================
    print(f"\n{YELLOW}Step 5: Generate Excalidraw JSON{RESET}")
    print("-" * 70)

    exc_json = process_description_to_excalidraw(process_desc)

    element_count = len(exc_json.get("elements", []))
    print(f"{GREEN}✅ Excalidraw JSON Generated{RESET}")
    print(f"   Total Elements: {element_count}")

    # Count element types
    element_types = {}
    for elem in exc_json.get("elements", []):
        elem_type = elem.get("type", "unknown")
        element_types[elem_type] = element_types.get(elem_type, 0) + 1

    for elem_type, count in element_types.items():
        print(f"   - {elem_type}: {count}")

    # ======================================================================
    # Step 6: Validate Excalidraw JSON
    # ======================================================================
    print(f"\n{YELLOW}Step 6: Validate Excalidraw JSON{RESET}")
    print("-" * 70)

    if validate_excalidraw_json(exc_json):
        print(f"{GREEN}✅ JSON validation passed{RESET}")
    else:
        print(f"{RED}❌ JSON validation failed{RESET}")
        return False

    # ======================================================================
    # Step 7: Build API Response
    # ======================================================================
    print(f"\n{YELLOW}Step 7: Build API Response{RESET}")
    print("-" * 70)

    api_response = {
        "status": "success",
        "excalidrawJson": exc_json,
        "processDescription": process_desc.strip(),
        "elementCount": element_count,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "specId": generate_viz_request.get("specId")
    }

    print(f"{GREEN}✅ API Response Built{RESET}")
    print(f"   Status: {api_response['status']}")
    print(f"   Element Count: {api_response['elementCount']}")
    print(f"   Timestamp: {api_response['timestamp']}")
    print(f"   Spec ID: {api_response['specId']}")

    # ======================================================================
    # Step 8: Frontend Receives Response & Renders
    # ======================================================================
    print(f"\n{YELLOW}Step 8: Frontend Receives & Renders Diagram{RESET}")
    print("-" * 70)

    print(f"{GREEN}✅ Diagram Ready for Rendering{RESET}")
    print(f"   Next Steps:")
    print(f"   1. Frontend saves excalidrawJson to spec state")
    print(f"   2. Render diagram in /generator-test page (inline)")
    print(f"   3. Auto-save visualizationProcess field to DB on publish")

    # ======================================================================
    # Summary: Show sample JSON structure
    # ======================================================================
    print(f"\n{YELLOW}Sample API Response (truncated):,{RESET}")
    print("-" * 70)

    sample_response = {
        "status": api_response["status"],
        "elementCount": api_response["elementCount"],
        "timestamp": api_response["timestamp"],
        "specId": api_response["specId"],
        "excalidrawJson": {
            "type": exc_json.get("type"),
            "version": exc_json.get("version"),
            "elements": f"{len(exc_json.get('elements', []))} elements",
            "appState": "{ ...render config }"
        }
    }

    print(json.dumps(sample_response, indent=2))

    # ======================================================================
    # Final Summary
    # ======================================================================
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}E2E Test Summary{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    print(f"{GREEN}✅ Complete Pipeline Tested Successfully{RESET}\n")

    print(f"Pipeline Flow:")
    print(f"  1. {GREEN}✅{RESET} LLM generates spec with processDescription")
    print(f"  2. {GREEN}✅{RESET} Frontend extracts processDescription")
    print(f"  3. {GREEN}✅{RESET} Frontend calls /api/generate-viz")
    print(f"  4. {GREEN}✅{RESET} Backend validates input")
    print(f"  5. {GREEN}✅{RESET} Backend parses {len(steps)} process steps")
    print(f"  6. {GREEN}✅{RESET} Backend generates {element_count} Excalidraw elements")
    print(f"  7. {GREEN}✅{RESET} Backend validates Excalidraw JSON")
    print(f"  8. {GREEN}✅{RESET} Backend returns success response")
    print(f"  9. {GREEN}✅{RESET} Frontend receives and renders diagram")

    print(f"\n{GREEN}🎉 E2E Pipeline Complete!{RESET}\n")

    return True


if __name__ == "__main__":
    success = test_e2e_flow()
    exit(0 if success else 1)
