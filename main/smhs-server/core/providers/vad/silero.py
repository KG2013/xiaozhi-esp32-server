import time
import numpy as np
import torch
from config.logger import setup_logging
from core.providers.vad.base import VADProviderBase
from core.utils.util import decode_opus_to_pcm

TAG = __name__
logger = setup_logging()

# VAD模型要求的音频格式
VAD_TARGET_SAMPLE_RATE = 16000
VAD_TARGET_CHANNELS = 1


class VADProvider(VADProviderBase):
    def __init__(self, config):
        logger.bind(tag=TAG).info("SileroVAD", config)
        self.model, _ = torch.hub.load(
            repo_or_dir=config["model_dir"],
            source="local",
            model="silero_vad",
            force_reload=False,
        )

        # 处理空字符串的情况
        threshold = config.get("threshold", "0.5")
        threshold_low = config.get("threshold_low", "0.2")
        min_silence_duration_ms = config.get("min_silence_duration_ms", "1000")

        self.vad_threshold = float(threshold) if threshold else 0.5
        self.vad_threshold_low = float(threshold_low) if threshold_low else 0.2

        self.silence_threshold_ms = (
            int(min_silence_duration_ms) if min_silence_duration_ms else 1000
        )

        # 至少要多少帧才算有语音
        self.frame_window_threshold = 3

    def __del__(self):
        if hasattr(self, 'decoder') and self.decoder is not None:
            try:
                del self.decoder
            except Exception:
                pass

    def is_vad(self, conn, opus_packet):
        # 手动模式：直接返回True，不进行实时VAD检测，所有音频都缓存
        if conn.client_listen_mode == "manual":
            return True
            
        try:
            # 获取连接的Opus配置
            opus_config = getattr(conn, 'opus_config', None)
            
            # 验证音频包
            if not opus_packet or len(opus_packet) == 0:
                logger.bind(tag=TAG).warning("收到空的Opus数据包")
                return False
            
            # 使用统一的解码方法，自动转换为16000Hz单声道（VAD模型要求的格式）
            pcm_data = decode_opus_to_pcm(
                [opus_packet], 
                opus_config, 
                target_sample_rate=VAD_TARGET_SAMPLE_RATE, 
                target_channels=VAD_TARGET_CHANNELS
            )
            
            if not pcm_data:
                logger.bind(tag=TAG).warning(
                    f"无法解码Opus数据包(大小:{len(opus_packet)}字节)，可能是数据损坏"
                )
                return False
            
            # 将解码后的PCM数据添加到缓冲区
            combined_pcm = b"".join(pcm_data)
            conn.client_audio_buffer.extend(combined_pcm)

            # 处理缓冲区中的完整帧（每次处理512采样点）
            client_have_voice = False
            while len(conn.client_audio_buffer) >= 512 * 2:
                # 提取前512个采样点（1024字节）
                chunk = conn.client_audio_buffer[: 512 * 2]
                conn.client_audio_buffer = conn.client_audio_buffer[512 * 2 :]

                # 转换为模型需要的张量格式
                audio_int16 = np.frombuffer(chunk, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_float32)

                # 检测语音活动
                with torch.no_grad():
                    speech_prob = self.model(audio_tensor, 16000).item()

                # 双阈值判断
                if speech_prob >= self.vad_threshold:
                    is_voice = True
                elif speech_prob <= self.vad_threshold_low:
                    is_voice = False
                else:
                    is_voice = conn.last_is_voice

                # 声音没低于最低值则延续前一个状态，判断为有声音
                conn.last_is_voice = is_voice

                # 更新滑动窗口
                conn.client_voice_window.append(is_voice)
                client_have_voice = (
                    conn.client_voice_window.count(True) >= self.frame_window_threshold
                )

                # 如果之前有声音，但本次没有声音，且与上次有声音的时间差已经超过了静默阈值，则认为已经说完一句话
                # manual 模式下不通过 VAD 静音检测自动触发停止，只等待用户明确发送 stop 信号
                if conn.client_have_voice and not client_have_voice:
                    stop_duration = time.time() * 1000 - conn.last_activity_time
                    if stop_duration >= self.silence_threshold_ms and conn.client_listen_mode != "manual":
                        conn.client_voice_stop = True
                if client_have_voice:
                    conn.client_have_voice = True
                    conn.last_activity_time = time.time() * 1000

            return client_have_voice
        except Exception as e:
            logger.bind(tag=TAG).error(f"处理音频包时发生错误: {e}")
            import traceback
            logger.bind(tag=TAG).debug(f"错误详情: {traceback.format_exc()}")
            return False
