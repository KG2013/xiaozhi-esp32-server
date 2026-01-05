"""
Opus编码工具类
将PCM音频数据编码为Opus格式
"""

import logging
import traceback
import numpy as np
from opuslib_next import Encoder
from opuslib_next import constants
from typing import Optional, Callable, Any


class OpusConfig:
    """Opus配置类 - 统一管理编码和解码的配置参数"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, frame_duration_ms: int = 20,vbr: bool = True):
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_duration_ms = frame_duration_ms
        self.sample_points = int(sample_rate * frame_duration_ms / 1000)
        self.vbr = vbr
        self.bitrate = sample_rate * channels
        self.frame_size = int(self.bitrate/8*frame_duration_ms/1000)  # 比特率= 目标字节数×8 / 帧时长= 40×8 / 0.02 =16,000bps
        self.enc_frame_duration_ms = frame_duration_ms

class OpusEncoderUtils:
    """PCM到Opus的编码器"""

    def __init__(self, sample_rate: int, channels: int, frame_size_ms: int, vbr: bool = True, bitrate: int = None):
        """
        初始化Opus编码器

        Args:
            sample_rate: 采样率 (Hz)
            channels: 通道数 (1=单声道, 2=立体声)
            frame_size_ms: 帧大小 (毫秒)
            vbr: 是否使用可变码率 (True=VBR, False=固定码率)
            bitrate: 码率 (bps)，如果为None则使用默认值 sample_rate * channels
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size_ms = frame_size_ms
        # 计算每帧样本数 = 采样率 * 帧大小(毫秒) / 1000
        self.frame_size = (sample_rate * frame_size_ms) // 1000
        # 总帧大小 = 每帧样本数 * 通道数
        self.total_frame_size = self.frame_size * channels

        # VBR和码率设置
        self.vbr = vbr
        # 如果未指定码率，使用默认值：sample_rate * channels
        if bitrate is None:
            self.bitrate = sample_rate * channels
        else:
            self.bitrate = bitrate
        
        self.complexity = 10  # 最高质量

        # 当frame_duration=20时，每3帧(60ms)合并为一个元素
        self.frames_per_group = 3 if frame_size_ms == 20 else 1
        self.temp_frames = []  # 临时存储当前组的帧

        # 缓冲区初始化为空
        self.buffer = np.array([], dtype=np.int16)

        try:
            # 创建Opus编码器
            self.encoder = Encoder(
                sample_rate, channels, constants.APPLICATION_AUDIO  # 音频优化模式
            )
            # 设置VBR模式和码率
            self.encoder.vbr = self.vbr
            self.encoder.bitrate = self.bitrate
            self.encoder.complexity = self.complexity
            self.encoder.signal = constants.SIGNAL_VOICE  # 语音信号优化
        except Exception as e:
            logging.error(f"初始化Opus编码器失败: {e}")
            raise RuntimeError("初始化失败") from e

    def reset_state(self):
        """重置编码器状态"""
        self.encoder.reset_state()
        self.buffer = np.array([], dtype=np.int16)
        self.temp_frames = []  # 重置帧合并缓冲区

    def encode_pcm_to_opus_stream(self, pcm_data: bytes, end_of_stream: bool, callback: Callable[[Any], Any]):
        """
        将PCM数据编码为Opus格式，以流式方式进行处理

        Args:
            pcm_data: PCM字节数据
            end_of_stream: 是否为流的结束,
            callback: opus处理方法

        Returns:
            Opus数据包列表
        """
        # 将字节数据转换为short数组
        new_samples = self._convert_bytes_to_shorts(pcm_data)

        # 校验PCM数据
        self._validate_pcm_data(new_samples)

        # 将新数据追加到缓冲区
        self.buffer = np.append(self.buffer, new_samples)

        offset = 0

        # 处理所有完整帧
        while offset <= len(self.buffer) - self.total_frame_size:
            frame = self.buffer[offset : offset + self.total_frame_size]
            output = self._encode(frame)
            if output:
                # 根据frames_per_group决定是否合并帧
                if self.frames_per_group > 1:
                    # 需要合并多帧
                    self.temp_frames.append(output)
                    # 当累积到指定数量的帧时，合并并回调
                    if len(self.temp_frames) == self.frames_per_group:
                        merged_data = b''.join(self.temp_frames)
                        callback(merged_data)
                        logging.debug(f"合并{self.frames_per_group}帧({self.frame_size_ms * self.frames_per_group}ms)回调")
                        self.temp_frames = []  # 清空临时列表
                else:
                    # 单帧直接回调
                    callback(output)
            offset += self.total_frame_size

        # 保留未处理的样本
        self.buffer = self.buffer[offset:]

        # 流结束时处理剩余数据
        if end_of_stream:
            # 处理缓冲区中的剩余数据
            if len(self.buffer) > 0:
                # 创建最后一帧并用0填充
                last_frame = np.zeros(self.total_frame_size, dtype=np.int16)
                last_frame[: len(self.buffer)] = self.buffer
                output = self._encode(last_frame)
                if output:
                    if self.frames_per_group > 1:
                        self.temp_frames.append(output)
                    else:
                        callback(output)
                self.buffer = np.array([], dtype=np.int16)
            
            # 处理剩余的不足一组的帧
            if self.temp_frames:
                if self.frames_per_group > 1:
                    merged_data = b''.join(self.temp_frames)
                    callback(merged_data)
                    logging.debug(f"合并剩余{len(self.temp_frames)}帧回调")
                else:
                    for frame in self.temp_frames:
                        callback(frame)
                self.temp_frames = []

    def _encode(self, frame: np.ndarray) -> Optional[bytes]:
        """编码一帧音频数据"""
        try:
            # 编码器已释放，跳过编码
            if not hasattr(self, 'encoder') or self.encoder is None:
                return None
            # 将numpy数组转换为bytes
            frame_bytes = frame.tobytes()
            # opuslib要求输入字节数必须是channels*2的倍数
            encoded = self.encoder.encode(frame_bytes, self.frame_size)
            return encoded
        except Exception as e:
            logging.error(f"Opus编码失败: {e}")
            traceback.print_exc()
            return None

    def _convert_bytes_to_shorts(self, bytes_data: bytes) -> np.ndarray:
        """将字节数组转换为short数组 (16位PCM)"""
        # 假设输入是小端字节序的16位PCM
        return np.frombuffer(bytes_data, dtype=np.int16)

    def _validate_pcm_data(self, pcm_shorts: np.ndarray) -> None:
        """验证PCM数据是否有效"""
        # 16位PCM数据范围是 -32768 到 32767
        if np.any((pcm_shorts < -32768) | (pcm_shorts > 32767)):
            invalid_samples = pcm_shorts[(pcm_shorts < -32768) | (pcm_shorts > 32767)]
            logging.warning(f"发现无效PCM样本: {invalid_samples[:5]}...")
            # 在实际应用中可以选择裁剪而不是抛出异常
            # np.clip(pcm_shorts, -32768, 32767, out=pcm_shorts)

    def close(self):
        """关闭编码器并释放资源"""
        if hasattr(self, 'encoder') and self.encoder:
            try:
                del self.encoder
                self.encoder = None
            except Exception as e:
                logging.error(f"Error releasing Opus encoder: {e}")