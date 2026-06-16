"""智能员工类型注册表模块

提供智能员工类型的注册和管理功能，确保只有已注册的类型可以被实例化。
"""
from typing import Dict, Type, Any
from bo.ai_worker import AIWorker


class WorkerTypeRegistry:
    """
    智能员工类型注册表
    
    用于管理和注册所有可用的智能员工类型，确保只有已注册的类型可以被实例化。
    
    示例用法:
        # 注册类型
        WorkerTypeRegistry.register("AIWorker", AIWorker)
        
        # 获取类型
        worker_class = WorkerTypeRegistry.get("AIWorker")
        
        # 检查类型是否已注册
        if WorkerTypeRegistry.is_registered("AIWorker"):
            print("AIWorker已注册")
    """
    
    _registry: Dict[str, Type[AIWorker]] = {}
    
    @classmethod
    def register(cls, type_name: str, worker_class: Type[AIWorker]) -> None:
        """
        注册智能员工类型
        
        :param type_name: 类型名称
        :param worker_class: 智能员工类（必须是AIWorker的子类）
        :raises ValueError: 如果类型名称已存在或类不是AIWorker的子类
        """
        if not issubclass(worker_class, AIWorker):
            raise ValueError(f"{worker_class.__name__} 必须是 AIWorker 的子类")
        
        if type_name in cls._registry:
            raise ValueError(f"类型 {type_name} 已注册")
        
        cls._registry[type_name] = worker_class
    
    @classmethod
    def unregister(cls, type_name: str) -> None:
        """
        注销智能员工类型
        
        :param type_name: 类型名称
        :raises ValueError: 如果类型不存在
        """
        if type_name not in cls._registry:
            raise ValueError(f"类型 {type_name} 未注册")
        
        del cls._registry[type_name]
    
    @classmethod
    def get(cls, type_name: str) -> Type[AIWorker]:
        """
        获取智能员工类型
        
        :param type_name: 类型名称
        :return: 智能员工类
        :raises ValueError: 如果类型不存在
        """
        if type_name not in cls._registry:
            raise ValueError(f"类型 {type_name} 未注册，请先注册")
        
        return cls._registry[type_name]
    
    @classmethod
    def is_registered(cls, type_name: str) -> bool:
        """
        检查类型是否已注册
        
        :param type_name: 类型名称
        :return: 如果已注册返回True，否则返回False
        """
        return type_name in cls._registry
    
    @classmethod
    def get_all_types(cls) -> Dict[str, Type[AIWorker]]:
        """
        获取所有已注册的类型
        
        :return: 类型名称到类型的映射
        """
        return cls._registry.copy()
    
    @classmethod
    def create_worker(cls, type_name: str, **kwargs) -> AIWorker:
        """
        创建智能员工实例
        
        :param type_name: 类型名称
        :param kwargs: 员工初始化参数
        :return: 智能员工实例
        :raises ValueError: 如果类型不存在
        """
        worker_class = cls.get(type_name)
        return worker_class(**kwargs)


# 默认注册AIWorker类型
WorkerTypeRegistry.register("AIWorker", AIWorker)