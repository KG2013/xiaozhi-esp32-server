import asyncio
from core.providers.tts.dto.dto import SentenceType

TAG = __name__


async def handleWelcomeMessage(conn, msg_json):
    """处理welcome消息，发送欢迎词"""
    conn.logger.bind(tag=TAG).info("Welcome message received")
    
    # 发送欢迎词
    if conn.tts and conn.play_welcome_audio:
        # 使用从API获取的greetingMessage
        greeting_message = conn.config.get("greetingMessage")
        if greeting_message and greeting_message.strip():
            # 使用配置的欢迎语
            welcome_text = greeting_message.strip()
            # 判断欢迎语不为空时才调用生成音频的逻辑
            if welcome_text:
                # 生成TTS音频
                opus_packets = await asyncio.to_thread(conn.tts.to_tts, welcome_text)
                if opus_packets:
                    conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, welcome_text))
                    conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
                    conn.logger.bind(tag=TAG).info(f"欢迎词已发送: {welcome_text}")
        # 如果greetingMessage为空，则不发送任何欢迎语
    
    conn.logger.bind(tag=TAG).info("Welcome message processed")

