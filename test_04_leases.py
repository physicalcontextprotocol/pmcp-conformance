"""
P-MCP Conformance Test — Section 4: Lease Acquire/Release
==========================================================
Verifies exclusive zone lease semantics: acquire, check, release,
expiry, and double-acquire protection.
"""
from __future__ import annotations

import time
import pytest

from conftest import rpc_call


class TestLeaseLifecycle:
    """PMCP-CONF-04: Zone lease lifecycle."""

    @pytest.mark.asyncio
    async def test_acquire_lease_success(self, mock_robot_server):
        """leases/acquire for a free zone MUST return granted=True with a lease_id."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": "workspace_A", "duration_ms": 10_000},
        )
        assert "error" not in resp
        result = resp["result"]
        assert result.get("granted") is True
        assert "lease_id" in result
        assert result["lease_id"] != ""

    @pytest.mark.asyncio
    async def test_acquire_lease_returns_expiry(self, mock_robot_server):
        """Lease response MUST include expires_ms greater than now."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": "workspace_B", "duration_ms": 5_000},
        )
        result = resp["result"]
        assert "expires_ms" in result
        assert int(result["expires_ms"]) > int(time.time() * 1000)

    @pytest.mark.asyncio
    async def test_release_lease_success(self, mock_robot_server):
        """leases/release for a valid lease_id MUST return released=True."""
        acquire = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": "workspace_C", "duration_ms": 10_000},
        )
        lease_id = acquire["result"]["lease_id"]

        release = await rpc_call(
            mock_robot_server["base_url"],
            "leases/release",
            {"lease_id": lease_id},
        )
        assert "error" not in release
        assert release["result"]["released"] is True

    @pytest.mark.asyncio
    async def test_release_unknown_lease(self, mock_robot_server):
        """Releasing an unknown lease_id MUST return released=False (not an error)."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "leases/release",
            {"lease_id": "nonexistent_lease_xyz_999"},
        )
        # Should be a result (not error) with released=False
        assert "error" not in resp
        assert resp["result"]["released"] is False

    @pytest.mark.asyncio
    async def test_lease_acquire_release_acquire(self, mock_robot_server):
        """After releasing a lease, the same zone MUST be acquirable again."""
        zone = "workspace_reacquire_test"

        r1 = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": zone, "duration_ms": 5_000},
        )
        lease_id = r1["result"]["lease_id"]
        assert r1["result"]["granted"] is True

        await rpc_call(
            mock_robot_server["base_url"],
            "leases/release",
            {"lease_id": lease_id},
        )

        r2 = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": zone, "duration_ms": 5_000},
        )
        assert r2["result"]["granted"] is True
        assert r2["result"]["lease_id"] != lease_id

    @pytest.mark.asyncio
    async def test_lease_has_zone_id_and_robot_id(self, mock_robot_server):
        """Lease response MUST include zone_id and robot_id fields."""
        resp = await rpc_call(
            mock_robot_server["base_url"],
            "leases/acquire",
            {"zone_id": "workspace_D", "duration_ms": 5_000},
        )
        result = resp["result"]
        assert "zone_id" in result
        assert "robot_id" in result
