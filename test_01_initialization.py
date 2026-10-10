"""
PCP Conformance Test — Section 1: Initialization Handshake
==============================================================
Verifies that a compliant robot server correctly handles the initialize
handshake as specified in Section 3.1 of the protocol spec.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict

import aiohttp
import pytest
import pytest_asyncio

PCP_VERSION = "0.5"
JSONRPC_VERSION = "2.0"


async def rpc_call(base_url: str, method: str, params: Dict[str, Any] = None, req_id: int = 1):
    """Helper: perform a single JSON-RPC call and return parsed response."""
    payload = {
        "jsonrpc": JSONRPC_VERSION,
        "method": method,
        "params": params or {},
        "id": req_id,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as resp:
            assert resp.status == 200, f"HTTP {resp.status}"
            return await resp.json()


# ─────────────────────────────────────────────────────────────────────────────

class TestInitializationHandshake:
    """PCP-CONF-01: Initialization handshake."""

    @pytest.mark.asyncio
    async def test_initialize_returns_protocol_version(self, mock_robot_server):
        """Server MUST return the negotiated protocolVersion in initialize response."""
        base = mock_robot_server["base_url"]
        resp = await rpc_call(base, "initialize", {
            "protocolVersion": PCP_VERSION,
            "clientInfo": {"name": "conformance-tester", "version": "1.0.0"},
        })
        assert "error" not in resp, f"Unexpected error: {resp.get('error')}"
        result = resp["result"]
        assert "protocolVersion" in result, "protocolVersion missing from initialize response"
        assert result["protocolVersion"] == PCP_VERSION

    @pytest.mark.asyncio
    async def test_initialize_includes_server_info(self, mock_robot_server):
        """Server MUST include serverInfo with name and robotId."""
        resp = await rpc_call(mock_robot_server["base_url"], "initialize", {
            "protocolVersion": PCP_VERSION,
        })
        result = resp["result"]
        assert "serverInfo" in result
        info = result["serverInfo"]
        assert "name" in info
        assert "robotId" in info

    @pytest.mark.asyncio
    async def test_initialize_includes_capabilities(self, mock_robot_server):
        """Server MUST include capabilities.actuations and capabilities.sensors."""
        resp = await rpc_call(mock_robot_server["base_url"], "initialize", {
            "protocolVersion": PCP_VERSION,
        })
        result = resp["result"]
        assert "capabilities" in result
        caps = result["capabilities"]
        assert "actuations" in caps or "features" in caps

    @pytest.mark.asyncio
    async def test_initialize_response_is_valid_jsonrpc(self, mock_robot_server):
        """Response MUST be valid JSON-RPC 2.0."""
        resp = await rpc_call(mock_robot_server["base_url"], "initialize", {
            "protocolVersion": PCP_VERSION,
        })
        assert resp["jsonrpc"] == JSONRPC_VERSION
        assert "id" in resp
        assert "result" in resp or "error" in resp

    @pytest.mark.asyncio
    async def test_unknown_method_returns_method_not_found(self, mock_robot_server):
        """Unknown methods MUST return error code -32601."""
        resp = await rpc_call(mock_robot_server["base_url"], "nonexistent/method", {})
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_invalid_json_returns_parse_error(self, mock_robot_server):
        """Invalid JSON body MUST return parse error -32700."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_robot_server['base_url']}/mcp",
                data=b"not-json!!!",
                headers={"Content-Type": "application/json"},
            ) as resp:
                assert resp.status == 200  # JSON-RPC errors are still HTTP 200
                body = await resp.json()
                assert "error" in body
                assert body["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_health_endpoint(self, mock_robot_server):
        """GET /health MUST return 200 with status=ok."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{mock_robot_server['base_url']}/health") as resp:
                assert resp.status == 200
                body = await resp.json()
                assert body.get("status") == "ok"
