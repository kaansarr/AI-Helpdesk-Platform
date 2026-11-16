import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.mcp.agent.formatter import format_tool_answer
from app.mcp.agent.planner import ask_llm_for_tool_decision
from app.mcp.agent.policy import (
    RISKY_TOOLS,
    tool_requires_confirmation,
    validate_decision,
)
from app.mcp.utils.logger import get_logger


logger = get_logger(__name__)


# MCP Server bağlantı ayarları
server_params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp.server"]
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


async def call_mcp_tool(tool_name: str, arguments: dict):
    """
    MCP Server'a bağlanır ve belirtilen tool'u çalıştırır.
    """

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments
                )

                if result.is_error:
                    logger.error(
                        f"MCP tool error: {tool_name}, Result: {result}"
                    )

                    return {
                        "success": False,
                        "error": "MCP tool hata döndürdü.",
                        "message": "Tool çalıştırılırken bir hata oluştu."
                    }

                parsed_result = parse_mcp_result(result)

                if not isinstance(parsed_result, dict):
                    logger.error(
                        f"MCP tool beklenen dict formatında sonuç döndürmedi. "
                        f"Tool: {tool_name}, Result: {parsed_result}"
                    )

                    return {
                        "success": False,
                        "error": str(parsed_result),
                        "message": "Tool sonucu beklenen formatta gelmedi."
                    }

                return {
                    "success": True,
                    "data": parsed_result
                }

    except Exception as error:
        logger.exception(
            f"MCP tool execution failed. "
            f"Tool: {tool_name}, Arguments: {arguments}"
        )

        return {
            "success": False,
            "error": str(error),
            "message": "Tool çalıştırılırken teknik bir hata oluştu."
        }


def get_confirmation_message(tool_name: str, arguments: dict) -> str:
    """
    Kullanıcıya yapılacak işlemi açıkça gösteren onay mesajını üretir.
    """

    if tool_name == "create_ticket":
        return (
            "Yeni bir IT destek kaydı oluşturulacak.\n\n"
            f"Başlık: {arguments.get('title')}\n"
            f"Açıklama: {arguments.get('description')}\n\n"
            "Bu işlemi onaylıyor musunuz?"
        )

    if tool_name == "update_ticket_status":
        return (
            "Mevcut destek kaydının durumu güncellenecek.\n\n"
            f"Ticket ID: {arguments.get('ticket_id')}\n"
            f"Yeni durum: {arguments.get('status')}\n\n"
            "Bu işlemi onaylıyor musunuz?"
        )

    return (
        f"'{tool_name}' işlemi gerçekleştirilecek.\n\n"
        "Bu işlemi onaylıyor musunuz?"
    )


