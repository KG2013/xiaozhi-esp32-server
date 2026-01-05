from typing import Dict, Any

from core.handle.greetingHandle import handleWelcomeMessage
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType


class GreetingTextMessageHandler(TextMessageHandler):
    """Welcome消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.WELCOME

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        await handleWelcomeMessage(conn, msg_json)

