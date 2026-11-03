
from mcp.server import MCPServer

# for validation of input parameters, we can use Pydantic's Field and Annotated types
from typing import Annotated
from pydantic import Field


mcp = MCPServer("agent-platform-lab")


@mcp.tool()
def gpu_status() -> dict:
    """Get GPU identity and currently available memory."""
    return {
        "gpu": "NVIDIA A100",
        "available_memory_gb": 40.0,
        "available": True,
    }


# # type annotations tell MCP that both inputs must be numeric.
# @mcp.tool()
# def estimate_training_fit(
#     available_memory_gb: float,
#     required_memory_gb: float,
# ) -> dict:
#     """Check whether a workload fits in available GPU memory.

#     First call gpu_status to obtain available_memory_gb.
#     """
#     if available_memory_gb < 0 or required_memory_gb < 0:
#         raise ValueError("Memory values must be non-negative")

#     remaining = available_memory_gb - required_memory_gb

#     return {
#         "fits_in_memory": remaining >= 0,
#         "remaining_memory_gb": round(remaining, 2),
#     }


@mcp.tool()
def estimate_training_fit(
    available_memory_gb: Annotated[
        float, Field(ge=0, le=1000)
    ],
    required_memory_gb: Annotated[
        float, Field(ge=0, le=1000)
    ],
) -> dict:
    """Check if a workload fits in GPU memory."""
    remaining = available_memory_gb - required_memory_gb

    return {
        "fits_in_memory": remaining >= 0,
        "remaining_memory_gb": round(remaining, 2),
    }



import asyncio


@mcp.tool()
async def gpu_utilization() -> dict:
    """Return current GPU utilization (mock data)."""
    await asyncio.sleep(2)  # Simulate I/O latency
    return {"utilization_percent": 75}


@mcp.tool()
async def gpu_temperature() -> dict:
    """Return current GPU temperature (mock data)."""
    await asyncio.sleep(2)  # Simulate I/O latency
    return {"temperature_celsius": 65}



if __name__ == "__main__":
    mcp.run()
