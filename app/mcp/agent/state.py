class ConversationState:
    """
    Tek bir konuşma için basit state yönetimi yapar.

    Şimdilik pending_action RAM'de tutulur.
    Gerçek projede burası Redis, database veya session store olabilir.
    """

    def __init__(self):
        self.pending_action = None

    def has_pending_action(self) -> bool:
        return self.pending_action is not None

    def set_pending_action(self, pending_action: dict):
        self.pending_action = pending_action

    def get_pending_action(self):
        return self.pending_action

    def clear_pending_action(self):
        self.pending_action = None