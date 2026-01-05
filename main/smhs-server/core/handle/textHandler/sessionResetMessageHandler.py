"""
Session Reset 消息处理器
处理设备重连时的 session_reset 消息
"""

from typing import Dict, Any
from core.handle.textMessageType import TextMessageType
from core.handle.textMessageHandler import TextMessageHandler

TAG = __name__


class SessionResetTextMessageHandler(TextMessageHandler):
    """Session Reset 消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.SESSION_RESET

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """
        处理 session_reset 消息
        
        当设备重连时，客户端会发送此消息通知服务端重置会话状态
        """
        device_id = msg_json.get("device_id", "unknown")
        reason = msg_json.get("reason", "unknown")
        timestamp = msg_json.get("timestamp", 0)
        
        conn.logger.bind(tag=TAG).info(
            f"设备重连通知 - 设备: {device_id}, 原因: {reason}, 时间戳: {timestamp}"
        )
        
        # 这里只记录日志，不做任何状态清理
        # 让系统保持原有的运行状态，避免干扰正常流程
