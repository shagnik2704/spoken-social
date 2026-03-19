from fastmcp import FastMCP
mcp=FastMCP("spoken-social")

if __name__=="main":mcp.run(transport="sse",host="0.0.0.0",port=8081)
