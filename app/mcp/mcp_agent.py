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


def select_tool(user_message: str) -> dict:
    """
    Kullanıcı mesajına göre hangi MCP tool'unun çağrılacağını seçer.
    Şimdilik basit rule-based karar veriyoruz.
    """

    message_lower = user_message.lower()

    if "bilgilerim" in message_lower or "kullanıcı bilgim" in message_lower:
        return {
            "tool_name": "get_user_info",
            "arguments": {
                "user_id": "demo_user"
            },
            "requires_confirmation": False
        }

    if "ticket" in message_lower or "kayıt aç" in message_lower or "destek kaydı" in message_lower:
        return {
            "tool_name": "create_ticket",
            "arguments": {
                "title": "Kullanıcı destek talebi",
                "description": user_message
            },
            "requires_confirmation": True
        }

    return {
        "tool_name": None,
        "arguments": {},
        "requires_confirmation": False
    }

async def run_agent(user_message: str):
    """
    MCP server'a bağlanır, kullanıcı mesajına göre tool seçer ve MCP üzerinden çağırır.
    """

    selected = select_tool(user_message)

    if not selected["tool_name"]:
        return {
            "agent_type": "mcp_agent",
            "message": user_message,
            "answer": "Bu mesaj için uygun bir MCP tool seçilemedi."
        }

    if selected.get("requires_confirmation"):
        return {
            "agent_type": "mcp_agent",
            "message": user_message,
            "selected_tool": selected["tool_name"],
            "arguments": selected["arguments"],
            "requires_confirmation": True,
            "confirmation_message": "Bu işlem sistemde kayıt oluşturacak. Devam etmek istiyor musunuz?",
            "pending_action": {
                "tool_name": selected["tool_name"],
                "arguments": selected["arguments"]
            }
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                selected["tool_name"],
                arguments=selected["arguments"]
            )

            parsed_result = parse_mcp_result(result)

            return {
                "agent_type": "mcp_agent",
                "message": user_message,
                "selected_tool": selected["tool_name"],
                "arguments": selected["arguments"],
                "result": parsed_result
            }


async def execute_pending_action(pending_action: dict):
    """
    Kullanıcı onay verdikten sonra MCP tool'unu çalıştırır.
    """

    tool_name = pending_action.get("tool_name")
    arguments = pending_action.get("arguments", {})

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            parsed_result = parse_mcp_result(result)

            return {
                "agent_type": "mcp_agent",
                "executed_tool": tool_name,
                "arguments": arguments,
                "result": parsed_result
            }


async def main():
    questions = [
        "Benim bilgilerim nedir?",
        "VPN açılmıyor bunun için ticket açar mısın?",
        "Merhaba nasılsın?"
    ]

    for question in questions:
        print("=" * 80)
        print("Kullanıcı mesajı:", question)

        result = await run_agent(question)

        print("Agent sonucu:")
        print(result)

        if result.get("requires_confirmation"):
            print("\nAgent onay istiyor:")
            print(result["confirmation_message"])

            user_confirmation = "evet"

            print("Kullanıcı cevabı:")
            print(user_confirmation)

            if user_confirmation.lower() in ["evet", "tamam", "onaylıyorum", "olur"]:
                final_result = await execute_pending_action(
                    result["pending_action"]
                )

                print("Onay sonrası MCP sonucu:")
                print(final_result)
            else:
                print("İşlem iptal edildi.")


if __name__ == "__main__":
    asyncio.run(main())