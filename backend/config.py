"""
Backend Configuration for Diagram Generation & Rate Limiting
"""
import os
from typing import Dict, Any

# Rate Limiting Configuration
RATE_LIMITS: Dict[str, Any] = {
    "diagram_generation": {
        # Max generations per day per user
        "max_per_day": int(os.getenv("DIAGRAM_RATE_LIMIT_PER_DAY", "2")),

        # Reset time (UTC)
        "reset_hour": 0,  # Midnight UTC

        # Premium tier multiplier (future)
        "premium_multiplier": 5,  # Premium users: 10/day

        # Grace period for new users (days)
        "grace_period_days": 7,  # First 7 days: unlimited
    }
}

# Diagram Storage Configuration
DIAGRAM_STORAGE: Dict[str, Any] = {
    # Keep last N versions in database
    "db_history_limit": 3,

    # File backup directory
    "backup_dir": os.getenv("DIAGRAM_BACKUP_DIR", "diagrams"),

    # Enable file backup (in addition to DB)
    "file_backup_enabled": os.getenv("DIAGRAM_FILE_BACKUP", "true").lower() == "true",

    # Enable S3 backup (future)
    "s3_backup_enabled": os.getenv("DIAGRAM_S3_BACKUP", "false").lower() == "true",

    # S3 bucket name
    "s3_bucket": os.getenv("DIAGRAM_S3_BUCKET", "blueprint-hub-diagrams"),
}

# LLM Configuration for Diagram Generation
LLM_CONFIG: Dict[str, Any] = {
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 30,  # seconds
}

# MCP Configuration (Model Context Protocol integrations)
MCP_CONFIG: Dict[str, Any] = {
    # Excalidraw MCP - Process Flow/System Overview (MVP level, no details)
    "excalidraw": {
        "enabled": True,
        "use_case": "Process visualization (overview, no details)",
        "default_width": 280,
        "default_height": 70,
        "spacing": 140,
        "theme": "light",
        "color": {
            "stroke": "#43a047",  # Green
            "background": "#e8f5e9",
        }
    },

    # Draw.io MCP - Detailed Diagrams (Future: Phase 5+)
    "drawio": {
        "enabled": False,  # Future implementation
        "use_case": "Architecture, ER, Sequence diagrams (detailed)",
        "diagram_types": ["architecture", "er_diagram", "sequence", "flowchart"],
    },

    # Figma MCP - Wireframe Prototypes (Future: Phase 5+)
    "figma": {
        "enabled": False,  # Future implementation
        "use_case": "Wireframe prototype (black & white shapes only)",
        "color_scheme": "monochrome",  # Black & White only
        "elements": ["rectangle", "text", "button"],
    }
}

def get_rate_limit_for_user(user_id: str, is_premium: bool = False) -> int:
    """Get daily rate limit for a specific user."""
    base_limit = RATE_LIMITS["diagram_generation"]["max_per_day"]

    if is_premium:
        return base_limit * RATE_LIMITS["diagram_generation"]["premium_multiplier"]

    return base_limit

def get_backup_path(user_id: str, spec_id: str, version: int) -> str:
    """Generate file backup path for a diagram."""
    backup_dir = DIAGRAM_STORAGE["backup_dir"]
    return f"{backup_dir}/{user_id}/{spec_id}/v{version}.json"
