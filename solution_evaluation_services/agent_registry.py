"""Agent服务注册表模块

用于管理可用的评价Agent，提供注册、发现、调度等功能。
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Type, Callable
from threading import Lock
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_evaluation_agent import (
    BaseEvaluationAgent,
    AgentConfig,
    AgentType,
    AgentStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRegistration(BaseModel):
    """Agent注册信息"""
    agent_id: str = Field(description="Agent ID")
    name: str = Field(description="Agent名称")
    agent_type: AgentType = Field(description="Agent类型")
    description: Optional[str] = Field(default=None, description="Agent描述")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")
    last_heartbeat: datetime = Field(default_factory=datetime.now, description="最后心跳时间")
    is_active: bool = Field(default=True, description="是否活跃")


class AgentRegistry:
    """
    Agent服务注册表
    
    用于管理可用的评价Agent，提供：
    - Agent注册与注销
    - Agent发现与查询
    - Agent健康检查
    - Agent负载均衡
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化Agent注册表
        
        :param storage_path: 注册信息存储路径
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._agents: Dict[str, BaseEvaluationAgent] = {}
        self._registrations: Dict[str, AgentRegistration] = {}
        self._type_index: Dict[AgentType, List[str]] = {t: [] for t in AgentType}
        self._storage_path = storage_path or "agent_registry_data"
        self._logger = logger
        
        os.makedirs(self._storage_path, exist_ok=True)
        self._initialized = True
        
        # 加载已保存的注册信息
        self._load_registrations()
    
    def register(self, agent: BaseEvaluationAgent, 
                capabilities: Optional[List[str]] = None,
                description: Optional[str] = None) -> bool:
        """
        注册Agent
        
        :param agent: Agent实例
        :param capabilities: 能力列表
        :param description: Agent描述
        :return: 是否注册成功
        """
        agent_id = agent.agent_id
        
        if agent_id in self._agents:
            self._logger.warning(f"Agent {agent_id} 已存在，更新注册信息")
        
        # 存储Agent实例
        self._agents[agent_id] = agent
        
        # 创建注册信息
        registration = AgentRegistration(
            agent_id=agent_id,
            name=agent.name,
            agent_type=agent.agent_type,
            description=description or agent.config.description,
            capabilities=capabilities or [],
            registered_at=datetime.now(),
            last_heartbeat=datetime.now(),
            is_active=True
        )
        self._registrations[agent_id] = registration
        
        # 更新类型索引
        if agent_id not in self._type_index[agent.agent_type]:
            self._type_index[agent.agent_type].append(agent_id)
        
        # 保存注册信息
        self._save_registrations()
        
        self._logger.info(f"Agent {agent_id} ({agent.name}) 注册成功")
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """
        注销Agent
        
        :param agent_id: Agent ID
        :return: 是否注销成功
        """
        if agent_id not in self._agents:
            self._logger.warning(f"Agent {agent_id} 不存在")
            return False
        
        agent = self._agents[agent_id]
        agent_type = agent.agent_type
        
        # 移除Agent
        del self._agents[agent_id]
        del self._registrations[agent_id]
        
        # 更新类型索引
        if agent_id in self._type_index[agent_type]:
            self._type_index[agent_type].remove(agent_id)
        
        # 保存注册信息
        self._save_registrations()
        
        self._logger.info(f"Agent {agent_id} 注销成功")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[BaseEvaluationAgent]:
        """
        获取Agent实例
        
        :param agent_id: Agent ID
        :return: Agent实例
        """
        return self._agents.get(agent_id)
    
    def get_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """
        获取Agent注册信息
        
        :param agent_id: Agent ID
        :return: 注册信息
        """
        return self._registrations.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseEvaluationAgent]:
        """
        按类型获取Agent列表
        
        :param agent_type: Agent类型
        :return: Agent列表
        """
        agent_ids = self._type_index.get(agent_type, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[BaseEvaluationAgent]:
        """
        获取可用的Agent列表
        
        :param agent_type: Agent类型（可选）
        :return: 可用Agent列表
        """
        if agent_type:
            agents = self.get_agents_by_type(agent_type)
        else:
            agents = list(self._agents.values())
        
        return [agent for agent in agents if agent.is_available]
    
    def select_agent(self, agent_type: AgentType, 
                    strategy: str = "round_robin") -> Optional[BaseEvaluationAgent]:
        """
        选择一个Agent（支持负载均衡策略）
        
        :param agent_type: Agent类型
        :param strategy: 选择策略（round_robin/random/least_used）
        :return: 选中的Agent
        """
        available_agents = self.get_available_agents(agent_type)
        
        if not available_agents:
            return None
        
        if strategy == "random":
            import random
            return random.choice(available_agents)
        elif strategy == "least_used":
            return min(available_agents, key=lambda a: a._usage_count)
        else:  # round_robin
            return available_agents[0]
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有Agent信息
        
        :return: Agent信息列表
        """
        return [agent.get_info() for agent in self._agents.values()]
    
    def list_registrations(self) -> List[AgentRegistration]:
        """
        列出所有注册信息
        
        :return: 注册信息列表
        """
        return list(self._registrations.values())
    
    def heartbeat(self, agent_id: str) -> bool:
        """
        更新Agent心跳
        
        :param agent_id: Agent ID
        :return: 是否成功
        """
        if agent_id in self._registrations:
            self._registrations[agent_id].last_heartbeat = datetime.now()
            self._registrations[agent_id].is_active = True
            return True
        return False
    
    def check_health(self, agent_id: str) -> Dict[str, Any]:
        """
        检查Agent健康状态
        
        :param agent_id: Agent ID
        :return: 健康状态信息
        """
        agent = self._agents.get(agent_id)
        registration = self._registrations.get(agent_id)
        
        if not agent or not registration:
            return {"status": "not_found", "agent_id": agent_id}
        
        return {
            "status": "healthy" if agent.is_available else "unhealthy",
            "agent_id": agent_id,
            "name": agent.name,
            "agent_type": agent.agent_type.value,
            "agent_status": agent.status.value,
            "is_active": registration.is_active,
            "last_heartbeat": registration.last_heartbeat.isoformat(),
            "usage_count": agent._usage_count,
            "error_count": agent._error_count
        }
    
    def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """
        检查所有Agent健康状态
        
        :return: 健康状态字典
        """
        return {agent_id: self.check_health(agent_id) for agent_id in self._agents}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取注册表统计信息
        
        :return: 统计信息
        """
        total_agents = len(self._agents)
        available_agents = len(self.get_available_agents())
        
        type_stats = {}
        for agent_type in AgentType:
            agents = self.get_agents_by_type(agent_type)
            type_stats[agent_type.value] = {
                "total": len(agents),
                "available": len([a for a in agents if a.is_available])
            }
        
        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "by_type": type_stats,
            "registrations": len(self._registrations)
        }
    
    def _save_registrations(self) -> None:
        """保存注册信息到文件"""
        file_path = os.path.join(self._storage_path, "registrations.json")
        data = {
            agent_id: reg.model_dump()
            for agent_id, reg in self._registrations.items()
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def _load_registrations(self) -> None:
        """从文件加载注册信息"""
        file_path = os.path.join(self._storage_path, "registrations.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for agent_id, reg_data in data.items():
                        reg_data['agent_type'] = AgentType(reg_data['agent_type'])
                        self._registrations[agent_id] = AgentRegistration(**reg_data)
            except Exception as e:
                self._logger.error(f"加载注册信息失败: {e}")
    
    def clear(self) -> None:
        """清空注册表"""
        self._agents.clear()
        self._registrations.clear()
        for agent_type in AgentType:
            self._type_index[agent_type] = []
        self._save_registrations()


# 全局注册表实例
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """获取全局注册表实例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(agent: BaseEvaluationAgent, 
                  capabilities: Optional[List[str]] = None,
                  description: Optional[str] = None) -> bool:
    """注册Agent到全局注册表"""
    return get_registry().register(agent, capabilities, description)


def get_agent(agent_id: str) -> Optional[BaseEvaluationAgent]:
    """从全局注册表获取Agent"""
    return get_registry().get_agent(agent_id)


def select_agent(agent_type: AgentType, strategy: str = "round_robin") -> Optional[BaseEvaluationAgent]:
    """从全局注册表选择Agent"""
    return get_registry().select_agent(agent_type, strategy)
