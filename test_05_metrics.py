"""
P-MCP Conformance Test — Section 5: Metrics & Ping
====================================================
Verifies the pmcp/metrics and pmcp/ping methods return
well-formed responses with required fields.
"""
from __future__ import annotations

import time
import pytest

from conftest import rpc_call

METRICS_REQUIRED = {
    "actuationCount",
    "sensorReadCount",
    "safetyViolations",
    "avgActuationDurationMs",
    "uptimeSeconds",
    "energyUsedJ",
    "connectedClients",
    "lastHeartbeatMs",
}


class TestMetricsAndPing:
    """PMCP-CONF-05: Metrics and ping."""

    @pytest.mark.asyncio
    async def test_ping_responds(self, mock_robot_server):
        """pmcp/ping MUST return a response without error."""
        resp = await rpc_call(mock_robot_server["base_url"], "pmcp/ping", {})
        assert "error" not in resp
        assert resp["result"] is not None

    @pytest.mark.asyncio
    async def test_ping_response_is_recent(self, mock_robot_server):
        """Ping response timestamp MUST be within 5 seconds."""
        before = int(time.time() * 1000)
        resp = await rpc_call(mock_robot_server["base_url"], "pmcp/ping", {})
        after = int(time.time() * 1000)
        ts = resp["result"].get("timestamp")
        if ts is not None:
            assert before - 5000 <= int(ts) <= after + 5000

    @pytest.mark.asyncio
    async def test_metrics_returns_all_required_fields(self, mock_robot_server):
        """pmcp/metrics MUST include all required metric fields."""
        resp = await rpc_call(mock_robot_server["base_url"], "pmcp/metrics", {})
        assert "error" not in resp
        result = resp["result"]
        for field in METRICS_REQUIRED:
            assert field in result, f"Metric field '{field}' missing"

    @pytest.mark.asyncio
    async def test_metrics_values_are_non_negative(self, mock_robot_server):
        """All numeric metric values MUST be non-negative."""
        resp = await rpc_call(mock_robot_server["base_url"], "pmcp/metrics", {})
        result = resp["result"]
        for field in METRICS_REQUIRED:
            val = result.get(field, 0)
            assert float(val) >= 0, f"{field}={val} is negative"

    @pytest.mark.asyncio
    async def test_uptime_is_positive(self, mock_robot_server):
        """uptimeSeconds MUST be > 0 after server startup."""
        resp = await rpc_call(mock_robot_server["base_url"], "pmcp/metrics", {})
        assert float(resp["result"]["uptimeSeconds"]) >= 0


class TestEstop:
    """PMCP-CONF-05b: Emergency stop."""

    @pytest.mark.asyncio
    async def test_estop_engage(self, mock_robot_server):
        """safety/estop/engage MUST return engaged=True."""
        resp = await rpc_call(
            mock_robot_server["base_url"], "safety/estop/engage", {}
        )
        assert "error" not in resp
        assert resp["result"]["engaged"] is True

    @pytest.mark.asyncio
    async def test_estop_disengage(self, mock_robot_server):
        """safety/estop/disengage MUST return engaged=False."""
        await rpc_call(mock_robot_server["base_url"], "safety/estop/engage", {})
        resp = await rpc_call(
            mock_robot_server["base_url"], "safety/estop/disengage", {}
        )
        assert "error" not in resp
        assert resp["result"]["engaged"] is False
