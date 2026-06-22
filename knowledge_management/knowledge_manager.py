"""知识管理服务

提供对知识的增、删、改、查等基础服务。
知识是指由用户提供的文本，由标题、摘要和内容组成。
"""

import json
import os
import logging
from typing import List, Optional
from datetime import datetime

from .models import Knowledge, KnowledgeQueryParams

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    知识管理服务
    
    管理知识库，提供增、删、改、查等基础服务。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化知识管理器"""
        self._storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), 'knowledge_base', 'knowledge.json'
        )
        self._knowledge_list: List[Knowledge] = []
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        
        # 加载知识库
        self._load_knowledge()
        
        # 如果知识库为空，初始化预置知识
        if not self._knowledge_list:
            self._initialize_default_knowledge()
            self._save_knowledge()
    
    def _load_knowledge(self):
        """从文件加载知识"""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._knowledge_list = [Knowledge(**item) for item in data]
                logger.info(f"成功加载 {len(self._knowledge_list)} 条知识")
            else:
                logger.info("知识库文件不存在，将创建新的知识库")
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
            self._knowledge_list = []
    
    def _save_knowledge(self):
        """保存知识到文件"""
        try:
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                data = [knowledge.dict() for knowledge in self._knowledge_list]
                json.dump(data, f, ensure_ascii=False, indent=2,
                          default=self._datetime_to_str)
            logger.info(f"成功保存 {len(self._knowledge_list)} 条知识")
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
    
    def _datetime_to_str(self, obj):
        """datetime转字符串"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    
    def _initialize_default_knowledge(self):
        """初始化预置知识"""
        logger.info("初始化预置知识")
        
        default_knowledge = [
            Knowledge(
                knowledge_id="KNOW_EVAL_001",
                title="SMART原则详解",
                summary="SMART原则是设定目标的五大准则，包括具体、可衡量、可实现、相关、有时限",
                content="""SMART原则是管理学中设定目标的五大准则：
1. Specific（具体）：目标应清晰明确，避免模糊不清
2. Measurable（可衡量）：目标应有明确的衡量标准，便于评估达成情况
3. Achievable（可实现）：目标应具有挑战性但可实现，避免过于困难或过于简单
4. Relevant（相关）：目标应与组织战略和整体目标保持一致
5. Time-bound（有时限）：目标应设定明确的完成时间节点

在评估方案目标完整性时，需检查每个目标是否符合SMART原则。""",
                index_ids=["IDX_COMP_001"],
                tags=["目标管理", "SMART", "完整性评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_002",
                title="资源需求分析方法",
                summary="介绍如何系统分析方案所需的人力、物力、财力资源",
                content="""资源需求分析是方案评估的重要环节，主要包括：
1. 人力资源分析：确定所需人员数量、技能要求、岗位职责
2. 物力资源分析：确定所需设备、设施、材料等物资
3. 财力资源分析：编制预算，确定资金来源和使用计划
4. 时间资源分析：确定项目周期、关键路径、里程碑

资源需求分析应遵循以下原则：
- 全面性：覆盖所有类型的资源需求
- 准确性：基于充分的调研和估算
- 合理性：资源配置与目标相匹配
- 可行性：资源来源可靠，获取途径明确""",
                index_ids=["IDX_COMP_003"],
                tags=["资源管理", "资源分析", "完整性评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_003",
                title="战略一致性评估框架",
                summary="评估方案与组织战略目标一致性的方法论",
                content="""战略一致性评估用于判断方案是否与组织战略目标保持一致：

评估维度：
1. 目标对齐：方案目标是否与战略目标一致
2. 资源匹配：方案资源需求是否与战略资源配置一致
3. 优先级排序：方案是否支持战略优先级
4. 风险承受：方案风险是否在战略风险承受范围内
5. 价值贡献：方案是否为战略目标实现做出实质性贡献

评估方法：
- 战略地图分析法：将方案目标映射到战略地图的各个层面
- 平衡计分卡法：从财务、客户、内部流程、学习成长四个维度评估
- 优先级矩阵法：评估方案对战略优先级的支持程度""",
                index_ids=["IDX_RAT_001"],
                tags=["战略管理", "战略对齐", "合理性评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_004",
                title="技术可行性评估方法",
                summary="评估方案技术方案可行性的系统方法",
                content="""技术可行性评估是判断方案技术方案是否可行的关键步骤：

评估内容：
1. 技术成熟度：所采用技术是否成熟，是否经过验证
2. 技术储备：组织是否具备相关技术能力和人才
3. 技术风险：是否存在技术不确定性和潜在风险
4. 技术兼容性：技术方案是否与现有系统兼容
5. 技术演进：技术方案是否具有扩展性和演进能力

评估方法：
- 技术就绪水平（TRL）评估：评估技术从概念到成熟的阶段
- 专家评审法：邀请技术专家进行评估
- 原型验证法：通过原型验证技术可行性
- 风险矩阵法：评估技术风险的可能性和影响程度""",
                index_ids=["IDX_RAT_002"],
                tags=["技术评估", "可行性研究", "合理性评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_005",
                title="成本收益分析指南",
                summary="进行经济合理性评估的成本收益分析方法",
                content="""成本收益分析是评估方案经济合理性的核心方法：

分析步骤：
1. 识别成本：包括直接成本和间接成本
2. 识别收益：包括直接收益和间接收益
3. 量化成本收益：将成本和收益转化为货币价值
4. 计算指标：净现值(NPV)、内部收益率(IRR)、投资回收期等
5. 敏感性分析：评估关键变量变化对结果的影响

评估标准：
- NPV > 0：项目可行
- IRR > 基准收益率：项目可行
- 投资回收期 < 预期回收期：项目可行

注意事项：
- 考虑时间价值：使用折现率计算现值
- 考虑风险因素：对不确定因素进行敏感性分析
- 考虑机会成本：比较替代方案的收益""",
                index_ids=["IDX_RAT_003"],
                tags=["成本收益分析", "经济评估", "合理性评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_006",
                title="仿真效率评估指标",
                summary="评估仿真执行效率的关键指标和方法",
                content="""仿真效率评估关注仿真执行的性能表现：

核心指标：
1. 执行时间：仿真完成所需的总时间
2. 时间步长：仿真的时间分辨率
3. 资源利用率：CPU、内存等资源的使用情况
4. 收敛速度：仿真达到稳定状态的速度
5. 吞吐量：单位时间内处理的事件数量

评估方法：
- 基准测试法：与标准模型进行对比
- 瓶颈分析法：识别性能瓶颈所在
- 优化建议：提出性能优化方案

优化策略：
- 算法优化：改进仿真算法
- 并行计算：利用多核处理器
- 模型简化：在保证精度的前提下简化模型""",
                index_ids=["IDX_SIM_001"],
                tags=["仿真效率", "性能评估", "效率评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_007",
                title="仿真覆盖完备性评估",
                summary="评估仿真场景覆盖程度的方法和标准",
                content="""仿真覆盖完备性评估确保仿真覆盖所有关键场景：

评估维度：
1. 正常场景：典型的业务流程和操作场景
2. 异常场景：故障、错误、异常情况
3. 边界场景：参数边界、极端条件
4. 并发场景：多用户、多任务并发情况
5. 时序场景：时间相关的业务场景

评估方法：
- 场景矩阵法：建立场景覆盖矩阵
- 覆盖率统计：计算各类场景的覆盖率
- 专家评审：邀请领域专家评估覆盖充分性

覆盖标准：
- 正常场景覆盖率 ≥ 95%
- 异常场景覆盖率 ≥ 80%
- 边界场景覆盖率 ≥ 85%""",
                index_ids=["IDX_SIM_002"],
                tags=["仿真覆盖", "完备性评估", "效率评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_008",
                title="风险识别与评估方法",
                summary="系统识别和评估方案风险的方法论",
                content="""风险识别与评估是方案评估的重要组成部分：

风险识别方法：
1. 头脑风暴法：组织专家团队进行风险讨论
2. 情景分析法：分析不同情景下的风险
3. 历史数据法：参考类似项目的历史风险
4. SWOT分析法：分析优势、劣势、机会、威胁

风险评估维度：
1. 可能性：风险发生的概率
2. 影响程度：风险发生后的影响大小
3. 紧迫性：风险发生的时间紧迫性

风险等级划分：
- 高风险：可能性高、影响大
- 中风险：可能性中、影响中
- 低风险：可能性低、影响小

风险应对策略：
- 规避：避免风险发生
- 转移：将风险转移给第三方
- 减轻：降低风险可能性或影响
- 接受：接受风险并制定应急计划""",
                index_ids=["IDX_RISK_001"],
                tags=["风险管理", "风险评估", "风险识别"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_009",
                title="方案完整性评估标准",
                summary="方案完整性评估的综合标准和指南",
                content="""方案完整性评估是对方案内容全面性的系统检查：

完整性评估标准：
1. 目标完整性：目标明确、具体、可衡量
2. 内容完整性：包含所有必要的组成部分
3. 逻辑完整性：各部分之间逻辑关系清晰
4. 信息完整性：信息充分、准确、可靠
5. 结构完整性：结构合理、层次分明

完整性评估检查清单：
- 是否有明确的目标和范围
- 是否有详细的执行计划
- 是否有资源需求和预算
- 是否有风险识别和应对措施
- 是否有时间节点和里程碑
- 是否有责任分工和组织架构
- 是否有监控和评估机制
- 是否有沟通和协调方案

完整性评分标准：
- 90-100分：完整，无需补充
- 70-89分：基本完整，需少量补充
- 50-69分：部分完整，需较多补充
- 0-49分：不完整，需大幅完善""",
                index_ids=["IDX_COMP_000"],
                tags=["完整性评估", "评估标准", "方案评估"],
                category="evaluation"
            ),
            Knowledge(
                knowledge_id="KNOW_EVAL_010",
                title="方案合理性评估框架",
                summary="方案合理性评估的综合框架和方法论",
                content="""方案合理性评估是对方案可行性和有效性的综合判断：

评估维度：
1. 战略合理性：与组织战略目标的一致性
2. 技术合理性：技术方案的可行性
3. 经济合理性：投入产出比的合理性
4. 操作合理性：操作流程的可行性
5. 时间合理性：时间安排的合理性

评估方法：
- 多准则决策分析(MCDA)：综合多个评估准则
- 层次分析法(AHP)：建立层次结构进行权重分析
- 专家打分法：邀请专家进行综合评估

合理性评分标准：
- 90-100分：合理，可直接实施
- 70-89分：基本合理，需少量调整
- 50-69分：部分合理，需较大调整
- 0-49分：不合理，需重新设计

评估流程：
1. 明确评估目标和范围
2. 收集相关信息和数据
3. 应用评估方法进行分析
4. 综合判断并形成结论
5. 提出改进建议""",
                index_ids=["IDX_RAT_000"],
                tags=["合理性评估", "评估框架", "方案评估"],
                category="evaluation"
            )
        ]
        
        self._knowledge_list = default_knowledge
        logger.info(f"已初始化 {len(default_knowledge)} 条预置知识")
    
    def add_knowledge(self, knowledge: Knowledge) -> Knowledge:
        """添加知识"""
        if any(existing.knowledge_id == knowledge.knowledge_id for existing in self._knowledge_list):
            raise ValueError(f"知识ID已存在: {knowledge.knowledge_id}")
        
        knowledge.created_at = datetime.now()
        knowledge.updated_at = datetime.now()
        self._knowledge_list.append(knowledge)
        self._save_knowledge()
        
        logger.info(f"添加知识: {knowledge.knowledge_id} - {knowledge.title}")
        return knowledge
    
    def update_knowledge(self, knowledge_id: str, **kwargs) -> Knowledge:
        """更新知识"""
        for knowledge in self._knowledge_list:
            if knowledge.knowledge_id == knowledge_id:
                for key, value in kwargs.items():
                    if hasattr(knowledge, key):
                        setattr(knowledge, key, value)
                
                knowledge.updated_at = datetime.now()
                self._save_knowledge()
                
                logger.info(f"更新知识: {knowledge_id}")
                return knowledge
        
        raise ValueError(f"知识不存在: {knowledge_id}")
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """删除知识"""
        original_count = len(self._knowledge_list)
        self._knowledge_list = [k for k in self._knowledge_list if k.knowledge_id != knowledge_id]
        
        if len(self._knowledge_list) < original_count:
            self._save_knowledge()
            logger.info(f"删除知识: {knowledge_id}")
            return True
        
        raise ValueError(f"知识不存在: {knowledge_id}")
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Knowledge]:
        """根据ID获取知识"""
        for knowledge in self._knowledge_list:
            if knowledge.knowledge_id == knowledge_id:
                return knowledge
        return None
    
    def query_knowledge(self, params: KnowledgeQueryParams) -> List[Knowledge]:
        """查询知识"""
        results = self._knowledge_list
        
        if params.is_active is not None:
            results = [k for k in results if k.is_active == params.is_active]
        
        if params.knowledge_id:
            results = [k for k in results if params.knowledge_id in k.knowledge_id]
        
        if params.title:
            results = [k for k in results if params.title in k.title]
        
        if params.index_id:
            results = [k for k in results if params.index_id in k.index_ids]
        
        if params.tag:
            results = [k for k in results if params.tag in k.tags]
        
        if params.category:
            results = [k for k in results if params.category in k.category]
        
        return results
    
    def list_knowledge(self) -> List[Knowledge]:
        """获取所有知识"""
        return self._knowledge_list
    
    def get_knowledge_by_index(self, index_id: str) -> List[Knowledge]:
        """获取与指定评价指标相关的知识"""
        return [k for k in self._knowledge_list if index_id in k.index_ids]
    
    def search_knowledge(self, query: str) -> List[Knowledge]:
        """搜索知识（基于标题、摘要、内容）"""
        query_lower = query.lower()
        results = []
        
        for knowledge in self._knowledge_list:
            if (query_lower in knowledge.title.lower() or
                query_lower in knowledge.summary.lower() or
                query_lower in knowledge.content.lower()):
                results.append(knowledge)
        
        return results


# 全局知识管理器实例
_knowledge_manager = None


def get_knowledge_manager(storage_path: Optional[str] = None) -> KnowledgeManager:
    """获取知识管理器单例"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager(storage_path)
    return _knowledge_manager
