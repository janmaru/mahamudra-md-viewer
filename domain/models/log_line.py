"""
Domain model for a single log line.
Pure data container with no external dependencies.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass
class LogLine:
    """A structured log line parsed from Serilog format."""
    raw: str
    timestamp: str = ""
    short_ts: str = ""
    level: str = ""
    body: str = ""
    direction: str = ""       # DIR_PLC_WCS | DIR_WCS_PLC | ""
    is_routing: bool = False
    routing_type: str = ""
    json_payload: str = ""
    json_pre: str = ""
    json_post: str = ""
    parsed_ts: dt.datetime | None = None

    def has_json(self) -> bool:
        """Check if this line contains a JSON payload."""
        return bool(self.json_payload)

    def is_error(self) -> bool:
        """Check if this line is an error or fatal level."""
        return self.level in ("ERR", "FTL")

    def is_warning(self) -> bool:
        """Check if this line is a warning."""
        return self.level == "WRN"

    def is_info(self) -> bool:
        """Check if this line is an info/debug level."""
        return self.level in ("INF", "DBG")

    def get_direction_label(self) -> str:
        """Get human-readable direction label."""
        if self.direction == "PLC->WCS":
            return "PLC → WCS"
        elif self.direction == "WCS->PLC":
            return "WCS → PLC"
        return ""
