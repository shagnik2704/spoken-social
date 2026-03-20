from mcp_server.core import mcp

# Import tool modules so they register their @mcp.tool() decorators
import mcp_server.tools.database
import mcp_server.tools.prometheus
import mcp_server.tools.loki
# Alerting tools excluded per your plan!

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8081)
