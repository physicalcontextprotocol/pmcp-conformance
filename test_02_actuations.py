"""
PCP Conformance Test — Section 2: Actuation Lifecycle
=========================================================
Verifies actuations/list, actuations/execute, batch actuation,
and correct error handling for unknown actuations.
"""
from __future__ import annotations

import pytest

from conftest import rpc_call as _rpc


async def rpc_call(base_url, method, params=None, req_id=1):
    return await _rpc(base_url, method, params, req_id)


class TestActuationLifecycle:
    """PCP-CONF-02: Actuation lifecycle."""

    @pytest.mark.asyncio
    async def test_actuations_list(self, mock_robot_server):
        """actuations/list MUST return a non-empty list of actuations."""
        resp = await _rpc(mock_robot_server["base_url"], "actuations/list", {})
        assert "error" not in resp, f"Unexpected error: {resp.get('error')}"
        result = resp["result"]
        assert "actuations" in result
        assert isinstance(result["actuations"], list)
        assert len(result["actuations"]) > 0, "No actuations registered"

    @pytest.mark.asyncio
    async def test_actuation_has_required_fields(self, mock_robot_server):
        """Each actuation MUST have 'name' and 'description' fields."""
        resp = await _rpc(mock_robot_server["base_url"], "actuations/list", {})
        for act in resp["result"]["actuations"]:
            assert "name" in act, f"Actuation missing 'name': {act}"
            assert "description" in act, f"Actuation missing 'description': {act}"

    @pytest.mark.asyncio
    async def test_execute_known_actuation(self, mock_robot_server):
        """actuations/execute MUST succeed for registered actuations."""
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/execute",
            {"name": "move_to", "params": {"x": 0.1, "y": 0.2, "z": 0.3}},
        )
        assert "error" not in resp
        result = resp["result"]
        assert "success" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_returns_energy_and_duration(self, mock_robot_server):
        """Actuation result MUST include energy_consumed_j and duration_ms."""
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/execute",
            {"name": "open_gripper", "params": {}},
        )
        result = resp["result"]
        assert "energy_consumed_j" in result, "energy_consumed_j missing"
        assert "duration_ms" in result, "duration_ms missing"
        assert isinstance(result["energy_consumed_j"], (int, float))
        assert isinstance(result["duration_ms"], (int, float))

    @pytest.mark.asyncio
    async def test_execute_unknown_actuation_returns_error(self, mock_robot_server):
        """Executing an unknown actuation MUST return method-not-found (-32601)."""
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/execute",
            {"name": "fly_to_moon", "params": {}},
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_batch_actuation(self, mock_robot_server):
        """actuations/batch MUST execute multiple actuations and return all results."""
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/batch",
            {
                "actuations": [
                    {"name": "open_gripper", "params": {}},
                    {"name": "move_to", "params": {"x": 0.0, "y": 0.0, "z": 0.2}},
                    {"name": "close_gripper", "params": {"force_n": 10.0}},
                ],
                "atomic": True,
            },
        )
        assert "error" not in resp
        result = resp["result"]
        assert "results" in result
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 3, f"Expected 3 results, got {len(result['results'])}"

    @pytest.mark.asyncio
    async def test_batch_actuation_has_total_duration(self, mock_robot_server):
        """Batch response MUST include total_duration_ms."""
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/batch",
            {
                "actuations": [{"name": "open_gripper", "params": {}}],
                "atomic": True,
            },
        )
        assert "total_duration_ms" in resp["result"]

    @pytest.mark.asyncio
    async def test_actuation_id_preserved_in_response(self, mock_robot_server):
        """JSON-RPC id in request MUST match id in response."""
        custom_id = 42
        resp = await _rpc(
            mock_robot_server["base_url"],
            "actuations/execute",
            {"name": "open_gripper", "params": {}},
            req_id=custom_id,
        )
        assert resp["id"] == custom_id
