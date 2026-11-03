from mcp.server import MCPServer

mcp = MCPServer("agent-ai-engineer-lab")

@mcp.tool()
def gpu_status() -> dict:
    """return available GPU information"""
    return {
        "GPU": "A100",
        "memory_gb": 40,
        "available": True,
    }

if __name__ == "__main__":
    mcp.run()