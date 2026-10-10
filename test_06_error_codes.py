"""
PCP Conformance Test — Section 6: Error Codes
=================================================
Verifies that all PCP-specific error codes are correctly numeric
and that the error structure conforms to JSON-RPC 2.0.
"""
from __future__ import annotations

import pytest

from conftest import rpc_call

# PCP error code range
PCP_ERROR_MIN = -33999
PCP_ERROR_MAX = -33000

# JSON-RPC 2.0 standard codes
JSONRPC_ERROR_MIN = -32768
JSONRPC_ERROR_MAX = -32000


class TestErrorCodes:
    """PCP-CONF-06: Error code compliance."""

    @pytest.mark.asyncio
    async def test_error_has_code_and_message(self, mock_robot_server):
        """All errors MUST have 'code' (int) and 'message' (string)."""
        resp = await rpc_call(
            mock_robot_server["base_url"], "nonexistent_method", {}
        )
        assert "error" in resp
        err = resp["error"]
        assert isinstance(err.get("code"), int), "error.code must be an integer"
        assert isinstance(err.get("message"), str), "error.message must be a string"

    @pytest.mark.asyncio
    async def test_method_not_found_code(self, mock_robot_server):
        """Method not found MUST return exactly -32601."""
        resp = await rpc_call(
            mock_robot_server["base_url"], "does_not_exist", {}
        )
        assert resp["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_parse_error_code(self, mock_robot_server):
        """Parse error MUST return exactly -32700."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_robot_server['base_url']}/mcp",
                data=b"}}broken{{",
                headers={"Content-Type": "application/json"},
            ) as resp:
                body = await resp.json()
                assert "error" in body
                assert body["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_error_id_matches_request(self, mock_robot_server):
        """Error response id MUST match the request id."""
        custom_id = 99
        resp = await rpc_call(
            mock_robot_server["base_url"], "nonexistent", {}, req_id=custom_id
        )
        assert resp["id"] == custom_id

    @pytest.mark.asyncio
    async def test_success_response_has_no_error_field(self, mock_robot_server):
        """Success responses MUST NOT include the 'error' field."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "actuations/execute",
            {"name": "open_gripper", "params": {}},
        )
        assert "error" not in resp, "Success response must not have 'error' field"
        assert "result" in resp

    @pytest.mark.asyncio
    async def test_error_response_has_no_result_field(self, mock_robot_server):
        """Error responses MUST NOT include the 'result' field (JSON-RPC spec)."""
        resp = await rpc_call(
            mock_robot_server["base_url"], "does_not_exist", {}
        )
        # Per JSON-RPC 2.0: either result or error, not both
        assert "error" in resp
        # result may be absent OR None; it MUST NOT be a real value
        result = resp.get("result")
        assert result is None, f"Error response should not have non-null result: {result}"

    @pytest.mark.asyncio
    async def test_jsonrpc_version_in_all_responses(self, mock_robot_server):
        """Every response MUST have jsonrpc='2.0'."""
        for method, params in [
            ("initialize", {"protocolVersion": "0.5"}),
            ("actuations/list", {}),
            ("pcp/ping", {}),
            ("nonexistent", {}),
        ]:
            resp = await rpc_call(mock_robot_server["base_url"], method, params)
            assert resp.get("jsonrpc") == "2.0", f"jsonrpc version wrong for {method}"
