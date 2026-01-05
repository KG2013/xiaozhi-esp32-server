import re
import os
import json
import copy
import wave
import socket
import requests
import subprocess
import numpy as np
import opuslib_next
from io import BytesIO
from loguru import logger
from core.utils import p3
from pydub import AudioSegment
from typing import Callable, Any
from core.utils.opus_encoder_utils import OpusConfig

TAG = __name__
emoji_map = {
    "neutral": "😶",
    "happy": "🙂",
    "laughing": "😆",
    "funny": "😂",
    "sad": "😔",
    "angry": "😠",
    "crying": "😭",
    "loving": "😍",
    "embarrassed": "😳",
    "surprised": "😲",
    "shocked": "😱",
    "thinking": "🤔",
    "winking": "😉",
    "cool": "😎",
    "relaxed": "😌",
    "delicious": "🤤",
    "kissy": "😘",
    "confident": "😏",
    "sleepy": "😴",
    "silly": "😜",
    "confused": "🙄",
}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to Google's DNS servers
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return "127.0.0.1"


def is_private_ip(ip_addr):
    """
    Check if an IP address is a private IP address (compatible with IPv4 and IPv6).

    @param {string} ip_addr - The IP address to check.
    @return {bool} True if the IP address is private, False otherwise.
    """
    try:
        # Validate IPv4 or IPv6 address format
        if not re.match(
            r"^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", ip_addr
        ):
            return False  # Invalid IP address format

        # IPv4 private address ranges
        if "." in ip_addr:  # IPv4 address
            ip_parts = list(map(int, ip_addr.split(".")))
            if ip_parts[0] == 10:
                return True  # 10.0.0.0/8 range
            elif ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                return True  # 172.16.0.0/12 range
            elif ip_parts[0] == 192 and ip_parts[1] == 168:
                return True  # 192.168.0.0/16 range
            elif ip_addr == "127.0.0.1":
                return True  # Loopback address
            elif ip_parts[0] == 169 and ip_parts[1] == 254:
                return True  # Link-local address 169.254.0.0/16
            else:
                return False  # Not a private IPv4 address
        else:  # IPv6 address
            ip_addr = ip_addr.lower()
            if ip_addr.startswith("fc00:") or ip_addr.startswith("fd00:"):
                return True  # Unique Local Addresses (FC00::/7)
            elif ip_addr == "::1":
                return True  # Loopback address
            elif ip_addr.startswith("fe80:"):
                return True  # Link-local unicast addresses (FE80::/10)
            else:
                return False  # Not a private IPv6 address

    except (ValueError, IndexError):
        return False  # IP address format error or insufficient segments


def get_ip_info(ip_addr, logger):
    try:
        # 导入全局缓存管理器
        from core.utils.cache.manager import cache_manager, CacheType

        # 先从缓存获取
        cached_ip_info = cache_manager.get(CacheType.IP_INFO, ip_addr)
        if cached_ip_info is not None:
            return cached_ip_info

        # 缓存未命中，调用API
        if is_private_ip(ip_addr):
            ip_addr = ""
        url = f"https://whois.pconline.com.cn/ipJson.jsp?json=true&ip={ip_addr}"
        resp = requests.get(url).json()
        ip_info = {"city": resp.get("city")}

        # 存入缓存
        cache_manager.set(CacheType.IP_INFO, ip_addr, ip_info)
        return ip_info
    except Exception as e:
        logger.bind(tag=TAG).error(f"Error getting client ip info: {e}")
        return {}


