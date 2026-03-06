"""
gemini_to_excalidraw.py
-----------------------
Sends a text description to Gemini → Excalidraw elements JSON →
add_elements via excalidraw-mcp → clean diagram in browser canvas.

Requirements:
    pip install google-genai mcp python-dotenv

Usage:
    python gemini_to_excalidraw.py
    python gemini_to_excalidraw.py --prompt "Draw a 3-tier web architecture"
    python gemini_to_excalidraw.py --prompt "Draw a 3-tier web architecture" --output arch.excalidraw
"""
import asyncio
import argparse
import json
import math
import os
import random
import re
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "YOUR_GEMINI_MODEL_HERE")

SYSTEM_PROMPT = """\
You are an Excalidraw diagram expert. Convert the user's description into
a valid Excalidraw elements array (JSON).

RULES:
- Return ONLY a raw JSON array — no explanation, no markdown fences.
- Each element must follow the Excalidraw element schema below.
- Use "rectangle" for boxes/containers, "text" for standalone labels,
  "arrow" for connections, "ellipse" for databases.
- For group containers (e.g. tiers), use a large rectangle with low opacity
  (backgroundColor: "#e8f4f8", opacity: 40).
- Place elements with realistic x/y so they don't overlap.
  Use an 800px wide canvas, spacing elements at least 80px apart vertically.
- Keep ids short (e.g. "el1", "el2", ...).
- Use strokeColor "#333333", backgroundColor "#dbe9f9" for normal boxes.
- Use strokeStyle "dashed" for replica/cache connections.

SHAPE ELEMENT SCHEMA:
{
  "id": "el1",
  "type": "rectangle",          // or "ellipse"
  "x": 100,
  "y": 100,
  "width": 160,
  "height": 60,
  "label": {"text": "My Label"},  // optional inline label
  "strokeColor": "#333333",
  "backgroundColor": "#dbe9f9",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 1,
  "opacity": 100,
  "roundness": {"type": 3}      // optional rounded corners
}

TEXT ELEMENT SCHEMA:
{
  "id": "t1",
  "type": "text",
  "x": 100,
  "y": 100,
  "width": 160,
  "height": 25,
  "text": "My Label",
  "fontSize": 16,
  "strokeColor": "#333333",
  "backgroundColor": "transparent",
  "opacity": 100
}

ARROW ELEMENT SCHEMA:
{
  "id": "ar1",
  "type": "arrow",
  "x": 200,
  "y": 160,
  "width": 0,
  "height": 80,
  "strokeColor": "#333333",
  "startBinding": {"elementId": "el1", "focus": 0, "gap": 1},
  "endBinding":   {"elementId": "el2", "focus": 0, "gap": 1}
}
"""


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def dump_result(label: str, result) -> None:
    print(f"\n  ┌─ {label} ───────────────────────────────────")
    if not result.content:
        print("  │  (empty)")
    for i, block in enumerate(result.content):
        kind = getattr(block, "type", type(block).__name__)
        text = getattr(block, "text", repr(block))
        print(f"  │  [{i}] type={kind}")
        print(f"  │      {text[:600]}")
    print(f"  │  isError={getattr(result, 'isError', False)}")
    print(f"  └────────────────────────────────────────────\n")


# ─────────────────────────────────────────────
# Step 1: Gemini → Excalidraw elements JSON
# ─────────────────────────────────────────────
def generate_elements(user_prompt: str) -> list:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"[1/5] Sending to Gemini ({GEMINI_MODEL})...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )
    raw = response.text.strip()
    # Strip accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$",          "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    print(f"\n── Raw Gemini output (first 500 chars) ─────\n{raw[:500]}\n────────────────────────────────────────────\n")

    elements = json.loads(raw)   # raises if Gemini returned bad JSON
    print(f"      ✔ Parsed {len(elements)} raw elements from Gemini")

    

    return elements


