import asyncio

from app.mcp.agent.state import ConversationState
from app.mcp.agent.policy import detect_confirmation_intent
from app.mcp.llm_mcp_agent import run_llm_mcp_agent, execute_pending_action


async def main():
    print("MCP Helpdesk Agent başladı.")
    print("Çıkmak için 'exit' yazabilirsin.")
    print("-" * 80)

    state = ConversationState()

    while True:
        user_message = input("\nSen: ").strip()

        if user_message.lower() in ["exit", "quit", "çık", "cikis", "çıkış"]:
            print("Agent kapatıldı.")
            break

        if not user_message:
            continue

        if state.has_pending_action():
            confirmation_intent = detect_confirmation_intent(user_message)

            if confirmation_intent == "approve":
                result = await execute_pending_action(state.get_pending_action())

                print("\nAgent:")
                print(result.get("final_answer"))

                state.clear_pending_action()
                continue

            if confirmation_intent == "reject":
                print("\nAgent:")
                print("İşlem iptal edildi.")

                state.clear_pending_action()
                continue

            print("\nAgent:")
            print("Bekleyen bir işlem var. Lütfen onayladığını veya iptal etmek istediğini belirt.")
            continue

        result = await run_llm_mcp_agent(user_message)

        if result.get("requires_confirmation"):
            state.set_pending_action(result.get("pending_action"))

            print("\nAgent:")
            print(result.get("confirmation_message"))
            continue

        if result.get("final_answer"):
            print("\nAgent:")
            print(result.get("final_answer"))
            continue

        print("\nAgent:")
        print(result.get("answer", "Bu mesaj için cevap üretilemedi."))


if __name__ == "__main__":
    asyncio.run(main())