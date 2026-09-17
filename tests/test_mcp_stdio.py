"""MCP stdio integration contract.

This test uses the SDK transport rather than importing MCP tool functions.  A
concurrent ``list_tools`` call works around the installed SDK 1.29.1 reader
queue issue observed after the first post-initialize request.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def _call_with_tool_discovery(session: ClientSession, name: str, arguments: dict):
    call = asyncio.create_task(session.call_tool(name, arguments))
    await asyncio.sleep(0.1)
    discovery = asyncio.create_task(session.list_tools())
    done, pending = await asyncio.wait(
        {call, discovery}, timeout=15, return_when=asyncio.ALL_COMPLETED
    )
    for task in pending:
        task.cancel()
    assert call in done, f"MCP call timed out: {name}"
    return call.result()


def test_mcp_stdio_bootstrap_cycle_uses_real_sdk(tmp_path: Path):
    (tmp_path / "cortex.toml").write_text(
        "[project]\nname = \"mcp-test\"\nphase = \"develop\"\n",
        encoding="utf-8",
    )

    async def run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "cortex.server.mcp_server"],
            env={**os.environ, "CORTEX_ROOT": str(tmp_path)},
            cwd=Path(__file__).parents[1],
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await asyncio.wait_for(session.initialize(), 15)
                assert initialized.serverInfo.name == "cortex"
                init = await _call_with_tool_discovery(
                    session, "cortex_init", {"branch": "main", "task": "MCP bootstrap"}
                )
                assert init.isError is False
                assert "CORTEX CONTEXT" in init.content[0].text
                status = await _call_with_tool_discovery(session, "cortex_status", {})
                assert '"sessions": 1' in status.content[0].text

    asyncio.run(run())
