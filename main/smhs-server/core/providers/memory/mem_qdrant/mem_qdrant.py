"""
基于Qdrant的向量记忆存储
实现与mem_local_short相同的接口，但使用向量检索
"""

from ..base import MemoryProviderBase, logger
import time
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, SearchRequest
)
from core.utils.util import check_model_key
from .embedding_utils import EmbeddingProvider

TAG = __name__

# 复用mem_local_short的Prompt
short_term_memory_prompt = """
# 时空记忆编织者

## 核心使命
构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹
根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务

## 记忆法则
### 1. 三维度记忆评估（每次更新必执行）
| 维度       | 评估标准                  | 权重分 |
|------------|---------------------------|--------|
| 时效性     | 信息新鲜度（按对话轮次） | 40%    |
| 情感强度   | 含💖标记/重复提及次数     | 35%    |
| 关联密度   | 与其他信息的连接数量      | 25%    |

### 2. 动态更新机制
**名字变更处理示例：**
原始记忆："曾用名": ["张三"], "现用名": "张三丰"
触发条件：当检测到「我叫X」「称呼我Y」等命名信号时
操作流程：
1. 将旧名移入"曾用名"列表
2. 记录命名时间轴："2024-02-15 14:32:启用张三丰"
3. 在记忆立方追加：「从张三到张三丰的身份蜕变」

### 3. 空间优化策略
- **信息压缩术**：用符号体系提升密度
  - ✅"张三丰[北/软工/🐱]"
  - ❌"北京软件工程师，养猫"
- **淘汰预警**：当总字数≥900时触发
  1. 删除权重分<60且3轮未提及的信息
  2. 合并相似条目（保留时间戳最近的）

## 记忆结构
输出格式必须为可解析的json字符串，不需要解释、注释和说明，保存记忆时仅从对话提取信息，不要混入示例内容
请将每次对话总结为一条独立的记忆片段（100-300字），而不是整个历史的全量摘要。

输出格式示例：
```json
{
  "summary": "用户今天询问了如何搭建记忆服务的问题，对向量数据库Qdrant表现出兴趣",
  "keywords": ["记忆服务", "Qdrant", "向量数据库"],
  "importance": 7,
  "emotion": "好奇"
}
```
"""


def extract_json_data(json_code: str) -> str:
    """从LLM响应中提取JSON数据"""
    start = json_code.find("```json")
    if start != -1:
        end = json_code.find("```", start + 1)
        if end != -1:
            return json_code[start + 7:end].strip()
    
    # 尝试直接解析
    try:
        json.loads(json_code)
        return json_code
    except:
        pass
    
    return ""


