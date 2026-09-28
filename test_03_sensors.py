"""
P-MCP Conformance Test — Section 3: Sensor Reading
====================================================
Verifies sensors/list, sensors/read, sensor response schema,
and handling of unknown sensor names.
"""
from __future__ import annotations

import time
import pytest

from conftest import rpc_call


class TestSensorReading:
    """PMCP-CONF-03: Sensor reading."""

    @pytest.mark.asyncio
    async def test_sensors_list(self, mock_robot_server):
        """sensors/list MUST return a non-empty list."""
        resp = await rpc_call(mock_robot_server["base_url"], "sensors/list", {})
        assert "error" not in resp
        result = resp["result"]
        assert "sensors" in result
        assert isinstance(result["sensors"], list)
        assert len(result["sensors"]) > 0

    @pytest.mark.asyncio
    async def test_sensor_has_required_fields(self, mock_robot_server):
        """Each sensor entry MUST have 'name' field."""
        resp = await rpc_call(mock_robot_server["base_url"], "sensors/list", {})
        for s in resp["result"]["sensors"]:
            assert "name" in s, f"Sensor missing 'name': {s}"

    @pytest.mark.asyncio
    async def test_read_known_sensor(self, mock_robot_server):
        """sensors/read MUST succeed for a registered sensor."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "sensors/read",
            {"name": "joint_angles"},
        )
        assert "error" not in resp, f"Unexpected error: {resp.get('error')}"
        result = resp["result"]
        assert "value" in result

    @pytest.mark.asyncio
    async def test_sensor_reading_schema(self, mock_robot_server):
        """Sensor reading MUST include value, unit, timestamp_ms, and quality."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "sensors/read",
            {"name": "gripper_force"},
        )
        result = resp["result"]
        assert "value" in result, "value missing"
        assert "unit" in result, "unit missing"
        assert "timestamp_ms" in result, "timestamp_ms missing"
        assert "quality" in result, "quality missing"

    @pytest.mark.asyncio
    async def test_sensor_timestamp_is_recent(self, mock_robot_server):
        """Sensor timestamp MUST be within 5 seconds of the request time."""
        before = int(time.time() * 1000)
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "sensors/read",
            {"name": "joint_angles"},
        )
        after = int(time.time() * 1000)
        ts = resp["result"]["timestamp_ms"]
        assert before - 5000 <= ts <= after + 5000, f"Timestamp {ts} not recent"

    @pytest.mark.asyncio
    async def test_sensor_quality_range(self, mock_robot_server):
        """Sensor quality MUST be in range [0.0, 1.0]."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "sensors/read",
            {"name": "gripper_force"},
        )
        quality = resp["result"]["quality"]
        assert 0.0 <= float(quality) <= 1.0, f"quality={quality} out of range"

    @pytest.mark.asyncio
    async def test_read_unknown_sensor_returns_error(self, mock_robot_server):
        """Reading an unknown sensor MUST return error -32601."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "sensors/read",
            {"name": "quantum_teleporter"},
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601
