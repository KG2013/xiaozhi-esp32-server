"""
TTS上报功能已集成到ConnectionHandler类中。

上报功能包括：
1. 每个连接对象拥有自己的上报队列和处理线程
2. 上报线程的生命周期与连接对象绑定
3. 使用ConnectionHandler.enqueue_tts_report方法进行上报

具体实现请参考core/connection.py中的相关代码。
"""

import time

from config.manage_api_client import report as manage_report
from core.utils.util import decode_opus_to_pcm
from core.utils.opus_encoder_utils import OpusConfig
from typing import Optional

TAG = __name__


def report(conn, type, text, opus_data, report_time):
    """执行聊天记录上报操作

    Args:
        conn: 连接对象
        type: 上报类型，1为用户，2为智能体
        text: 合成文本
        opus_data: opus音频数据
        report_time: 上报时间
    """
    try:
        if opus_data:
            audio_data = opus_to_wav(conn, opus_data)
        else:
            audio_data = None
        # 执行上报
        manage_report(
            ssid=conn.device_id,
            session_id=conn.session_id,
            chat_type=type,
            content=text,
            audio=audio_data,
            report_time=report_time,
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"聊天记录上报失败: {e}")


def opus_to_wav(conn, opus_data):
    """将Opus数据转换为WAV格式的字节流

    Args:
        conn: 连接对象
        opus_data: opus音频数据

    Returns:
        bytes: WAV格式的音频数据
    """
    # 获取Opus配置，如果连接对象没有配置则使用None（将使用默认配置）
    opus_config = getattr(conn, 'opus_config', None)
    
    # 使用util.py中的统一解码函数进行解码
    pcm_data = decode_opus_to_pcm(opus_data, opus_config)

    if not pcm_data:
        raise ValueError("没有有效的PCM数据")

    # 创建WAV文件头
    pcm_data_bytes = b"".join(pcm_data)
    num_samples = len(pcm_data_bytes) // 2  # 16-bit samples

    # 获取采样率，如果有配置则使用配置的采样率，否则使用默认16000
    sample_rate = opus_config.sample_rate if opus_config else 16000
    num_channels = opus_config.channels if opus_config else 1
    byte_rate = sample_rate * num_channels * 2  # 采样率 * 通道数 * 2字节(16bit)
    block_align = num_channels * 2  # 通道数 * 2字节(16bit)

    # WAV文件头
    wav_header = bytearray()
    wav_header.extend(b"RIFF")  # ChunkID
    wav_header.extend((36 + len(pcm_data_bytes)).to_bytes(4, "little"))  # ChunkSize
    wav_header.extend(b"WAVE")  # Format
    wav_header.extend(b"fmt ")  # Subchunk1ID
    wav_header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
    wav_header.extend((1).to_bytes(2, "little"))  # AudioFormat (PCM)
    wav_header.extend((num_channels).to_bytes(2, "little"))  # NumChannels
    wav_header.extend((sample_rate).to_bytes(4, "little"))  # SampleRate
    wav_header.extend((byte_rate).to_bytes(4, "little"))  # ByteRate
    wav_header.extend((block_align).to_bytes(2, "little"))  # BlockAlign
    wav_header.extend((16).to_bytes(2, "little"))  # BitsPerSample
    wav_header.extend(b"data")  # Subchunk2ID
    wav_header.extend(len(pcm_data_bytes).to_bytes(4, "little"))  # Subchunk2Size

    # 返回完整的WAV数据
    return bytes(wav_header) + pcm_data_bytes


def enqueue_tts_report(conn, text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_tts_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """将TTS数据加入上报队列

    Args:
        conn: 连接对象
        text: 合成文本
        opus_data: opus音频数据
    """
    try:
        # 使用连接对象的队列，传入文本和二进制数据而非文件路径
        if conn.chat_history_conf == 2:
            conn.report_queue.put((2, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"TTS数据已加入上报队列: {conn.device_id}, 音频大小: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((2, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"TTS数据已加入上报队列: {conn.device_id}, 不上报音频"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"加入TTS上报队列失败: {text}, {e}")


def enqueue_asr_report(conn, text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_asr_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """将ASR数据加入上报队列

    Args:
        conn: 连接对象
        text: 合成文本
        opus_data: opus音频数据
    """
    try:
        # 使用连接对象的队列，传入文本和二进制数据而非文件路径
        if conn.chat_history_conf == 2:
            conn.report_queue.put((1, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"ASR数据已加入上报队列: {conn.device_id}, 音频大小: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((1, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"ASR数据已加入上报队列: {conn.device_id}, 不上报音频"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).debug(f"加入ASR上报队列失败: {text}, {e}")
