"""
Business logic for parsing Serilog-style log files.
Pure domain service with no external dependencies.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Optional

from ..models.log_line import LogLine
from ..models.tree_node import TreeNode


# Serilog line regex
_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+[+\-]\d{2}:\d{2})"
    r"\s+\[(?P<level>\w+)\]"
    r"\s+(?P<body>.*)$"
)

_DIRECTION_RE = re.compile(r"^\[(?P<dir>PLC\s*->\s*WCS|WCS\s*->\s*PLC)\]\s*")
_ROUTING_RE = re.compile(r"^Routing message of type\s+(?P<type>\S+)")
_SHORT_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2}\.\d{3})\d*\s+[+\-]\d{2}:\d{2}")

_LEVEL_MAP = {
    "WARNING": "WRN", "WAR": "WRN",
    "ERROR": "ERR",
    "FATAL": "FTL",
    "DEBUG": "DBG",
    "INFORMATION": "INF", "INFO": "INF",
}

DIR_PLC_WCS = "PLC->WCS"
DIR_WCS_PLC = "WCS->PLC"
_GROUP_GAP_SECONDS = 2.0


class LogParserService:
    """Service for parsing and structuring Serilog log content."""

    @staticmethod
    def parse_line(raw: str) -> LogLine:
        """Parse a single log line from raw text."""
        line = LogLine(raw=raw)
        m = _LINE_RE.match(raw)
        if not m:
            line.body = raw
            return line

        line.timestamp = m.group("ts")
        line.level = m.group("level").upper()
        line.level = _LEVEL_MAP.get(line.level, line.level)
        body = m.group("body")

        ts_short = _SHORT_TS_RE.match(line.timestamp)
        line.short_ts = ts_short.group(1) if ts_short else line.timestamp
        line.parsed_ts = LogParserService._parse_timestamp(line.timestamp)

        dm = _DIRECTION_RE.match(body)
        if dm:
            line.direction = dm.group("dir").replace(" ", "")
            body = body[dm.end():]

        rm = _ROUTING_RE.match(body)
        if rm:
            line.is_routing = True
            line.routing_type = rm.group("type")

        extracted = LogParserService._extract_json(body)
        if extracted:
            line.json_pre = extracted[0]
            raw_json = extracted[1]
            line.json_post = extracted[2]
            try:
                parsed = json.loads(raw_json)
                line.json_payload = json.dumps(parsed, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                line.json_payload = raw_json
            line.body = line.json_pre
        else:
            line.body = body

        return line

    @staticmethod
    def parse_lines(content: str) -> list[LogLine]:
        """Parse multiple lines from content string."""
        raw_lines = content.splitlines()
        return [LogParserService.parse_line(line) for line in raw_lines if line.strip()]

    @staticmethod
    def build_tree(lines: list[LogLine]) -> list[TreeNode]:
        """Group lines into tree structure (routing messages with children)."""
        nodes: list[TreeNode] = []
        current_node: Optional[TreeNode] = None
        last_ts: Optional[dt.datetime] = None

        for line in lines:
            ts = line.parsed_ts
            gap = False
            if ts and last_ts and (ts - last_ts).total_seconds() > _GROUP_GAP_SECONDS:
                gap = True
            last_ts = ts

            if line.is_routing:
                current_node = TreeNode(header=line)
                nodes.append(current_node)
            elif gap:
                current_node = None
                nodes.append(TreeNode(header=line))
            elif current_node is not None:
                current_node.children.append(line)
            else:
                nodes.append(TreeNode(header=line))

        return nodes

    @staticmethod
    def _parse_timestamp(ts_str: str) -> Optional[dt.datetime]:
        """Parse timestamp from Serilog format."""
        try:
            return dt.datetime.strptime(ts_str[:23], "%Y-%m-%d %H:%M:%S.%f")
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _extract_json(body: str) -> Optional[tuple[str, str, str]]:
        """Extract JSON payload from log line body.
        
        Returns (pre, json_str, post) or None.
        """
        idx = body.find(": {")
        if idx == -1:
            return None
        
        pre = body[:idx].strip()
        rest = body[idx + 2:]  # starts with '{'
        depth = 0
        end = -1
        
        for i, ch in enumerate(rest):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        
        if end == -1:
            return None
        
        json_str = rest[:end + 1]
        post = rest[end + 1:].strip()
        return pre, json_str, post
