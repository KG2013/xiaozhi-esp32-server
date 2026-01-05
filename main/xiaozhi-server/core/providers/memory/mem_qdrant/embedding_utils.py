"""
Embedding工具类 - 用于文本向量化
支持 OpenAI 和豆包(火山引擎)两种API
"""

import os
from typing import List, Optional
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class EmbeddingProvider:
    """统一的Embedding提供者，支持OpenAI和豆包两种API"""
    MODELS = {
        "openai": {
            "name": "text-embedding-3-small",
            "dim": 1536,
            "type": "api",
            "description": "OpenAI官方，1536维，高质量",
            # API配置
            "api_key": "你的openai api key",  # 或使用环境变量 OPENAI_API_KEY
            "base_url": None  # 可选，用于自定义代理
        },
        "openai-large": {
            "name": "text-embedding-3-large",
            "dim": 3072,
            "type": "api",
            "description": "OpenAI大模型，3072维，最高精度",
            # API配置
            "api_key": "你的openai api key",  # 或使用环境变量 OPENAI_API_KEY
            "base_url": None
        },
        # 豆包(火山引擎) API
        "doubao": {
            "name": "doubao-embedding-large-text-240915",
            "dim": 4096,  # 注意：豆包模型已升级，实际维度为4096
            "type": "api",
            "description": "豆包大规模文本向量模型，4096维（已升级），国内优化",
            # API配置
            "api_key": "a7568900-d463-437a-bf3c-69bf53221d78",  # 或使用环境变量 DOUBAO_API_KEY
            "base_url": "https://ark.cn-beijing.volces.com/api/v3"
        }
    }
    
    def __init__(self, model_name: str = "doubao"):
        """
        初始化Embedding提供者
        
        Args:
            model_name: 模型名称，可选: openai, openai-large, doubao
                       自动从 MODELS 配置中读取所有相关配置
        """
        self.model_name = model_name
        self.timeout = 30  # 固定超时时间为30秒
        
        # 获取模型信息
        if model_name not in self.MODELS:
            logger.bind(tag=TAG).warning(
                f"未知模型 {model_name}，使用默认模型 doubao"
            )
            model_name = "doubao"
            self.model_name = model_name
        
        # 从 MODELS 配置中读取所有模型信息
        model_info = self.MODELS[model_name]
        self.model_type = model_info["type"]
        self.embedding_dim = model_info["dim"]
        self.api_key = model_info.get("api_key")
        self.base_url = model_info.get("base_url")
        
        logger.bind(tag=TAG).info(
            f"初始化Embedding模型: {model_name} ({model_info['description']})"
        )
        
        # 根据模型类型初始化客户端
        if model_name.startswith("openai"):
            self._init_openai()
        elif model_name == "doubao":
            self._init_doubao()
        else:
            raise ValueError(f"不支持的模型: {model_name}")
    
    def _init_openai(self):
        """初始化OpenAI Embedding"""
        try:
            from openai import OpenAI
            
            # 优先使用传入的api_key，否则从环境变量获取
            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "使用OpenAI Embedding需要设置api_key参数或OPENAI_API_KEY环境变量"
                )
            
            # 初始化客户端
            client_args = {"api_key": api_key}
            if self.base_url:
                client_args["base_url"] = self.base_url
            
            self.client = OpenAI(**client_args)
            
            logger.bind(tag=TAG).info(
                f"OpenAI Embedding初始化成功 - 模型: {self.model_name}, "
                f"维度: {self.embedding_dim}"
            )
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"初始化OpenAI失败: {e}")
            raise
    
    def _init_doubao(self):
        """初始化豆包(火山引擎) Embedding"""
        try:
            from openai import OpenAI
            
            # 豆包使用OpenAI兼容接口
            api_key = self.api_key or os.getenv("DOUBAO_API_KEY")
            if not api_key:
                raise ValueError(
                    "使用豆包Embedding需要设置api_key参数或DOUBAO_API_KEY环境变量"
                )
            
            # 火山引擎默认URL
            base_url = self.base_url
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.timeout
            )
            
            logger.bind(tag=TAG).info(
                f"豆包Embedding初始化成功 - 模型: {self.MODELS[self.model_name]['name']}, "
                f"维度: {self.embedding_dim}, "
                f"URL: {base_url}"
            )
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"初始化豆包失败: {e}")
            raise
    
    def encode(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        return self._encode_api(text)
    
    def _encode_api(self, text: str) -> List[float]:
        """使用API模型编码 (OpenAI/豆包)"""
        try:
            model_config = self.MODELS[self.model_name]
            response = self.client.embeddings.create(
                model=model_config["name"],
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"API编码失败 ({self.model_name}): {e}"
            )
            raise
    
    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        # API批量处理
        model_config = self.MODELS[self.model_name]
        response = self.client.embeddings.create(
            model=model_config["name"],
            input=texts
        )
        return [item.embedding for item in response.data]

