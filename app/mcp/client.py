import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)


def parse_mcp_result(result):
    """
    MCP tool sonucundaki text content'i JSON'a çevirir.
    """

    if not result.content:
        return None

    text = result.content[0].text

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("Mevcut MCP tools:")
            for tool in tools.tools:
                print("-", tool.name)

            user_result = await session.call_tool(
                "get_user_info",
                arguments={
                    "user_id": "demo_user"
                }
            )

            print("\nget_user_info sonucu:")
            print(parse_mcp_result(user_result))

            ticket_result = await session.call_tool(
                "create_ticket",
                arguments={
                    "title": "VPN sorunu",
                    "description": "VPN açılmıyor, kullanıcı bağlantı kuramıyor."
                }
            )

            print("\ncreate_ticket sonucu:")
            print(parse_mcp_result(ticket_result))


if __name__ == "__main__":
    asyncio.run(main())