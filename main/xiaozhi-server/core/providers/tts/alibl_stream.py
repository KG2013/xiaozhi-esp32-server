import os
import uuid
import json
import time
import queue
import asyncio
import traceback
import struct
import websockets
from asyncio import Task
from config.logger import setup_logging
from core.utils.util import pcm_to_data_stream
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType
from core.utils.opus_encoder_utils import OpusEncoderUtils

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

        self.interface_type = InterfaceType.DUAL_STREAM
        # 基础配置
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("api_key is required for CosyVoice TTS")

        # WebSocket配置
        self.ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
        self.ws = None
        self._monitor_task = None
        self.last_active_time = None

        # 模型和音色配置
        self.model = config.get("model", "cosyvoice-v2")
        self.voice = config.get("voice", "longxiaochun_v2")  # 默认音色
        if config.get("private_voice"):
            self.voice = config.get("private_voice")

        # 音频参数配置
        self.format = config.get("format", "pcm")
        sample_rate = config.get("sample_rate", "24000")
        self.sample_rate = int(sample_rate) if sample_rate else 24000

        volume = config.get("volume", "50")
        self.volume = int(volume) if volume else 50

        rate = config.get("rate", "1.0")
        self.rate = float(rate) if rate else 1.0

        pitch = config.get("pitch", "1.0")
        self.pitch = float(pitch) if pitch else 1.0

        
        self.bit_rate = 16

        self.header = {
            "Authorization": f"Bearer {self.api_key}",
            # "user-agent": "your_platform_info", // 可选
            # "X-DashScope-WorkSpace": workspace, // 可选，阿里云百炼业务空间ID
            "X-DashScope-DataInspection": "enable",
        }
        
        # Opus编码器实例（用于流式处理，避免帧边界错位）
        self.opus_encoder = None


    async def _ensure_connection(self):
        """确保WebSocket连接可用，支持60秒内连接复用"""
        try:
            current_time = time.time()
            if self.ws and current_time - self.last_active_time < 60:
                # 一分钟内才可以复用链接进行连续对话
                logger.bind(tag=TAG).info(f"使用已有链接...")
                return self.ws
            logger.bind(tag=TAG).info("开始建立新连接...")

            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=self.header,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )

            logger.bind(tag=TAG).info("WebSocket连接建立成功")
            self.last_active_time = current_time
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"建立连接失败: {str(e)}")
            self.ws = None
            self.last_active_time = None
            raise

    def tts_text_priority_thread(self):
        """流式TTS文本处理线程"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"收到TTS任务｜{message.sentence_type.name} ｜ {message.content_type.name} | 会话ID: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False

                if self.conn.client_abort:
                    try:
                        logger.bind(tag=TAG).info("收到打断信息，终止TTS文本处理线程")
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"取消TTS会话失败: {str(e)}")
                        continue

                if message.sentence_type == SentenceType.FIRST:
                    # 初始化会话
                    try:
                        # 设置标志，确保发送 tts start 消息
                        self.tts_audio_first_sentence = True
                        if not getattr(self.conn, "sentence_id", None): 
                            self.conn.sentence_id = uuid.uuid4().hex
                            logger.bind(tag=TAG).info(f"自动生成新的 会话ID: {self.conn.sentence_id}")

                        logger.bind(tag=TAG).info("开始启动TTS会话...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.start_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                        self.before_stop_play_files.clear()
                        logger.bind(tag=TAG).info("TTS会话启动成功")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"启动TTS会话失败: {str(e)}")
                        continue

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        try:
                            logger.bind(tag=TAG).debug(
                                f"开始发送TTS文本: {message.content_detail}"
                            )
                            future = asyncio.run_coroutine_threadsafe(
                                self.text_to_speak(message.content_detail, None),
                                loop=self.conn.loop,
                            )
                            future.result()
                            logger.bind(tag=TAG).debug("TTS文本发送成功")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"发送TTS文本失败: {str(e)}")
                            continue

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"添加音频文件到待播放列表: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # 先处理文件音频数据
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))

                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).info("开始结束TTS会话...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"结束TTS会话失败: {str(e)}")
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理TTS文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )
                continue

    async def text_to_speak(self, text, _):
        """发送文本到TTS服务进行合成"""
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning("WebSocket连接不存在，终止发送文本")
                return

            # 过滤Markdown
            filtered_text = MarkdownCleaner.clean_markdown(text)

            # 发送continue-task消息
            continue_task_message = {
                "header": {
                    "action": "continue-task",
                    "task_id": self.conn.sentence_id,
                    "streaming": "duplex",
                },
                "payload": {"input": {"text": filtered_text}},
            }

            await self.ws.send(json.dumps(continue_task_message))
            self.last_active_time = time.time()
            logger.bind(tag=TAG).debug(f"已发送文本: {filtered_text}")

        except Exception as e:
            logger.bind(tag=TAG).error(f"发送TTS文本失败: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
            raise

    async def start_session(self, session_id):
        """启动TTS会话"""
        logger.bind(tag=TAG).info(f"开始会话～～{session_id}")
        try:
            # 检查并清理上一个会话的监听任务
            if (
                self._monitor_task is not None
                and isinstance(self._monitor_task, Task)
                and not self._monitor_task.done()
            ):
                logger.bind(tag=TAG).info("检测到未完成的上个会话，关闭监听任务...")
                await self.close()

            # 确保连接可用
            await self._ensure_connection()
            
            # 初始化Opus编码器（用于流式处理，避免帧边界错位）
            opus_config = self.get_opus_config()
            if opus_config and self.format == "pcm":
                # 使用配置的帧大小进行编码，确保帧对齐
                frame_duration_ms = opus_config.enc_frame_duration_ms
                self.opus_encoder = OpusEncoderUtils(
                    sample_rate=opus_config.sample_rate,
                    channels=opus_config.channels,
                    frame_size_ms=frame_duration_ms,
                    vbr=opus_config.vbr,  # 使用配置的VBR模式
                    bitrate=opus_config.bitrate  # 使用配置的码率
                )
                logger.bind(tag=TAG).debug(
                    f"初始化Opus编码器: sample_rate={opus_config.sample_rate}, "
                    f"channels={opus_config.channels}, frame_size_ms={frame_duration_ms}, "
                    f"vbr={opus_config.vbr}, bitrate={opus_config.bitrate}"
                )

            # 启动监听任务
            self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

            # 发送run-task消息启动会话
            run_task_message = {
                "header": {
                    "action": "run-task",
                    "task_id": session_id,
                    "streaming": "duplex",
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": self.model,
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": self.voice,
                        "format": self.format,
                        "sample_rate": self.sample_rate,
                        "volume": self.volume,
                        "rate": self.rate,
                        "pitch": self.pitch,
                        "bit_rate": self.bit_rate,
                    },
                    "input": {}
                },
            }

            await self.ws.send(json.dumps(run_task_message))
            self.last_active_time = time.time()
            logger.bind(tag=TAG).info("会话启动请求已发送")
        except Exception as e:
            logger.bind(tag=TAG).error(f"启动会话失败: {str(e)}")
            await self.close()
            raise

    async def finish_session(self, session_id):
        """结束TTS会话"""
        logger.bind(tag=TAG).info(f"关闭会话～～{session_id}")
        try:
            if self.ws and session_id:
                # 发送finish-task消息
                finish_task_message = {
                    "header": {
                        "action": "finish-task",
                        "task_id": session_id,
                        "streaming": "duplex",
                    },
                    "payload": {
                        "input": {}
                    }
                }

                await self.ws.send(json.dumps(finish_task_message))
                self.last_active_time = time.time()
                logger.bind(tag=TAG).info("会话结束请求已发送")
                # 等待监听任务完成
                if self._monitor_task:
                    try:
                        await self._monitor_task
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"等待监听任务完成时发生错误: {str(e)}"
                        )
                    finally:
                        self._monitor_task = None

        except Exception as e:
            logger.bind(tag=TAG).error(f"关闭会话失败: {str(e)}")
            await self.close()
            raise

    async def close(self):
        """清理资源"""
        # 取消监听任务
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"关闭时取消监听任务错误: {e}")
            self._monitor_task = None

        # 重置Opus编码器状态
        if self.opus_encoder:
            try:
                self.opus_encoder.reset_state()
            except Exception as e:
                logger.bind(tag=TAG).warning(f"重置Opus编码器状态时出错: {e}")
            self.opus_encoder = None

        # 关闭WebSocket连接
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            self.last_active_time = None

    async def _start_monitor_tts_response(self):
        """监听TTS响应"""
        try:
            session_finished = False
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()
                    self.last_active_time = time.time()

                    # 检查客户端是否中止
                    if self.conn.client_abort:
                        logger.bind(tag=TAG).info("收到打断信息，终止监听TTS响应")
                        break

                    if isinstance(msg, str):  # JSON控制消息
                        try:
                            data = json.loads(msg)
                            event = data["header"].get("event")

                            if event == "task-started":
                                logger.bind(tag=TAG).debug("TTS任务启动成功~")
                                self.tts_audio_queue.put((SentenceType.FIRST, [], None))
                            elif event == "result-generated":
                                # 发送缓存的数据
                                if self.conn.tts_MessageText:
                                    logger.bind(tag=TAG).info(
                                        f"句子语音生成成功： {self.conn.tts_MessageText}"
                                    )
                                    self.tts_audio_queue.put(
                                        (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                    )
                                    self.conn.tts_MessageText = None
                            elif event == "task-finished":
                                logger.bind(tag=TAG).debug("TTS任务完成~")
                                # 处理Opus编码器缓冲区中的剩余数据
                                if self.opus_encoder:
                                    try:
                                        self.opus_encoder.encode_pcm_to_opus_stream(
                                            pcm_data=b"",
                                            end_of_stream=True,  # 标记流结束，处理剩余数据
                                            callback=self.handle_opus
                                        )
                                    except Exception as e:
                                        logger.bind(tag=TAG).warning(f"处理剩余Opus数据时出错: {e}")
                                self._process_before_stop_play_files()
                                session_finished = True
                                break
                            elif event == "task-failed":
                                error_code = data["header"].get("error_code", "unknown")
                                error_message = data["header"].get("error_message", "未知错误")
                                logger.bind(tag=TAG).error(
                                    f"TTS任务失败: {error_code} - {error_message}"
                                )
                                break
                        except json.JSONDecodeError:
                            logger.bind(tag=TAG).warning("收到无效的JSON消息")
                    elif isinstance(msg, (bytes, bytearray)):
                        if self.format == "pcm":
                            # 使用带缓冲的Opus编码器处理流式数据，避免帧边界错位导致的杂音
                            if self.opus_encoder:
                                # 使用OpusEncoderUtils的流式编码，自动处理不完整的帧
                                self.opus_encoder.encode_pcm_to_opus_stream(
                                    pcm_data=msg,
                                    end_of_stream=False,  # 流式数据，不是结束
                                    callback=self.handle_opus
                                )
                            else:
                                # 回退到原有方法（如果编码器未初始化）
                                logger.bind(tag=TAG).warning("Opus编码器未初始化，使用回退方法")
                                pcm_to_data_stream(
                                    msg,
                                    is_opus=True,
                                    callback=self.handle_opus,
                                    opus_config=self.get_opus_config()
                                )
                        else:
                            self.handle_opus(extract_opus_packets(msg))
                        
                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("WebSocket连接已关闭")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"处理TTS响应时出错: {e}\n{traceback.format_exc()}"
                    )
                    break

            # 仅在连接异常且非正常结束时才关闭连接
            if not session_finished and self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        # 监听任务退出时清理引用和处理剩余数据
        finally:
            # 处理Opus编码器缓冲区中的剩余数据（防止数据丢失）
            if self.opus_encoder:
                try:
                    self.opus_encoder.encode_pcm_to_opus_stream(
                        pcm_data=b"",
                        end_of_stream=True,  # 标记流结束，处理剩余数据
                        callback=self.handle_opus
                    )
                except Exception as e:
                    logger.bind(tag=TAG).warning(f"清理Opus编码器剩余数据时出错: {e}")
            self._monitor_task = None

    def to_tts(self, text: str) -> list:
        """非流式生成音频数据，用于生成音频及测试场景"""
        try:
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 生成会话ID
            session_id = uuid.uuid4().hex
            # 存储音频数据
            audio_data = []

            async def _generate_audio():
                ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=self.header,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                )

                try:
                    # 发送run-task消息启动会话
                    run_task_message = {
                        "header": {
                            "action": "run-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "task_group": "audio",
                            "task": "tts",
                            "function": "SpeechSynthesizer",
                            "model": self.model,
                            "parameters": {
                                "text_type": "PlainText",
                                "voice": self.voice,
                                "format": self.format,
                                "sample_rate": self.sample_rate,
                                "volume": self.volume,
                                "rate": self.rate,
                                "pitch": self.pitch,
                                "bit_rate": self.bit_rate,
                            },
                            "input": {}
                        },
                    }
                    await ws.send(json.dumps(run_task_message))

                    # 等待任务启动
                    task_started = False
                    while not task_started:
                        msg = await ws.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-started":
                                task_started = True
                                logger.bind(tag=TAG).debug("TTS任务已启动")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "未知错误")
                                raise Exception(
                                    f"启动任务失败: {error_code} - {error_message}"
                                )

                    # 发送文本
                    filtered_text = MarkdownCleaner.clean_markdown(text)
                    # 发送continue-task消息
                    continue_task_message = {
                        "header": {
                            "action": "continue-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {"input": {"text": filtered_text}},
                    }
                    await ws.send(json.dumps(continue_task_message))

                    # 发送finish-task消息
                    finish_task_message = {
                        "header": {
                            "action": "finish-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "input": {}
                        }
                    }
                    await ws.send(json.dumps(finish_task_message))

                    # 接收音频数据
                    task_finished = False
                    while not task_finished:
                        msg = await ws.recv()
                        if isinstance(msg, (bytes, bytearray)):
                            pcm_to_data_stream(
                                msg,
                                is_opus=True,
                                callback=lambda opus: audio_data.append(opus),
                                opus_config=self.get_opus_config()
                            )
                        elif isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            if header.get("event") == "task-finished":
                                task_finished = True
                                logger.bind(tag=TAG).debug("TTS任务完成")
                            elif header.get("event") == "task-failed":
                                error_code = header.get("error_code", "unknown")
                                error_message = header.get("error_message", "未知错误")
                                raise Exception(
                                    f"合成失败: {error_code} - {error_message}"
                                )

                finally:
                    # 清理资源
                    try:
                        await ws.close()
                    except:
                        pass

            # 运行异步任务
            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data

        except Exception as e:
            logger.bind(tag=TAG).error(f"生成音频数据失败: {str(e)}")
            return []


def parse_ogg_page(data):
    """
    解析 OGG 页面结构
    """
    if len(data) < 27:
        logger.bind(tag=TAG).warning(f"OGG数据长度不足: {len(data)} 字节, 前27字节: {data[:27].hex() if len(data) >= 27 else data.hex()}")
        raise ValueError("Not a valid OGG page: data too short")
    
    if data[0:4] != b'OggS':
        logger.bind(tag=TAG).warning(f"OGG页面标识无效: 期望'OggS', 实际: {data[0:4]}, 前32字节: {data[:32].hex()}")
        raise ValueError("Not a valid OGG page")
    
    version = data[4]
    header_type = data[5]
    granule_position = struct.unpack('<Q', data[6:14])[0]
    bitstream_serial = struct.unpack('<I', data[14:18])[0]
    page_sequence = struct.unpack('<I', data[18:22])[0]
    checksum = struct.unpack('<I', data[22:26])[0]
    page_segments = data[26]
    
    if len(data) < 27 + page_segments:
        logger.bind(tag=TAG).warning(
            f"OGG页面数据不完整: 总长度={len(data)}, 需要至少{27 + page_segments}字节, "
            f"version={version}, header_type={header_type}, page_segments={page_segments}, "
            f"前64字节: {data[:64].hex()}"
        )
        raise ValueError("Not a valid OGG page: incomplete segment table")
    
    segment_table = data[27:27+page_segments]
    
    # 计算数据偏移
    header_size = 27 + page_segments
    data_start = header_size
    
    logger.bind(tag=TAG).debug(
        f"OGG页面解析成功: version={version}, header_type={header_type}, "
        f"granule_position={granule_position}, bitstream_serial={bitstream_serial}, "
        f"page_sequence={page_sequence}, page_segments={page_segments}, "
        f"header_size={header_size}, segment_table_len={len(segment_table)}, "
        f"data_len={len(data[data_start:])}"
    )
    
    return {
        'header_size': header_size,
        'segment_table': segment_table,
        'data': data[data_start:]
    }

def extract_opus_packets(ogg_data):
    """
    从 OGG 数据中提取 Opus 包
    """
    offset = 0
    opus_packets = []
    page_count = 0
    
    logger.bind(tag=TAG).debug(f"开始提取Opus包, 输入数据长度: {len(ogg_data)} 字节, 前32字节: {ogg_data[:32].hex() if len(ogg_data) >= 32 else ogg_data.hex()}")
    
    while offset < len(ogg_data):
        try:
            page = parse_ogg_page(ogg_data[offset:])
            page_count += 1
            offset += page['header_size']
            
            # 处理段数据
            segment_data = page['data']
            opus_packets.append(segment_data)
            
            logger.bind(tag=TAG).debug(
                f"OGG页面 {page_count}: 提取了 {len(segment_data)} 字节的Opus数据, "
                f"当前offset={offset}, 剩余数据={len(ogg_data) - offset} 字节"
            )
            
            offset += len(segment_data)
            
        except (ValueError, struct.error) as e:
            # 不是有效的 OGG 页面，可能已经是 Opus 数据
            logger.bind(tag=TAG).warning(
                f"OGG页面解析失败 (页面 {page_count + 1}): {type(e).__name__}: {e}, "
                f"当前offset={offset}, 剩余数据长度={len(ogg_data) - offset}, "
                f"剩余数据前64字节: {ogg_data[offset:offset+64].hex() if len(ogg_data) - offset >= 64 else ogg_data[offset:].hex()}"
            )
            opus_packets.append(ogg_data[offset:])
            break
    
    result = b''.join(opus_packets)
    logger.bind(tag=TAG).debug(
        f"Opus包提取完成: 共解析 {page_count} 个OGG页面, "
        f"提取了 {len(opus_packets)} 个数据包, 总输出长度: {len(result)} 字节"
    )
    
    return result