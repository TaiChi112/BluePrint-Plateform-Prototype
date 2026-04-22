#!/usr/bin/env python3
"""
Python MCP Client for Calendar Agent

Communicates with MCP Server via stdio JSON-RPC protocol.
This client allows the Python Calendar Agent to use Google Calendar tools
through the MCP protocol instead of direct API calls.

Usage:
    client = MCPClient(['node', 'mcp-server/server.js'])
    events = client.list_events('2026-06-01T00:00:00Z', '2026-06-30T23:59:59Z')
    client.create_event('Meeting', '2026-06-15T10:00:00+07:00', '2026-06-15T11:00:00+07:00')
"""

import json
import subprocess
import sys
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPEvent:
    """Represents a calendar event from MCP"""
    id: str
    summary: str
    start: str
    end: str
    description: Optional[str] = None


class MCPClientError(Exception):
    """Custom exception for MCP client errors"""
    pass


class MCPClient:
    """
    Python client for communicating with MCP Calendar Server via stdio

    This client sends JSON-RPC 2.0 requests to the MCP server and receives responses.
    """

    def __init__(self, server_command: List[str], timeout: int = 30):
        """
        Initialize MCP Client

        Args:
            server_command: Command to start MCP server (e.g., ['node', 'mcp-server/server.js'])
            timeout: Timeout for server communication in seconds
        """
        self.server_command = server_command
        self.timeout = timeout
        self.request_id = 0
        self.process = None
        self._response_handlers = {}
        self._lock = threading.Lock()
        self._connected = False

        self._start_server()

    def _start_server(self):
        """Start the MCP server process"""
        try:
            logger.info(f"Starting MCP server: {' '.join(self.server_command)}")
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Start response reader thread
            self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self._reader_thread.start()

            self._connected = True
            logger.info("✅ MCP server started successfully")
        except Exception as e:
            raise MCPClientError(f"Failed to start MCP server: {e}")

    def _read_responses(self):
        """Background thread to read responses from server"""
        try:
            while self.process and self.process.stdout:
                line = self.process.stdout.readline()
                if not line:
                    break

                try:
                    response = json.loads(line)
                    request_id = response.get('id')

                    if request_id in self._response_handlers:
                        event = self._response_handlers.pop(request_id)
                        event.set(response)
                except json.JSONDecodeError:
                    # Ignore non-JSON lines (e.g., server logs)
                    if line.strip():
                        logger.warning(f"Invalid JSON from server: {line}")
        except Exception as e:
            logger.error(f"Error reading responses: {e}")
            self._connected = False

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to server and wait for response

        Args:
            method: RPC method name (e.g., 'tools/list', 'tools/call')
            params: Request parameters

        Returns:
            Response data from server
        """
        if not self._connected:
            raise MCPClientError("MCP client not connected to server")

        with self._lock:
            self.request_id += 1
            request_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Create event to wait for response
        response_event = threading.Event()
        self._response_handlers[request_id] = response_event

        try:
            # Send request
            request_str = json.dumps(request)
            logger.debug(f"Sending request: {request_str}")
            self.process.stdin.write(request_str + "\n")
            self.process.stdin.flush()

            # Wait for response
            if not response_event.wait(timeout=self.timeout):
                raise MCPClientError(f"Request timeout (>{self.timeout}s)")

            # Get response
            response_data = response_event
            if hasattr(response_event, '_response'):
                response = response_event._response
            else:
                # Fallback - try to get from handlers
                response = {}

            if "result" in response:
                return response["result"]
            elif "error" in response:
                raise MCPClientError(f"Server error: {response['error'].get('message', str(response['error']))}")
            else:
                return {}

        except MCPClientError:
            raise
        except Exception as e:
            raise MCPClientError(f"Request failed: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from MCP server

        Returns:
            List of tool definitions
        """
        result = self._send_request("tools/list", {})
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server

        Args:
            name: Tool name (e.g., 'list_events', 'create_event')
            arguments: Tool arguments

        Returns:
            Tool response
        """
        result = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        # Extract content from response
        content = result.get("content", [])
        if content and len(content) > 0:
            text_content = content[0].get("text", "{}")
            return json.loads(text_content)

        return {}

    def list_events(
        self,
        time_min: str,
        time_max: str,
        max_results: int = 100
    ) -> List[MCPEvent]:
        """
        List calendar events in a date range

        Args:
            time_min: ISO 8601 start date (e.g., '2026-06-01T00:00:00Z')
            time_max: ISO 8601 end date (e.g., '2026-06-30T23:59:59Z')
            max_results: Maximum number of results

        Returns:
            List of MCPEvent objects
        """
        result = self.call_tool("list_events", {
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": max_results,
        })

        events = []
        for event_data in result.get("events", []):
            events.append(MCPEvent(
                id=event_data.get("id", ""),
                summary=event_data.get("summary", ""),
                start=event_data.get("start", ""),
                end=event_data.get("end", ""),
                description=event_data.get("description"),
            ))

        return events

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """
        Create a new calendar event

        Args:
            summary: Event title
            start: ISO 8601 start datetime
            end: ISO 8601 end datetime
            description: Optional event description
            location: Optional event location

        Returns:
            Event ID of created event
        """
        args = {
            "summary": summary,
            "start": start,
            "end": end,
        }
        if description:
            args["description"] = description
        if location:
            args["location"] = location

        result = self.call_tool("create_event", args)
        return result.get("eventId", "")

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> bool:
        """
        Update an existing calendar event

        Args:
            event_id: ID of event to update
            summary: New event title (optional)
            start: New start datetime (optional)
            end: New end datetime (optional)

        Returns:
            True if successful
        """
        args = {"eventId": event_id}
        if summary:
            args["summary"] = summary
        if start:
            args["start"] = start
        if end:
            args["end"] = end

        result = self.call_tool("update_event", args)
        return result.get("success", False)

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event

        Args:
            event_id: ID of event to delete

        Returns:
            True if successful
        """
        result = self.call_tool("delete_event", {"eventId": event_id})
        return result.get("success", False)

    def check_availability(self, start: str, end: str) -> bool:
        """
        Check if a time slot is available

        Args:
            start: ISO 8601 start datetime
            end: ISO 8601 end datetime

        Returns:
            True if slot is available (no conflicts)
        """
        result = self.call_tool("check_availability", {
            "start": start,
            "end": end,
        })
        return result.get("isAvailable", False)

    def close(self):
        """Close the MCP client and stop the server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self._connected = False
            logger.info("✅ MCP client closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage and testing
if __name__ == "__main__":
    try:
        # Start client
        client = MCPClient(["node", "mcp-server/server.js"])

        # List available tools
        print("\n📋 Available tools:")
        tools = client.list_tools()
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description']}")

        # Example: List events
        print("\n📅 Listing events from June 2026:")
        events = client.list_events(
            "2026-06-01T00:00:00Z",
            "2026-06-30T23:59:59Z"
        )
        print(f"  Found {len(events)} events")
        for event in events:
            print(f"    • {event.summary} ({event.start})")

        # Example: Create event
        print("\n➕ Creating test event...")
        event_id = client.create_event(
            summary="Test Event from MCP Client",
            start="2026-06-15T10:00:00+07:00",
            end="2026-06-15T11:00:00+07:00",
            description="Created via MCP client"
        )
        print(f"  Created event ID: {event_id}")

        # Example: Check availability
        print("\n🔍 Checking availability...")
        available = client.check_availability(
            "2026-06-15T14:00:00+07:00",
            "2026-06-15T15:00:00+07:00"
        )
        print(f"  Slot available: {available}")

        client.close()

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