class MemoryProvider(MemoryProviderBase):
    """基于Qdrant的向量记忆提供者"""
    
    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        
        # Qdrant配置
        self.qdrant_url = config.get("qdrant_url", "127.0.0.1")
        self.qdrant_port = config.get("qdrant_port", 6333)
        self.qdrant_api_key = config.get("qdrant_api_key", None)
        self.collection_name = config.get("collection_name", "smhs_memories")
        
        # Embedding配置 - 只需指定模型名称
        self.embedding_model = config.get("embedding_model", "doubao")
        
        # 检索配置
        self.top_k = config.get("top_k", 5)  # 返回最相似的K条记忆
        self.similarity_threshold = config.get("similarity_threshold", 0.6)
        
        # 初始化Embedding提供者
        # 通过 model_name 自动读取 embedding_utils.py 中的所有配置
        try:
            self.embedding_provider = EmbeddingProvider(
                model_name=self.embedding_model
            )
            self.embedding_dim = self.embedding_provider.embedding_dim
            logger.bind(tag=TAG).info(
                f"Embedding初始化成功 - 模型: {self.embedding_model}, "
                f"维度: {self.embedding_dim}"
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"初始化Embedding失败: {e}")
            raise
        
        # 初始化Qdrant客户端
        try:
            # 判断是使用完整 URL 还是 host+port
            # 如果 URL 只包含 http://ip 或 https://ip 而没有端口，需要拼接端口
            if self.qdrant_url.startswith(('http://', 'https://')):
                # 检查 URL 中是否已经包含端口
                import re
                if re.match(r'https?://[^:]+:\d+', self.qdrant_url):
                    # URL 中已包含端口，直接使用
                    full_url = self.qdrant_url
                else:
                    # URL 中没有端口，需要拼接
                    full_url = f"{self.qdrant_url}:{self.qdrant_port}"
                
                logger.bind(tag=TAG).info(f"使用 URL 模式连接: {full_url}")
                self.client = QdrantClient(
                    url=full_url,
                    api_key=self.qdrant_api_key,
                    timeout=30,
                    prefer_grpc=False  # 强制使用 HTTP 客户端
                )
            else:
                # 使用 host+port 模式
                logger.bind(tag=TAG).info(
                    f"使用 host+port 模式连接: {self.qdrant_url}:{self.qdrant_port}"
                )
                self.client = QdrantClient(
                    host=self.qdrant_url,
                    port=self.qdrant_port,
                    api_key=self.qdrant_api_key,
                    timeout=30,
                    prefer_grpc=False  # 强制使用 HTTP 客户端
                )
            
            logger.bind(tag=TAG).info(
                f"Qdrant客户端初始化成功: {self.qdrant_url}:{self.qdrant_port}"
            )
            
            # 创建collection（如果不存在）
            self._ensure_collection()
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"连接Qdrant失败: {e}")
            raise
    
    def _ensure_collection(self):
        """确保collection存在且维度正确"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # 创建新的collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE  # 使用余弦相似度
                    )
                )
                logger.bind(tag=TAG).info(
                    f"创建Qdrant集合: {self.collection_name}, 维度: {self.embedding_dim}"
                )
            else:
                # 集合已存在，检查维度是否匹配
                collection_info = self.client.get_collection(self.collection_name)
                existing_dim = collection_info.config.params.vectors.size
                
                if existing_dim != self.embedding_dim:
                    logger.bind(tag=TAG).warning(
                        f"集合 {self.collection_name} 维度不匹配！"
                        f"期望: {self.embedding_dim}, 实际: {existing_dim}"
                    )
                    logger.bind(tag=TAG).warning(
                        f"将删除并重建集合 {self.collection_name}..."
                    )
                    
                    # 删除旧集合
                    self.client.delete_collection(self.collection_name)
                    logger.bind(tag=TAG).info(f"已删除旧集合: {self.collection_name}")
                    
                    # 创建新集合
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.embedding_dim,
                            distance=Distance.COSINE
                        )
                    )
                    logger.bind(tag=TAG).info(
                        f"重建集合成功: {self.collection_name}, 新维度: {self.embedding_dim}"
                    )
                else:
                    logger.bind(tag=TAG).info(
                        f"Qdrant集合已存在: {self.collection_name}, 维度: {existing_dim}"
                    )
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"创建/检查集合失败: {e}")
            raise
    
    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        """初始化记忆"""
        super().init_memory(role_id, llm, **kwargs)
        logger.bind(tag=TAG).info(f"初始化记忆 - Role ID: {self.role_id}")
    
    async def save_memory(self, msgs):
        """
        保存记忆到Qdrant
        
        工作流程：
        1. 使用LLM总结对话内容
        2. 将总结转换为向量
        3. 存储到Qdrant
        """
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM未设置")
            return None
        
        if len(msgs) < 2:
            return None
        
        try:
            # 1. 构建对话上下文
            msgStr = ""
            for msg in msgs:
                if msg.role == "user":
                    msgStr += f"User: {msg.content}\n"
                elif msg.role == "assistant":
                    msgStr += f"Assistant: {msg.content}\n"
            
            # 2. 获取历史记忆上下文（最近的3条）
            recent_memories = await self._get_recent_memories(limit=3)
            if recent_memories:
                msgStr += "\n历史记忆（参考）：\n"
                for mem in recent_memories:
                    msgStr += f"- {mem}\n"
            
            # 当前时间
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            msgStr += f"\n当前时间：{time_str}"
            
            # 3. 调用LLM生成记忆摘要
            result = self.llm.response_no_stream(
                short_term_memory_prompt,
                msgStr,
                max_tokens=500,  # 单条记忆较短
                temperature=0.2,
            )
            
            # 4. 解析JSON
            json_str = extract_json_data(result)
            if not json_str:
                logger.bind(tag=TAG).warning("LLM返回的记忆格式无效")
                return None
            
            memory_data = json.loads(json_str)
            summary = memory_data.get("summary", "")
            
            if not summary or len(summary) < 10:
                logger.bind(tag=TAG).warning("记忆摘要过短，跳过保存")
                return None
            
            # 5. 生成向量
            embedding = self.embedding_provider.encode(summary)
            
            # 验证向量维度
            actual_dim = len(embedding)
            if actual_dim != self.embedding_dim:
                logger.bind(tag=TAG).error(
                    f"向量维度不匹配！期望: {self.embedding_dim}, 实际: {actual_dim}"
                )
                return None
            
            # 6. 构建元数据
            point_id = str(uuid.uuid4())
            payload = {
                "role_id": self.role_id,
                "summary": summary,
                "keywords": memory_data.get("keywords", []),
                "importance": memory_data.get("importance", 5),
                "emotion": memory_data.get("emotion", ""),
                "timestamp": time_str,
                "created_at": int(time.time())
            }
            
            # 7. 存储到Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.bind(tag=TAG).info(
                f"记忆保存成功 - Role: {self.role_id}, ID: {point_id}, "
                f"重要性: {payload['importance']}"
            )
            
            return summary
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"保存记忆失败: {e}")
            import traceback
            logger.bind(tag=TAG).error(traceback.format_exc())
            return None
    
    async def query_memory(self, query: str) -> str:
        """
        查询相关记忆
        
        Args:
            query: 用户查询文本
            
        Returns:
            格式化的记忆字符串
        """
        try:
            # 1. 将查询转换为向量
            query_embedding = self.embedding_provider.encode(query)
            
            # 2. 在Qdrant中搜索（根据客户端版本使用不同的API）
            search_results = None
            
            if hasattr(self.client, 'query_points'):
                # 最新版本 API
                result = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="role_id",
                                match=MatchValue(value=self.role_id)
                            )
                        ]
                    ),
                    limit=self.top_k,
                    score_threshold=self.similarity_threshold
                )
                search_results = result.points if hasattr(result, 'points') else result
                
            elif hasattr(self.client, 'search'):
                # 旧版本 API
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="role_id",
                                match=MatchValue(value=self.role_id)
                            )
                        ]
                    ),
                    limit=self.top_k,
                    score_threshold=self.similarity_threshold
                )
            else:
                logger.bind(tag=TAG).error("客户端没有可用的搜索方法")
                return ""
            
            if not search_results:
                return ""
            
            # 3. 格式化返回结果
            memories = []
            for result in search_results:
                payload = result.payload
                score = result.score
                
                memory_str = (
                    f"[{payload['timestamp']}] "
                    f"{payload['summary']} "
                    f"(相似度: {score:.2f}, 重要性: {payload['importance']})"
                )
                memories.append(memory_str)
            
            memories_text = "\n".join(f"- {mem}" for mem in memories)
            
            logger.bind(tag=TAG).info(
                f"检索到 {len(memories)} 条相关记忆 - Role: {self.role_id}"
            )
            
            return memories_text
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"查询记忆失败: {e}")
            return ""
    
    async def _get_recent_memories(self, limit: int = 5) -> List[str]:
        """获取最近的记忆（按时间排序）"""
        try:
            # 使用scroll API获取最近的记忆
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="role_id",
                            match=MatchValue(value=self.role_id)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            points = results[0] if results else []
            
            # 按时间戳排序
            sorted_points = sorted(
                points,
                key=lambda x: x.payload.get("created_at", 0),
                reverse=True
            )
            
            return [
                f"[{p.payload['timestamp']}] {p.payload['summary']}"
                for p in sorted_points[:limit]
            ]
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"获取最近记忆失败: {e}")
            return []
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        try:
            # 获取用户的所有记忆
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="role_id",
                            match=MatchValue(value=self.role_id)
                        )
                    ]
                )
            )
            
            return {
                "role_id": self.role_id,
                "total_memories": count_result.count,
                "collection": self.collection_name
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"获取统计信息失败: {e}")
            return {}