def write_json_file(file_path, data):
    """将数据写入 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def remove_punctuation_and_length(text):
    # 全角符号和半角符号的Unicode范围
    full_width_punctuations = (
        "！＂＃＄％＆＇（）＊＋，－。／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
    )
    half_width_punctuations = r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
    space = " "  # 半角空格
    full_width_space = "　"  # 全角空格

    # 去除全角和半角符号以及空格
    result = "".join(
        [
            char
            for char in text
            if char not in full_width_punctuations
            and char not in half_width_punctuations
            and char not in space
            and char not in full_width_space
        ]
    )

    if result == "Yeah":
        return 0, ""
    return len(result), result


def check_model_key(modelType, modelKey):
    if "你" in modelKey:
        return f"配置错误: {modelType} 的 API key 未设置,当前值为: {modelKey}"
    return None


def parse_string_to_list(value, separator=";"):
    """
    将输入值转换为列表
    Args:
        value: 输入值，可以是 None、字符串或列表
        separator: 分隔符，默认为分号
    Returns:
        list: 处理后的列表
    """
    if value is None or value == "":
        return []
    elif isinstance(value, str):
        return [item.strip() for item in value.split(separator) if item.strip()]
    elif isinstance(value, list):
        return value
    return []


def check_ffmpeg_installed() -> bool:
    """
    检查当前环境中是否已正确安装并可执行 ffmpeg。

    Returns:
        bool: 如果 ffmpeg 正常可用，返回 True；否则抛出 ValueError 异常。

    Raises:
        ValueError: 当检测到 ffmpeg 未安装或依赖缺失时，抛出详细的提示信息。
    """
    try:
        # 尝试执行 ffmpeg 命令
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,  # 非零退出码会触发 CalledProcessError
        )

        output = (result.stdout + result.stderr).lower()
        if "ffmpeg version" in output:
            return True

        # 如果未检测到版本信息，也视为异常情况
        raise ValueError("未检测到有效的 ffmpeg 版本输出。")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # 提取错误输出
        stderr_output = ""
        if isinstance(e, subprocess.CalledProcessError):
            stderr_output = (e.stderr or "").strip()
        else:
            stderr_output = str(e).strip()

        # 构建基础错误提示
        error_msg = [
            "❌ 检测到 ffmpeg 无法正常运行。\n",
            "建议您：",
            "1. 确认已正确激活 conda 环境；",
            "2. 查阅项目安装文档，了解如何在 conda 环境中安装 ffmpeg。\n",
        ]

        # 🎯 针对具体错误信息提供额外提示
        if "libiconv.so.2" in stderr_output:
            error_msg.append("⚠️ 发现缺少依赖库：libiconv.so.2")
            error_msg.append("解决方法：在当前 conda 环境中执行：")
            error_msg.append("   conda install -c conda-forge libiconv\n")
        elif "no such file or directory" in stderr_output and "ffmpeg" in stderr_output.lower():
            error_msg.append("⚠️ 系统未找到 ffmpeg 可执行文件。")
            error_msg.append("解决方法：在当前 conda 环境中执行：")
            error_msg.append("   conda install -c conda-forge ffmpeg\n")
        else:
            error_msg.append("错误详情：")
            error_msg.append(stderr_output or "未知错误。")

        # 抛出详细异常信息
        raise ValueError("\n".join(error_msg)) from e


def extract_json_from_string(input_string):
    """提取字符串中的 JSON 部分"""
    pattern = r"(\{.*\})"
    match = re.search(pattern, input_string, re.DOTALL)  # 添加 re.DOTALL
    if match:
        return match.group(1)  # 返回提取的 JSON 字符串
    return None


def audio_to_data_stream(audio_file_path, is_opus=True, callback: Callable[[Any], Any]=None, opus_config: OpusConfig = None) -> None:
    """
    将音频文件转换为opus/pcm数据流
    Args:
        audio_file_path: 音频文件路径
        is_opus: 是否进行Opus编码
        callback: 回调函数
        opus_config: Opus配置对象
    """
    sample_rate = opus_config.sample_rate
    channels = opus_config.channels

    # 获取文件后缀名
    file_type = os.path.splitext(audio_file_path)[1]
    if file_type:
        file_type = file_type.lstrip(".")
    # 读取音频文件，-nostdin 参数：不要从标准输入读取数据，否则FFmpeg会阻塞
    audio = AudioSegment.from_file(
        audio_file_path, format=file_type, parameters=["-nostdin"]
    )

    # 转换为指定采样率和通道数/16位小端编码（确保与编码器匹配）
    audio = audio.set_channels(channels).set_frame_rate(sample_rate).set_sample_width(2)

    # 获取原始PCM数据（16位小端）
    raw_data = audio.raw_data
    pcm_to_data_stream(raw_data, is_opus, callback, opus_config)

def audio_to_data(audio_file_path: str, is_opus: bool = True, opus_config: OpusConfig = None) -> list[bytes]:
    """
    将音频文件转换为Opus/PCM编码的帧列表
    Args:
        audio_file_path: 音频文件路径
        is_opus: 是否进行Opus编码
        opus_config: Opus配置对象
    """
    sample_rate = opus_config.sample_rate
    channels = opus_config.channels
    frame_duration = opus_config.enc_frame_duration_ms

    # 获取文件后缀名
    file_type = os.path.splitext(audio_file_path)[1]
    if file_type:
        file_type = file_type.lstrip(".")
    # 读取音频文件，-nostdin 参数：不要从标准输入读取数据，否则FFmpeg会阻塞
    audio = AudioSegment.from_file(
        audio_file_path, format=file_type, parameters=["-nostdin"]
    )

    # 转换为指定采样率和通道数/16位小端编码（确保与编码器匹配）
    audio = audio.set_channels(channels).set_frame_rate(sample_rate).set_sample_width(2)

    # 获取原始PCM数据（16位小端）
    raw_data = audio.raw_data

    # 编码参数
    frame_size = int(sample_rate * frame_duration / 1000)  # samples/frame
    
    datas = []
    
    if is_opus:
        # Opus编码：需要判断vbr
        vbr = opus_config.vbr
        bitrate = opus_config.bitrate
        # 初始化Opus编码器
        encoder = opuslib_next.Encoder(sample_rate, channels, opuslib_next.APPLICATION_AUDIO)
        # 打印日志确认 vbr 和 frame_duration 的值
        logger.bind(tag=TAG).debug(f"[audio_to_data] vbr={vbr}, frame_duration={frame_duration},frame_size={frame_size},audio_file_path={audio_file_path}")
        
        if not vbr:
            # 固定码率模式：先将PCM数据转换为numpy数组，按样本数处理
            pcm_stream = np.frombuffer(raw_data, dtype=np.int16)
            # 每帧的总样本数（考虑多声道）
            total_frame_size = frame_size * channels
            # 设置VBR
            encoder.vbr = vbr
            encoder.bitrate = bitrate
            
            # 按帧处理所有音频数据（包括最后一帧可能补零）
            for i in range(0, len(pcm_stream), total_frame_size):
                # 提取当前帧
                frame_samples = pcm_stream[i:i + total_frame_size]
                
                # 如果最后一帧不足，用零填充
                if len(frame_samples) < total_frame_size:
                    frame_samples = np.pad(frame_samples, (0, total_frame_size - len(frame_samples)), 'constant')
                    logger.bind(tag=TAG).debug(f"最后一帧用零填充到{total_frame_size}采样点")
                
                # 编码当前帧
                encoded_frame = encoder.encode(frame_samples.tobytes(), frame_size)
                if encoded_frame is not None:
                    # 单帧直接添加
                    datas.append(encoded_frame)
                else:
                    logger.bind(tag=TAG).warning(f"第{len(datas)}帧编码失败")
        else:
            # 动态码率模式：使用原有编码逻辑
            # 按帧处理所有音频数据（包括最后一帧可能补零）
            for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
                # 获取当前帧的二进制数据
                chunk = raw_data[i : i + frame_size * 2]

                # 如果最后一帧不足，补零
                if len(chunk) < frame_size * 2:
                    chunk += b"\x00" * (frame_size * 2 - len(chunk))

                # 转换为numpy数组处理
                np_frame = np.frombuffer(chunk, dtype=np.int16)
                # 编码Opus数据
                frame_data = encoder.encode(np_frame.tobytes(), frame_size)
                datas.append(frame_data)
    else:
        # PCM模式：不需要判断vbr，直接按帧处理
        # 按帧处理所有音频数据（包括最后一帧可能补零）
        for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
            # 获取当前帧的二进制数据
            chunk = raw_data[i : i + frame_size * 2]

            # 如果最后一帧不足，补零
            if len(chunk) < frame_size * 2:
                chunk += b"\x00" * (frame_size * 2 - len(chunk))

            frame_data = chunk if isinstance(chunk, bytes) else bytes(chunk)
            datas.append(frame_data)

    return datas

def audio_bytes_to_data_stream(audio_bytes, file_type, is_opus, callback: Callable[[Any], Any], opus_config: OpusConfig = None) -> None:
    """
    直接用音频二进制数据转为opus/pcm数据，支持wav、mp3、p3
    Args:
        audio_bytes: 音频二进制数据
        file_type: 音频文件类型
        is_opus: 是否进行Opus编码
        callback: 回调函数
        opus_config: Opus配置对象
    """
    if file_type == "p3":
        # 直接用p3解码
        return p3.decode_opus_from_bytes_stream(audio_bytes, callback)
    else:
        sample_rate = opus_config.sample_rate
        channels = opus_config.channels

        # 其他格式用pydub
        audio = AudioSegment.from_file(
            BytesIO(audio_bytes), format=file_type, parameters=["-nostdin"]
        )
        audio = audio.set_channels(channels).set_frame_rate(sample_rate).set_sample_width(2)
        raw_data = audio.raw_data
        pcm_to_data_stream(raw_data, is_opus, callback, opus_config)


def pcm_to_data_stream(raw_data, is_opus=True, callback: Callable[[Any], Any] = None, opus_config: OpusConfig = None):
    """
    将PCM原始数据转换为opus/pcm数据流
    Args:
        raw_data: PCM原始数据
        is_opus: 是否进行Opus编码
        callback: 回调函数
        opus_config: Opus配置对象
    """
    sample_rate = opus_config.sample_rate
    channels = opus_config.channels
    frame_duration = opus_config.enc_frame_duration_ms

    # 编码参数
    frame_size = int(sample_rate * frame_duration / 1000)  # samples/frame

    if is_opus:
        # Opus编码：需要判断vbr
        vbr = opus_config.vbr
        bitrate = opus_config.bitrate
        # 初始化Opus编码器
        encoder = opuslib_next.Encoder(sample_rate, channels, opuslib_next.APPLICATION_AUDIO)
        # 打印日志确认 vbr 和 frame_duration 的值
        logger.bind(tag=TAG).debug(f"[pcm_to_data_stream] vbr={vbr}, frame_duration={frame_duration},frame_size={frame_size}")
        
        if not vbr:
            # 固定码率模式：先将PCM数据转换为numpy数组，按样本数处理
            pcm_stream = np.frombuffer(raw_data, dtype=np.int16)
            # 每帧的总样本数（考虑多声道）
            total_frame_size = frame_size * channels
            # 设置VBR
            encoder.vbr = vbr
            encoder.bitrate = bitrate
            
            # 按帧处理所有音频数据（包括最后一帧可能补零）
            successful_frames = 0
            for i in range(0, len(pcm_stream), total_frame_size):
                # 提取当前帧
                frame_samples = pcm_stream[i:i + total_frame_size]
                
                # 如果最后一帧不足，用零填充
                if len(frame_samples) < total_frame_size:
                    frame_samples = np.pad(frame_samples, (0, total_frame_size - len(frame_samples)), 'constant')
                    logger.bind(tag=TAG).debug(f"最后一帧用零填充到{total_frame_size}采样点")
                
                # 编码当前帧
                encoded_frame = encoder.encode(frame_samples.tobytes(), frame_size)
                if encoded_frame is not None:
                    # 单帧直接回调
                    callback(encoded_frame)
                    successful_frames += 1
                else:
                    logger.bind(tag=TAG).warning(f"第{successful_frames}帧编码失败")
        else:
            # 动态码率模式：使用原有编码逻辑
            # 按帧处理所有音频数据（包括最后一帧可能补零）
            for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
                # 获取当前帧的二进制数据
                chunk = raw_data[i : i + frame_size * 2]

                # 如果最后一帧不足，补零
                if len(chunk) < frame_size * 2:
                    chunk += b"\x00" * (frame_size * 2 - len(chunk))

                # 转换为numpy数组处理
                np_frame = np.frombuffer(chunk, dtype=np.int16)
                # 编码Opus数据
                frame_data = encoder.encode(np_frame.tobytes(), frame_size)
                callback(frame_data)
    else:
        # PCM模式：不需要判断vbr，直接按帧处理
        # 按帧处理所有音频数据（包括最后一帧可能补零）
        for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
            # 获取当前帧的二进制数据
            chunk = raw_data[i : i + frame_size * 2]

            # 如果最后一帧不足，补零
            if len(chunk) < frame_size * 2:
                chunk += b"\x00" * (frame_size * 2 - len(chunk))

            frame_data = chunk if isinstance(chunk, bytes) else bytes(chunk)
            callback(frame_data)

def decode_opus_to_pcm(opus_data: list, config: OpusConfig = None, target_sample_rate: int = 16000, target_channels: int = 1) -> list[bytes]:
    """将Opus音频数据解码为PCM数据，并可选地进行重采样和通道转换
    
    Args:
        opus_data: Opus音频数据列表
        config: Opus配置对象，如果为None则使用默认配置 (16000Hz, 1通道, 20ms帧)
        target_sample_rate: 目标采样率，默认16000Hz（ASR模型标准输入）
        target_channels: 目标通道数，默认1（单声道，ASR模型标准输入）
    
    Returns:
        PCM数据列表（已转换为目标采样率和通道数）
    """
    try:
        # 如果没有提供config，使用默认配置
        if config is None:
            config = OpusConfig()
        
        # 使用config中的参数动态构建解码器
        decoder = opuslib_next.Decoder(config.sample_rate, config.channels)
        pcm_data = []
        # buffer_size应该是PCM样本数，不是字节数
        buffer_size = config.sample_points  # 使用config中的sample_points（样本数）
        
        # 根据vbr配置选择解码方式
        if config.vbr:
            # VBR模式：逐个数据包解码
            for i, opus_packet in enumerate(opus_data):
                try:
                    if not opus_packet or len(opus_packet) == 0:
                        continue
                    
                    pcm_frame = decoder.decode(opus_packet, buffer_size)
                    if pcm_frame and len(pcm_frame) > 0:
                        pcm_data.append(pcm_frame)
                        
                except opuslib_next.OpusError as e:
                    logger.bind(tag=TAG).warning(f"Opus解码错误，跳过数据包 {i}: {e}")
                except Exception as e:
                    logger.bind(tag=TAG).error(f"音频处理错误，数据包 {i}: {e}")
        else:
            # CBR模式：固定字节数解析
            # 合并所有opus数据包
            opus_stream = b"".join(opus_data)
            
            if not opus_stream:
                logger.bind(tag=TAG).warning("输入数据流为空")
                return []
            
            # 计算每帧字节数
            frame_size_bytes = config.frame_size
            num_frames = len(opus_stream) // frame_size_bytes
            
            if len(opus_stream) % frame_size_bytes != 0:
                logger.bind(tag=TAG).warning(f"数据流大小不是{frame_size_bytes}字节的整数倍，最后一帧可能不完整")
            
            logger.bind(tag=TAG).debug(f"总帧数: {num_frames}")
            
            # 解码所有帧
            successful_frames = 0
            
            for frame_idx in range(num_frames):
                start_byte = frame_idx * frame_size_bytes
                end_byte = start_byte + frame_size_bytes
                
                # 提取当前帧的数据
                frame_data = opus_stream[start_byte:end_byte]
                
                # 解码当前帧
                try:
                    pcm_frame = decoder.decode(frame_data, buffer_size)
                    if pcm_frame and len(pcm_frame) > 0:
                        pcm_data.append(pcm_frame)
                        successful_frames += 1
                    else:
                        logger.bind(tag=TAG).warning(f"第{frame_idx}帧解码失败")
                except opuslib_next.OpusError as e:
                    logger.bind(tag=TAG).warning(f"第{frame_idx}帧Opus解码错误: {e}")
                except Exception as e:
                    logger.bind(tag=TAG).error(f"第{frame_idx}帧音频处理错误: {e}")
            
            if not pcm_data:
                logger.bind(tag=TAG).error("没有成功解码任何帧")
                return []
            
            logger.bind(tag=TAG).debug(f"成功解码帧数: {successful_frames}/{num_frames}")
        
        # 检查是否需要进行重采样或通道转换
        need_resample = config.sample_rate != target_sample_rate
        need_channel_convert = config.channels != target_channels
        
        if need_resample or need_channel_convert:
            pcm_data = _convert_pcm_format(
                pcm_data, 
                src_sample_rate=config.sample_rate, 
                src_channels=config.channels,
                target_sample_rate=target_sample_rate,
                target_channels=target_channels
            )
        
        return pcm_data
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"音频解码过程发生错误: {e}")
        return []


def _convert_pcm_format(pcm_data: list[bytes], src_sample_rate: int, src_channels: int, 
                        target_sample_rate: int, target_channels: int) -> list[bytes]:
    """将PCM数据从源格式转换为目标格式（重采样和通道转换）
    
    Args:
        pcm_data: PCM数据列表
        src_sample_rate: 源采样率
        src_channels: 源通道数
        target_sample_rate: 目标采样率
        target_channels: 目标通道数
    
    Returns:
        转换后的PCM数据列表
    """
    try:
        # 合并所有PCM数据
        combined_pcm = b"".join(pcm_data)
        if not combined_pcm:
            return []
        
        # 转换为numpy数组（16位有符号整数）
        audio_array = np.frombuffer(combined_pcm, dtype=np.int16)
        
        # 通道转换：如果源是多通道，目标是单通道
        if src_channels > 1 and target_channels == 1:
            # 将交错的多通道数据reshape为(samples, channels)
            audio_array = audio_array.reshape(-1, src_channels)
            # 取所有通道的平均值转为单声道
            audio_array = audio_array.mean(axis=1).astype(np.int16)
        elif src_channels == 1 and target_channels > 1:
            # 单声道转多声道：复制到每个通道
            audio_array = np.tile(audio_array.reshape(-1, 1), (1, target_channels)).flatten()
        
        # 重采样
        if src_sample_rate != target_sample_rate:
            # 计算重采样后的样本数
            num_samples = len(audio_array)
            new_num_samples = int(num_samples * target_sample_rate / src_sample_rate)
            
            # 使用numpy的线性插值进行重采样
            x_old = np.linspace(0, 1, num_samples)
            x_new = np.linspace(0, 1, new_num_samples)
            audio_array = np.interp(x_new, x_old, audio_array.astype(np.float32)).astype(np.int16)
        
        # 转换回bytes
        converted_pcm = audio_array.tobytes()
        
        logger.bind(tag=TAG).debug(
            f"PCM格式转换完成: {src_sample_rate}Hz/{src_channels}ch -> {target_sample_rate}Hz/{target_channels}ch"
        )
        
        return [converted_pcm]
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"PCM格式转换失败: {e}")
        return pcm_data  # 转换失败时返回原始数据


def opus_datas_to_wav_bytes(opus_datas, sample_rate=16000, channels=1, opus_config: OpusConfig = None):
    """
    将opus帧列表解码为wav字节流
    
    Args:
        opus_datas: Opus音频数据列表
        sample_rate: 采样率（仅在opus_config为None时使用）
        channels: 通道数（仅在opus_config为None时使用）
        opus_config: Opus配置对象，如果提供则优先使用
    
    Returns:
        WAV格式的音频字节流
    """
    # 如果提供了opus_config，使用新的解码方式
    if opus_config is not None:
        pcm_datas = decode_opus_to_pcm(opus_datas, opus_config)
        if not pcm_datas:
            raise ValueError("没有有效的PCM数据")
        
        pcm_bytes = b"".join(pcm_datas)
        sample_rate = opus_config.sample_rate
        channels = opus_config.channels
    else:
        # 兼容旧的解码方式（不使用OpusConfig）
        decoder = opuslib_next.Decoder(sample_rate, channels)
        pcm_datas = []

        frame_duration = 60  # ms
        frame_size = int(sample_rate * frame_duration / 1000)  # 960

        for opus_frame in opus_datas:
            # 解码为PCM（返回bytes，2字节/采样点）
            pcm = decoder.decode(opus_frame, frame_size)
            pcm_datas.append(pcm)

        pcm_bytes = b"".join(pcm_datas)

    # 写入wav字节流
    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return wav_buffer.getvalue()

def check_vad_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("VAD") is None
    ):
        return False
    update_vad = False
    current_vad_module = before_config["selected_module"]["VAD"]
    new_vad_module = new_config["selected_module"]["VAD"]
    current_vad_type = (
        current_vad_module
        if "type" not in before_config["VAD"][current_vad_module]
        else before_config["VAD"][current_vad_module]["type"]
    )
    new_vad_type = (
        new_vad_module
        if "type" not in new_config["VAD"][new_vad_module]
        else new_config["VAD"][new_vad_module]["type"]
    )
    update_vad = current_vad_type != new_vad_type
    return update_vad


def check_asr_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("ASR") is None
    ):
        return False
    update_asr = False
    current_asr_module = before_config["selected_module"]["ASR"]
    new_asr_module = new_config["selected_module"]["ASR"]
    current_asr_type = (
        current_asr_module
        if "type" not in before_config["ASR"][current_asr_module]
        else before_config["ASR"][current_asr_module]["type"]
    )
    new_asr_type = (
        new_asr_module
        if "type" not in new_config["ASR"][new_asr_module]
        else new_config["ASR"][new_asr_module]["type"]
    )
    update_asr = current_asr_type != new_asr_type
    return update_asr


def filter_sensitive_info(config: dict) -> dict:
    """
    过滤配置中的敏感信息
    Args:
        config: 原始配置字典
    Returns:
        过滤后的配置字典
    """
    sensitive_keys = [
        "api_key",
        "personal_access_token",
        "access_token",
        "token",
        "secret",
        "access_key_secret",
        "secret_key",
    ]

    def _filter_dict(d: dict) -> dict:
        filtered = {}
        for k, v in d.items():
            if any(sensitive in k.lower() for sensitive in sensitive_keys):
                filtered[k] = "***"
            elif isinstance(v, dict):
                filtered[k] = _filter_dict(v)
            elif isinstance(v, list):
                filtered[k] = [_filter_dict(i) if isinstance(i, dict) else i for i in v]
            else:
                filtered[k] = v
        return filtered

    return _filter_dict(copy.deepcopy(config))


def get_vision_url(config: dict) -> str:
    """获取 vision URL

    Args:
        config: 配置字典

    Returns:
        str: vision URL
    """
    server_config = config["server"]
    vision_explain = server_config.get("vision_explain", "")
    if "你的" in vision_explain:
        local_ip = get_local_ip()
        port = int(server_config.get("http_port", 8003))
        vision_explain = f"http://{local_ip}:{port}/mcp/vision/explain"
    return vision_explain


def is_valid_image_file(file_data: bytes) -> bool:
    """
    检查文件数据是否为有效的图片格式

    Args:
        file_data: 文件的二进制数据

    Returns:
        bool: 如果是有效的图片格式返回True，否则返回False
    """
    # 常见图片格式的魔数（文件头）
    image_signatures = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"BM": "BMP",
        b"II*\x00": "TIFF",
        b"MM\x00*": "TIFF",
        b"RIFF": "WEBP",
    }

    # 检查文件头是否匹配任何已知的图片格式
    for signature in image_signatures:
        if file_data.startswith(signature):
            return True

    return False


def sanitize_tool_name(name: str) -> str:
    """Sanitize tool names for OpenAI compatibility."""
    # 支持中文、英文字母、数字、下划线和连字符
    return re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", name)


def validate_mcp_endpoint(mcp_endpoint: str) -> bool:
    """
    校验MCP接入点格式

    Args:
        mcp_endpoint: MCP接入点字符串

    Returns:
        bool: 是否有效
    """
    # 1. 检查是否以ws开头
    if not mcp_endpoint.startswith("ws"):
        return False

    # 2. 检查是否包含key、call字样
    if "key" in mcp_endpoint.lower() or "call" in mcp_endpoint.lower():
        return False

    # 3. 检查是否包含/mcp/字样
    if "/mcp/" not in mcp_endpoint:
        return False

    return True


def transform_device_id(device_id: str, device_type: str = "0") -> str:
    """
    转换 device-id
    根据 device-type 对 device-id 进行转换
    
    Args:
        device_id: 原始设备ID
        device_type: 设备类型，默认为 "0"
        
    Returns:
        str: 转换后的设备ID
    """
    if not device_id:
        return device_id
    
    # 如果 device-type 为 1，则将 device-id 暂时改成 1234567
    if device_type == "1":
        return "1234567"
    
    # 默认情况下返回原始值
    return device_id