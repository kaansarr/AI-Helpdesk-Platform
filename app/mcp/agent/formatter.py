def format_tool_answer(tool_name: str, result: dict) -> str:
    """
    MCP tool sonucunu kullanıcıya gösterilecek temiz cevaba çevirir.
    """

    if not isinstance(result, dict):
        return "İşlem sonucu beklenen formatta gelmedi. Lütfen logları kontrol edin."

    if tool_name == "get_user_info":
        return (
            f"Kullanıcı bilgilerin:\n"
            f"- Ad: {result.get('name')}\n"
            f"- User ID: {result.get('user_id')}\n"
            f"- Tenant: {result.get('tenant_id')}\n"
            f"- Rol: {result.get('role')}"
        )

    if tool_name == "search_documents":
        answer = result.get("answer", "Bu konu için bilgi bulunamadı.")
        sources = result.get("sources", [])

        source_text = ""

        if sources:
            first_source = sources[0]
            source_text = (
                f"\n\nKaynak:\n"
                f"- Başlık: {first_source.get('title')}\n"
                f"- Dosya: {first_source.get('source')}\n"
                f"- Kategori: {first_source.get('category')}"
            )

        return answer + source_text


    if tool_name == "list_tickets":
        tickets = result.get("tickets", [])

        if not tickets:
            return "Henüz destek kaydı bulunmuyor."

        lines = ["Son destek kayıtları:"]

        for ticket in tickets:
            lines.append(
                f"- {ticket.get('ticket_id')} | "
                f"{ticket.get('status')} | "
                f"{ticket.get('title')}"
            )

        return "\n".join(lines)


    if tool_name == "get_ticket_detail":
        if not result.get("found"):
            return result.get("message", "Destek kaydı bulunamadı.")

        ticket = result.get("ticket", {})

        return (
            f"Destek kaydı detayı:\n"
            f"- Ticket ID: {ticket.get('ticket_id')}\n"
            f"- Başlık: {ticket.get('title')}\n"
            f"- Açıklama: {ticket.get('description')}\n"
            f"- Durum: {ticket.get('status')}\n"
            f"- Oluşturulma: {ticket.get('created_at')}\n"
            f"- Güncellenme: {ticket.get('updated_at')}"
        )


    if tool_name == "update_ticket_status":
        if not result.get("updated"):
            return result.get("message", "Destek kaydı güncellenemedi.")

        ticket = result.get("ticket", {})

        return (
            f"Destek kaydı durumu güncellendi.\n"
            f"- Ticket ID: {ticket.get('ticket_id')}\n"
            f"- Başlık: {ticket.get('title')}\n"
            f"- Yeni durum: {ticket.get('status')}\n"
            f"- Güncellenme: {ticket.get('updated_at')}"
        )

    if tool_name == "create_ticket":
        return (
            f"Destek kaydı oluşturuldu.\n"
            f"- Ticket ID: {result.get('ticket_id')}\n"
            f"- Durum: {result.get('status')}\n"
            f"- Başlık: {result.get('title')}"
        )

    return "İşlem tamamlandı."