"""
性能追踪工具类
用于统计对话流程中各个节点的耗时
"""
import time
from typing import Dict, Optional
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class PerformanceTracker:
    """性能追踪器，用于记录和统计各节点耗时"""
    
    def __init__(self):
        self.timestamps: Dict[str, float] = {}
        self.durations: Dict[str, float] = {}
        self.first_audio_sent = False
        
    def reset(self):
        """重置所有时间戳和耗时记录"""
        self.timestamps.clear()
        self.durations.clear()
        self.first_audio_sent = False
    
    def record(self, event_name: str, timestamp: Optional[float] = None):
        """记录事件时间戳"""
        if timestamp is None:
            timestamp = time.monotonic()
        self.timestamps[event_name] = timestamp
    
    def calculate_duration(self, start_event: str, end_event: str) -> Optional[float]:
        """计算两个事件之间的耗时"""
        start_time = self.timestamps.get(start_event)
        end_time = self.timestamps.get(end_event)
        
        if start_time is None or end_time is None:
            return None
        
        duration = end_time - start_time
        self.durations[f"{start_event}_to_{end_event}"] = duration
        return duration
    
    def get_duration(self, event_name: str) -> Optional[float]:
        """获取已计算的耗时"""
        return self.durations.get(event_name)
    
    def log_statistics(self, conn, session_id: str = None):
        """输出性能统计信息，统计从设备发完语音到返回第一个语音的完整流程"""
        if not self.timestamps:
            return
        
        # 计算各个节点的耗时
        stats = {}
        
        # 获取关键时间点
        voice_stop_detected = self.timestamps.get("voice_stop_detected")
        asr_start = self.timestamps.get("asr_start")
        asr_end = self.timestamps.get("asr_end")
        intent_start = self.timestamps.get("intent_start")
        intent_end = self.timestamps.get("intent_end")
        memory_start = self.timestamps.get("memory_query_start")
        memory_end = self.timestamps.get("memory_query_end")
        llm_start = self.timestamps.get("llm_start")
        llm_first_token = self.timestamps.get("llm_first_token")
        llm_end = self.timestamps.get("llm_end")
        tts_start = self.timestamps.get("tts_start")
        tts_first_audio = self.timestamps.get("tts_first_audio")
        first_audio_sent = self.timestamps.get("first_audio_sent")
        
        # 1. ASR识别耗时（从开始识别到识别完成）
        if asr_start and asr_end:
            stats["ASR识别耗时"] = (asr_end - asr_start) * 1000
        
        # 2. 意图识别耗时
        if intent_start and intent_end:
            stats["意图识别耗时"] = (intent_end - intent_start) * 1000
        
        # 3. 记忆获取耗时
        if memory_start and memory_end:
            stats["记忆获取耗时"] = (memory_end - memory_start) * 1000
        
        # 4. LLM耗时（从调用到首次返回文本）
        if llm_start:
            if llm_first_token:
                stats["LLM首字耗时"] = (llm_first_token - llm_start) * 1000
            if llm_end:
                stats["LLM总耗时"] = (llm_end - llm_start) * 1000
        
        # 5. TTS耗时（从文本到第一段音频）
        if tts_start and tts_first_audio:
            stats["TTS首段音频耗时"] = (tts_first_audio - tts_start) * 1000
        
        # 6. 各个环节之间的间隔时间
        if voice_stop_detected and asr_start:
            stats["语音停止→ASR开始"] = (asr_start - voice_stop_detected) * 1000
        
        if asr_end and intent_start:
            stats["ASR结束→意图识别开始"] = (intent_start - asr_end) * 1000
        
        if intent_end and llm_start:
            stats["意图识别结束→LLM开始"] = (llm_start - intent_end) * 1000
        elif asr_end and llm_start and not intent_start:
            # 如果没有意图识别，则从ASR结束到LLM开始
            stats["ASR结束→LLM开始"] = (llm_start - asr_end) * 1000
        
        if memory_end and llm_start:
            stats["记忆获取结束→LLM开始"] = (llm_start - memory_end) * 1000
        
        if llm_end and tts_start:
            stats["LLM结束→TTS开始"] = (tts_start - llm_end) * 1000
        
        if tts_first_audio and first_audio_sent:
            stats["TTS首段音频→发送完成"] = (first_audio_sent - tts_first_audio) * 1000
        
        # 7. 总耗时（从设备发完语音到返回第一个语音）
        if voice_stop_detected and first_audio_sent:
            stats["总响应时间"] = (first_audio_sent - voice_stop_detected) * 1000
        
        # 输出统计信息
        if stats:
            log_msg = "=" * 70 + "\n"
            log_msg += "性能统计报告 - 从设备发完语音到返回第一个语音\n"
            if session_id:
                log_msg += f"会话ID: {session_id}\n"
            log_msg += "-" * 70 + "\n"
            
            # 按流程顺序输出
            ordered_keys = [
                "总响应时间",
                "ASR识别耗时",
                "语音停止→ASR开始",
                "ASR结束→意图识别开始",
                "意图识别耗时",
                "意图识别结束→LLM开始",
                "ASR结束→LLM开始",
                "记忆获取耗时",
                "记忆获取结束→LLM开始",
                "LLM首字耗时",
                "LLM总耗时",
                "LLM结束→TTS开始",
                "TTS首段音频耗时",
                "TTS首段音频→发送完成",
            ]
            
            # 先输出有序的统计项
            for key in ordered_keys:
                if key in stats:
                    log_msg += f"{key:30s}: {stats[key]:8.2f} ms\n"
            
            # 输出其他未列出的统计项
            for key, value in stats.items():
                if key not in ordered_keys:
                    log_msg += f"{key:30s}: {value:8.2f} ms\n"
            
            log_msg += "=" * 70
            
            logger.bind(tag=TAG).info(log_msg)
            
            # 同时输出到连接日志
            if hasattr(conn, 'logger'):
                conn.logger.bind(tag=TAG).info(log_msg)

