import asyncio
from core.providers.tts.dto.dto import SentenceType

TAG = __name__


async def handleLeaveMessage(conn, msg_json):
    """处理leave消息，发送结束语并关闭连接"""
    conn.logger.bind(tag=TAG).info("Leave message received")
    
    # 发送结束语
    if conn.tts and conn.play_welcome_audio:
        # 使用从API获取的leaveMessage
        leave_message = conn.config.get("leaveMessage")
        if leave_message and leave_message.strip():
            # 使用配置的结束语
            farewell_text = leave_message.strip()
            # 判断结束语不为空时才调用生成音频的逻辑
            if farewell_text:
                # 重置 tts_audio_first_sentence 标志，确保发送 "start" 状态
                conn.tts.tts_audio_first_sentence = True
                # 生成TTS音频
                opus_packets = await asyncio.to_thread(conn.tts.to_tts, farewell_text)
                if opus_packets:
                    conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, farewell_text))
                    conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
                    conn.logger.bind(tag=TAG).info(f"结束语已发送: {farewell_text}")
        # 如果leaveMessage为空，则不发送任何结束语
    
    # 设置关闭标志，在聊天完成后关闭连接
    # conn.close_after_chat = True
    # conn.logger.bind(tag=TAG).info("Leave message processed, connection will close after chat")