async def run_llm_mcp_agent(user_message: str):
    """
    LLM tabanlı MCP Agent.

    Akış:
    1. LLM Planner uygun tool'u seçer.
    2. Policy seçilen tool'u ve parametrelerini doğrular.
    3. Riskli tool için kullanıcı onayı istenir.
    4. Onay gerekmiyorsa MCP tool çalıştırılır.
    5. Sonuç kullanıcıya gösterilir.
    """

    logger.info(f"User message received: {user_message}")

    # 1. LLM Planner
    raw_decision = ask_llm_for_tool_decision(user_message)

    logger.info(f"Raw LLM decision: {raw_decision}")

    # 2. Policy Validation
    decision = validate_decision(
        raw_decision,
        user_message
    )

    logger.info(f"Validated decision: {decision}")

    if decision.get("error"):
        logger.warning(
            f"Decision validation failed: {decision.get('error')}"
        )

        return {
            "agent_type": "llm_mcp_agent",
            "message": user_message,
            "raw_decision": raw_decision,
            "decision": decision,
            "answer": "Tool kararı güvenli bulunmadı."
        }

    tool_name = decision.get("tool_name")
    arguments = decision.get("arguments", {})

    # 3. Tool gerekmiyorsa
    if not tool_name:
        logger.info(
            "No MCP tool required for this message."
        )

        return {
            "agent_type": "llm_mcp_agent",
            "message": user_message,
            "raw_decision": raw_decision,
            "decision": decision,
            "answer": "Bu mesaj için MCP tool çağırmaya gerek yok."
        }

    # 4. Riskli işlemler için kullanıcı onayı
    if tool_requires_confirmation(tool_name):

        logger.info(
            f"Confirmation required for tool: {tool_name}"
        )

        confirmation_message = get_confirmation_message(
            tool_name,
            arguments
        )

        return {
            "agent_type": "llm_mcp_agent",
            "message": user_message,
            "raw_decision": raw_decision,
            "decision": decision,
            "selected_tool": tool_name,
            "arguments": arguments,
            "requires_confirmation": True,
            "confirmation_message": confirmation_message,
            "pending_action": {
                "tool_name": tool_name,
                "arguments": arguments
            }
        }

    # 5. Onay gerektirmeyen MCP tool'ları çalıştır
    logger.info(
        f"Executing MCP tool: {tool_name} with arguments: {arguments}"
    )

    tool_response = await call_mcp_tool(
        tool_name,
        arguments
    )

    if not tool_response.get("success"):
        return {
            "agent_type": "llm_mcp_agent",
            "message": user_message,
            "selected_tool": tool_name,
            "arguments": arguments,
            "error": tool_response.get("error"),
            "final_answer": (
                "İşlem sırasında bir hata oluştu. "
                "Lütfen daha sonra tekrar deneyin."
            )
        }

    result = tool_response.get("data")

    if result.get("success") is False:
        logger.error(
            f"MCP tool business error: {result}"
        )

        return {
            "agent_type": "llm_mcp_agent",
            "message": user_message,
            "selected_tool": tool_name,
            "arguments": arguments,
            "error": result.get("error") or "MCP işlemi başarısız.",
            "final_answer": (
                result.get("message") or "İşlem tamamlanamadı."
            )
        }

    logger.info(
        f"MCP tool executed successfully: {tool_name}"
    )

    final_answer = format_tool_answer(
        tool_name,
        result
    )

    return {
        "agent_type": "llm_mcp_agent",
        "message": user_message,
        "raw_decision": raw_decision,
        "decision": decision,
        "selected_tool": tool_name,
        "arguments": arguments,
        "result": result,
        "final_answer": final_answer
    }


async def execute_pending_action(pending_action: dict):
    """
    Kullanıcı onay verdikten sonra MCP tool'unu çalıştırır.
    """

    tool_name = pending_action.get("tool_name")
    arguments = pending_action.get("arguments", {})

    # Onay üzerinden yalnızca izin verilen, onay gerektiren araçlar çalışabilir.
    if tool_name not in RISKY_TOOLS or not tool_requires_confirmation(tool_name):
        logger.warning(
            f"Invalid pending action tool: {tool_name}"
        )

        return {
            "agent_type": "llm_mcp_agent",
            "executed_tool": None,
            "error": "Geçersiz onay işlemi.",
            "final_answer": "Bu işlem onay üzerinden gerçekleştirilemez."
        }

    if not isinstance(arguments, dict):
        return {
            "agent_type": "llm_mcp_agent",
            "executed_tool": None,
            "error": "Geçersiz işlem parametreleri.",
            "final_answer": "İşlem parametreleri geçersiz."
        }

    logger.info(
        f"Executing pending action: {tool_name} "
        f"with arguments: {arguments}"
    )

    tool_response = await call_mcp_tool(
        tool_name,
        arguments
    )

    if not tool_response.get("success"):
        return {
            "agent_type": "llm_mcp_agent",
            "executed_tool": tool_name,
            "arguments": arguments,
            "error": tool_response.get("error"),
            "final_answer": (
                "İşlem sırasında bir hata oluştu. "
                "Lütfen daha sonra tekrar deneyin."
            )
        }

    result = tool_response.get("data")

    if result.get("success") is False:
        logger.error(
            f"MCP tool business error: {result}"
        )

        return {
            "agent_type": "llm_mcp_agent",
            "executed_tool": tool_name,
            "arguments": arguments,
            "error": result.get("error") or "MCP işlemi başarısız.",
            "final_answer": (
                result.get("message") or "İşlem tamamlanamadı."
            )
        }

    logger.info(
        f"Pending action executed successfully: {tool_name}"
    )

    final_answer = format_tool_answer(
        tool_name,
        result
    )

    return {
        "agent_type": "llm_mcp_agent",
        "executed_tool": tool_name,
        "arguments": arguments,
        "result": result,
        "final_answer": final_answer
    }