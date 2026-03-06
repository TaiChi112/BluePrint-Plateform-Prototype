"""
Excalidraw Element Sanitizer and Fixer

Ported from reference:
/d/RepositoryVS/Clone/fastapi-gemini-excalidraw/gemini_excalidraw/sanitize_elements.py

Ensures Gemini-generated or text-parsed Excalidraw elements have all required fields
and fixes common issues (vertical arrows → lines, missing points, etc.)
"""

import time
import random


# Default field sets per element type
BASE_DEFAULTS = {
    "angle": 0,
    "seed": lambda: random.randint(1, 999999),
    "version": 1,
    "versionNonce": lambda: random.randint(1, 999999),
    "isDeleted": False,
    "groupIds": [],
    "boundElements": [],
    "updated": lambda: int(time.time() * 1000),
    "link": None,
    "locked": False,
    "opacity": 100,
}

TYPE_DEFAULTS = {
    "rectangle": {
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "roundness": None,
    },
    "arrow": {
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "roundness": {"type": 2},
        "points": [[0, 0], [100, 0]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "elbowed": False,
    },
    "line": {
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "roundness": None,
        "points": [[0, 0], [0, 300]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": None,
    },
    "text": {
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "roundness": None,
        "fontSize": 16,
        "fontFamily": 1,
        "textAlign": "left",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": "",
        "lineHeight": 1.25,
        "autoResize": True,
    },
}


def fix_elements(elements: list) -> list:
    """
    Fix common issues in Excalidraw elements.

    Fixes:
    - Vertical arrows → convert to lines
    - Sync points to width/height
    - Sync originalText to text
    """
    for el in elements:
        el_type = el.get("type")

        # Fix 1: lifelines should be type "line", not "arrow"
        if el_type == "arrow" and el.get("height", 0) > el.get("width", 0):
            el["type"] = "line"
            el["endArrowhead"] = None
            el["startArrowhead"] = None
            h = el.get("height", 300)
            el["points"] = [[0, 0], [0, h]]

        # Fix 2: sync points to actual width/height
        if el_type in ("arrow", "line"):
            w = el.get("width", 0)
            h = el.get("height", 0)
            current_pts = el.get("points", [])
            if not current_pts or current_pts[-1] != [w, h]:
                el["points"] = [[0, 0], [w, h]]

        # Fix 3: sync originalText to text
        if el_type == "text":
            el["originalText"] = el.get("text", "")

    return elements


def sanitize_element(el: dict) -> dict:
    """
    Fill in missing required fields for an Excalidraw element.

    Ensures all elements have required Excalidraw properties:
    - id, type, x, y (basic position)
    - strokeColor, backgroundColor, fillStyle (appearance)
    - Points for arrows/lines
    - Text fields for text elements
    """
    el_type = el.get("type", "rectangle")

    # Apply base defaults
    for key, value in BASE_DEFAULTS.items():
        if key not in el:
            el[key] = value() if callable(value) else value

    # Apply type-specific defaults
    for key, value in TYPE_DEFAULTS.get(el_type, {}).items():
        if key not in el:
            el[key] = value

    # Fix arrows: derive points from width/height if missing
    if el_type in ("arrow", "line") and el.get("points") in (None, []):
        w = el.get("width", 100)
        h = el.get("height", 0)
        el["points"] = [[0, 0], [w, h]]

    # Fix negative width/height on arrows (Gemini sometimes does this)
    if el_type in ("arrow", "line"):
        w = el.get("width", 0)
        h = el.get("height", 0)
        if w < 0 or h < 0:
            el["x"] = el.get("x", 0) + w
            el["y"] = el.get("y", 0) + h
            el["width"] = abs(w)
            el["height"] = abs(h)
            el["points"] = [[0, 0], [abs(w), abs(h)]]

    # Fix rectangle inline labels
    if el_type == "rectangle" and "label" in el:
        del el["label"]

    return el


def sanitize_elements(elements: list) -> list:
    """
    Sanitize a list of Excalidraw elements.

    Applies sanitize_element() to each element.
    """
    return [sanitize_element(el) for el in elements]