# ─────────────────────────────────────────────
# Steps 2–4: MCP → add_elements → get_scene
# ─────────────────────────────────────────────
async def send_to_excalidraw(elements: list, session_name: str = "gemini-diagram",export_path:str = "./export.json", export_format: str = "json") -> str:
    # Windows-specific environment setup
    import os
    from pathlib import Path
    
    env = os.environ.copy()
    
    # Use absolute path for Windows compatibility
    script_dir = Path(__file__).parent.absolute()
    server_script = script_dir / "node_modules" / "@scofieldfree" / "excalidraw-mcp" / "dist" / "index.js"
    
    if not server_script.exists():
        raise FileNotFoundError(f"MCP server not found at {server_script}. Run: npm install @scofieldfree/excalidraw-mcp")
    
    server_params = StdioServerParameters(
        command="node",
        args=[str(server_script)],
        env=env
    )

    print("[2/5] Connecting to @scofieldfree/excalidraw-mcp...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("      Initializing MCP session...")
                await session.initialize()
                print("      ✓ Session initialized")
                tools_response = await session.list_tools()
                tool_names = [t.name for t in tools_response.tools]
                print(f"      Available tools: {tool_names}\n")

                # ── start_session ────────────────────────────
                print("[3/5] start_session...")
                r1 = await session.call_tool("start_session", {"sessionId": session_name})
                dump_result("start_session", r1)
                print("      Waiting 4s for browser + WebSocket...")
                await asyncio.sleep(4)

                # ── add_elements ─────────────────────────────
                print(f"[4/5] add_elements ({len(elements)} elements)...")
                r2 = await session.call_tool(
                    "add_elements",
                    {
                        "sessionId": session_name,
                        "elements":  elements,
                    },
                )
                dump_result("add_elements", r2)
                await asyncio.sleep(2)

                # ── get_scene ────────────────────────────────
                print("[5/5] get_scene...")
                r3 = await session.call_tool("get_scene", {"sessionId": session_name})
                dump_result("get_scene", r3)
                await asyncio.sleep(2)
                
                print("[6/5] export_diagram...")
                r4 = await session.call_tool("export_diagram", {"sessionId": session_name, "path": export_path,"format":export_format})
                
                # ── export json ────────────────────────────────
                if export_format == "json":

                    with open(export_path) as f:
                        exported = json.load(f)

                    excalidraw_file = {
                        "type": "excalidraw",
                        "version": 2,
                        "source": "https://excalidraw.com",
                        "elements": exported["elements"],
                        "appState": exported["appState"],
                        "files": {}
                    }

                    with open("arch.excalidraw", "w") as f:
                        json.dump(excalidraw_file, f, ensure_ascii=False)
                
                texts = [c.text for c in r3.content if hasattr(c, "text")]
                return "\n".join(texts)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt",  "-p", type=str, default=None)
    parser.add_argument("--session", "-s", type=str, default="gemini-diagram")
    parser.add_argument("--output",  "-o", type=str, default=None)
    args = parser.parse_args()

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        sys.exit("❌  Set GEMINI_API_KEY environment variable.")

    user_prompt = args.prompt or input("📝 Enter diagram description: ").strip()
    if not user_prompt:
        sys.exit("❌  No prompt provided.")

    # Step 1 — Gemini
    elements = generate_elements(user_prompt)

    # Steps 2–4 — MCP → Excalidraw canvas → text
    try:
        scene_text = asyncio.run(
            # export image
            # send_to_excalidraw(elements, session_name=args.session,export_format="png") 
            send_to_excalidraw(elements, session_name=args.session)
        )
    except KeyboardInterrupt:
        sys.exit("\n👋 Cancelled.")

    print("\n── Excalidraw scene (text) ─────────────────")
    print(json.dumps(elements, indent=2, ensure_ascii=False))
    print("────────────────────────────────────────────\n")

   


if __name__ == "__main__":
    main()