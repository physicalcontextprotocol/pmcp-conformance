"""
PCP Conformance Test Suite — conftest.py
==========================================
Shared fixtures for conformance tests.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
import time
from typing import Any, AsyncGenerator, Dict, Generator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import pytest_asyncio


# ─────────────────────────────────────────────────────────────────────────────
#  In-process mock robot server
# ─────────────────────────────────────────────────────────────────────────────

ROBOT_ID = "test_robot_001"
LEASE_STORE: Dict[str, Any] = {}
LEASE_COUNTER = 0


class MockRobotHandler(BaseHTTPRequestHandler):
    """Minimal PCP server for conformance testing."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # suppress output
        pass

    def do_GET(self):
        if self.path == "/health":
            self._respond({"status": "ok", "robot_id": ROBOT_ID})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global LEASE_COUNTER
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self._respond_raw(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
            )
            return

        method = req.get("method", "")
        params = req.get("params", {}) or {}
        req_id = req.get("id")

        result = None
        error = None

        if method == "initialize":
            result = {
                "protocolVersion": "0.5",
                "serverInfo": {
                    "name": "mock-robot",
                    "robotId": ROBOT_ID,
                    "robotClass": "TestRobot",
                },
                "capabilities": {
                    "actuations": {
                        "move_to": {
                            "name": "move_to",
                            "description": "Move to target position",
                            "parameters": [
                                {"name": "x", "type": "number", "description": "X", "required": True},
                                {"name": "y", "type": "number", "description": "Y", "required": True},
                                {"name": "z", "type": "number", "description": "Z", "required": True},
                            ],
                        },
                        "open_gripper": {
                            "name": "open_gripper",
                            "description": "Open the gripper",
                            "parameters": [],
                        },
                        "close_gripper": {
                            "name": "close_gripper",
                            "description": "Close gripper",
                            "parameters": [
                                {"name": "force_n", "type": "number", "description": "Grip force (N)", "required": False},
                            ],
                        },
                    },
                    "sensors": {
                        "joint_angles": {
                            "name": "joint_angles",
                            "description": "Read joint angles",
                            "sensor_type": "joint_state",
                            "unit": "radians",
                        },
                        "gripper_force": {
                            "name": "gripper_force",
                            "description": "Gripper force sensor",
                            "sensor_type": "force",
                            "unit": "N",
                        },
                    },
                    "features": {
                        "shadow": True,
                        "constitution": False,
                        "leases": True,
                        "metrics": True,
                        "batching": True,
                    },
                },
            }

        elif method == "actuations/list":
            result = {
                "actuations": [
                    {"name": "move_to", "description": "Move to target position"},
                    {"name": "open_gripper", "description": "Open the gripper"},
                    {"name": "close_gripper", "description": "Close gripper"},
                ]
            }

        elif method == "actuations/execute":
            name = params.get("name", "")
            if name not in ("move_to", "open_gripper", "close_gripper"):
                error = {"code": -32601, "message": f"Actuation not found: {name}"}
            else:
                result = {
                    "success": True,
                    "final_pose": {"x": 0.1, "y": 0.2, "z": 0.3},
                    "energy_consumed_j": 12.5,
                    "duration_ms": 450,
                }

        elif method == "actuations/batch":
            items = params.get("actuations", [])
            results = []
            for item in items:
                results.append({
                    "success": True,
                    "energy_consumed_j": 5.0,
                    "duration_ms": 100,
                })
            result = {
                "success": True,
                "results": results,
                "total_duration_ms": sum(r["duration_ms"] for r in results),
            }

        elif method == "sensors/list":
            result = {
                "sensors": [
                    {"name": "joint_angles", "sensor_type": "joint_state"},
                    {"name": "gripper_force", "sensor_type": "force"},
                ]
            }

        elif method == "sensors/read":
            name = params.get("name", "")
            if name == "joint_angles":
                result = {
                    "value": [0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
                    "unit": "radians",
                    "timestamp_ms": int(time.time() * 1000),
                    "quality": 1.0,
                }
            elif name == "gripper_force":
                result = {
                    "value": 5.2,
                    "unit": "N",
                    "timestamp_ms": int(time.time() * 1000),
                    "quality": 0.99,
                }
            else:
                error = {"code": -32601, "message": f"Sensor not found: {name}"}

        elif method == "leases/acquire":
            LEASE_COUNTER += 1
            zone_id = params.get("zone_id", "default")
            duration_ms = params.get("duration_ms", 30000)
            lease_id = f"lease_{LEASE_COUNTER}_{int(time.time())}"
            LEASE_STORE[lease_id] = {
                "zone_id": zone_id,
                "robot_id": ROBOT_ID,
                "expires_ms": int(time.time() * 1000) + duration_ms,
            }
            result = {
                "lease_id": lease_id,
                "zone_id": zone_id,
                "robot_id": ROBOT_ID,
                "expires_ms": int(time.time() * 1000) + duration_ms,
                "granted": True,
            }

        elif method == "leases/release":
            lease_id = params.get("lease_id", "")
            released = lease_id in LEASE_STORE
            if released:
                del LEASE_STORE[lease_id]
            result = {"released": released}

        elif method == "pcp/metrics":
            result = {
                "actuationCount": 10,
                "sensorReadCount": 50,
                "safetyViolations": 0,
                "avgActuationDurationMs": 350.0,
                "uptimeSeconds": 120.0,
                "energyUsedJ": 250.0,
                "connectedClients": 1,
                "lastHeartbeatMs": int(time.time() * 1000),
            }

        elif method == "pcp/ping":
            result = {"pong": True, "timestamp": int(time.time() * 1000)}

        elif method == "safety/estop/engage":
            result = {"engaged": True}

        elif method == "safety/estop/disengage":
            result = {"engaged": False}

        else:
            error = {"code": -32601, "message": f"Method not found: {method}"}

        if error:
            self._respond_raw({"jsonrpc": "2.0", "error": error, "id": req_id})
        else:
            self._respond_raw({"jsonrpc": "2.0", "result": result, "id": req_id})

    def _respond(self, data: Any, status: int = 200):
        self._respond_raw(data, status)

    def _respond_raw(self, data: Any, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-PCP-Version", "0.5")
        self.end_headers()
        self.wfile.write(body)


def _find_free_port() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def mock_robot_server():
    """Start a mock PCP robot server for the test session."""
    port = _find_free_port()
    server = HTTPServer(("127.0.0.1", port), MockRobotHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # give the server a moment to start
    time.sleep(0.05)

    yield {
        "host": "127.0.0.1",
        "port": port,
        "base_url": f"http://127.0.0.1:{port}",
        "robot_id": ROBOT_ID,
    }

    server.shutdown()


async def rpc_call(base_url: str, method: str, params: dict | None = None, req_id: int = 1) -> dict:
    """Send a JSON-RPC 2.0 request to the mock robot and return the response dict.

    Uses urllib from stdlib so conformance tests have no extra dependencies.
    """
    import urllib.request
    import urllib.error
    payload = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        base_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _do_request() -> dict:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_request)


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop so fixtures can be shared."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
