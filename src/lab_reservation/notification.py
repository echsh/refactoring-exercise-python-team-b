class NotificationService:
    def send(self, user_id, message):
        raise NotImplementedError


class RecordingNotificationService(NotificationService):
    def __init__(self):
        self.sent_messages = []

    def send(self, user_id, message):
        self.sent_messages.append(f"{user_id}:{message}")
