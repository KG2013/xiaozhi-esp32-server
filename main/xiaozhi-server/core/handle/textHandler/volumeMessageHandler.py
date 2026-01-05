from typing import Dict, Any

from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType

TAG = __name__


class VolumeTextMessageHandler(TextMessageHandler):
    """音量控制消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.VOLUME

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        """
        处理音量调节消息
        
        设备端按音量加减按钮时会发送此消息通知服务端当前音量值
        """
        volume_value = msg_json.get("value", 0)
        conn.logger.bind(tag=TAG).debug(f"设备音量调节: {volume_value}")
