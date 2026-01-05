from typing import Dict, Any

from core.handle.leaveHandle import handleLeaveMessage
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType


class LeaveTextMessageHandler(TextMessageHandler):
    """Leave消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LEAVE

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        await handleLeaveMessage(conn, msg_json)

