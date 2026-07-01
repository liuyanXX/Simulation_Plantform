"""结果空间 · 指标评估管理业务管理逻辑

EvaluationManager 面向业务层, 编排评估对象 / 计分规则 / 评估模板(含指标关联) /
评估任务 / 指标填报 / 结果快照 的完整生命周期, 底层通过 SrltEvaluationService
操作 srlt_ 数据表。

计分引擎 (compute_score) 支持四种计分规则:
  1 固定分档 (fixed_level): rule_config_json = {"levels": [{"label","score"}...]},
    raw_value 为档位 label 或索引。
  2 线性公式 (linear): 依据指标阈值将 raw_value 线性映射到 [0, full_score]。
  3 阶梯阈值 (step_threshold): rule_config_json = {"steps":[{"min","max","score"}...]}。
  4 自定义表达式 (expression): 对 raw_value(x) 求四则运算表达式值。

设计要点:
  - 短连接模式, 每次调用创建 Service, 与现有 router 风格一致。
  - 与知识空间指标库 (km_indicator_info) 通过 indicator_id 关联, 不修改其数据。
  - 完成任务 (finish_task) 时按模板权重汇总总分并异步固化生成快照。
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from data_storage_services.sql_db_services.srlt.evaluation_service import SrltEvaluationService
from bo.srlt.evaluation import (
    CalcType,
    EvaluateObject,
    EvaluateSnapshot,
    EvaluateTask,
    EvaluateTemplate,
    ScoreRule,
    TaskIndicatorRecord,
    TaskStatus,
    TemplateIndicatorRel,
)

logger = logging.getLogger("EvaluationManager")

_ALLOWED_EXPR = re.compile(r"^[0-9xX_.+\-*/()\s]+$")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def rank_of(score: Optional[float]) -> str:
    """按总分映射综合评级。"""
    if score is None:
        return "未评级"
    if score >= 90:
        return "优秀"
    if score >= 80:
        return "良好"
    if score >= 60:
        return "合格"
    if score >= 40:
        return "待改进"
    return "不合格"


class EvaluationManager:
    """指标评估管理业务管理器。"""

    def __init__(self, db_path: Optional[str] = None, db_name: Optional[str] = None) -> None:
        self._db_path = db_path
        self._db_name = db_name

    def _svc(self) -> SrltEvaluationService:
        return SrltEvaluationService(db_path=self._db_path, db_name=self._db_name)

    # ==================================================================
    # 对象类型字典 / 评估对象
    # ==================================================================
    def list_object_types(self):
        svc = self._svc()
        try:
            return svc.list_object_types()
        finally:
            svc._op.disconnect()

    def create_object(self, object_type: int, object_name: str, object_code: str,
                      org_id: Optional[int] = None, ext_json: Optional[Dict[str, Any]] = None,
                      status: int = 1) -> EvaluateObject:
        svc = self._svc()
        try:
            obj = EvaluateObject(object_type=object_type, object_name=object_name.strip(),
                                 object_code=object_code.strip(), org_id=org_id,
                                 ext_json=ext_json or {}, status=status)
            return svc.add_object(obj)
        finally:
            svc._op.disconnect()

    def update_object(self, object_id: int, **fields: Any) -> EvaluateObject:
        svc = self._svc()
        try:
            existing = svc.get_object(object_id)
            if existing is None:
                raise ValueError(f"评估对象不存在: {object_id}")
            for k, v in fields.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            return svc.update_object(existing)
        finally:
            svc._op.disconnect()

    def delete_object(self, object_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_object(object_id)
        finally:
            svc._op.disconnect()

    def get_object(self, object_id: int) -> Optional[EvaluateObject]:
        svc = self._svc()
        try:
            return svc.get_object(object_id)
        finally:
            svc._op.disconnect()

    def list_objects(self, object_type=None, org_id=None, status=None, keyword=None,
                     page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        svc = self._svc()
        try:
            offset = (max(1, page) - 1) * page_size
            items = svc.list_objects(object_type=object_type, org_id=org_id, status=status,
                                     keyword=keyword, limit=page_size, offset=offset)
            total = svc.count_objects(object_type=object_type, org_id=org_id, status=status, keyword=keyword)
            return {"list": items, "total": total, "page": page, "page_size": page_size}
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 计分规则
    # ==================================================================
    def create_rule(self, rule_name: str, calc_type: int = 1, rule_config_json=None,
                    expression=None, remark=None) -> ScoreRule:
        svc = self._svc()
        try:
            rule = ScoreRule(rule_name=rule_name.strip(), calc_type=calc_type,
                             rule_config_json=rule_config_json or {}, expression=expression, remark=remark)
            return svc.add_rule(rule)
        finally:
            svc._op.disconnect()

    def update_rule(self, rule_id: int, **fields: Any) -> ScoreRule:
        svc = self._svc()
        try:
            existing = svc.get_rule(rule_id)
            if existing is None:
                raise ValueError(f"计分规则不存在: {rule_id}")
            for k, v in fields.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            return svc.update_rule(existing)
        finally:
            svc._op.disconnect()

    def delete_rule(self, rule_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_rule(rule_id)
        finally:
            svc._op.disconnect()

    def list_rules(self, calc_type: Optional[int] = None) -> List[ScoreRule]:
        svc = self._svc()
        try:
            return svc.list_rules(calc_type=calc_type)
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 评估模板 + 指标关联
    # ==================================================================
    def create_template(self, template_name: str, template_code: str, scene_type: int = 1,
                        template_desc=None, total_score: int = 100, is_preset: int = 0,
                        version: int = 1, status: int = 1, create_user=None) -> EvaluateTemplate:
        svc = self._svc()
        try:
            tpl = EvaluateTemplate(template_name=template_name.strip(), template_code=template_code.strip(),
                                   scene_type=scene_type, template_desc=template_desc, total_score=total_score,
                                   is_preset=is_preset, version=version, status=status, create_user=create_user)
            return svc.add_template(tpl)
        finally:
            svc._op.disconnect()

    def update_template(self, template_id: int, **fields: Any) -> EvaluateTemplate:
        svc = self._svc()
        try:
            existing = svc.get_template(template_id)
            if existing is None:
                raise ValueError(f"评估模板不存在: {template_id}")
            for k, v in fields.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            return svc.update_template(existing)
        finally:
            svc._op.disconnect()

    def delete_template(self, template_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_template(template_id)
        finally:
            svc._op.disconnect()

    def get_template_detail(self, template_id: int) -> Optional[Dict[str, Any]]:
        svc = self._svc()
        try:
            tpl = svc.get_template(template_id)
            if tpl is None:
                return None
            data = tpl.model_dump()
            data["indicators"] = [r.model_dump() for r in svc.list_template_indicators(template_id)]
            return data
        finally:
            svc._op.disconnect()

    def list_templates(self, scene_type=None, is_preset=None, status=None, keyword=None,
                       page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        svc = self._svc()
        try:
            offset = (max(1, page) - 1) * page_size
            items = svc.list_templates(scene_type=scene_type, is_preset=is_preset, status=status,
                                       keyword=keyword, limit=page_size, offset=offset)
            total = svc.count_templates(scene_type=scene_type, is_preset=is_preset, status=status, keyword=keyword)
            return {"list": items, "total": total, "page": page, "page_size": page_size}
        finally:
            svc._op.disconnect()

    def set_template_indicators(self, template_id: int, indicators: List[Dict[str, Any]]) -> List[TemplateIndicatorRel]:
        """全量重置模板指标关联; 校验权重总和为100(允许为空)。"""
        svc = self._svc()
        try:
            if svc.get_template(template_id) is None:
                raise ValueError(f"评估模板不存在: {template_id}")
            rels = [
                TemplateIndicatorRel(
                    template_id=template_id,
                    indicator_id=int(it["indicator_id"]),
                    weight=float(it.get("weight", 0) or 0),
                    template_score_rule_id=it.get("template_score_rule_id"),
                    sort=int(it.get("sort", 0) or 0),
                    must_fill=int(it.get("must_fill", 1) if it.get("must_fill") is not None else 1),
                )
                for it in indicators
            ]
            if rels:
                total_weight = round(sum(r.weight for r in rels), 2)
                if abs(total_weight - 100.0) > 0.01:
                    raise ValueError(f"指标权重总和必须为100, 当前为 {total_weight}")
            return svc.set_template_indicators(template_id, rels)
        finally:
            svc._op.disconnect()

    def list_template_indicators(self, template_id: int) -> List[TemplateIndicatorRel]:
        svc = self._svc()
        try:
            return svc.list_template_indicators(template_id)
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 计分引擎
    # ==================================================================
    def compute_score(self, rule: Optional[ScoreRule], raw_value: Any, full_score: float = 100.0,
                      min_threshold: Optional[float] = None, max_threshold: Optional[float] = None,
                      positive: bool = True) -> Optional[float]:
        """依据计分规则计算单指标得分。规则为空时尝试将 raw_value 直接作为分值。"""
        if rule is None:
            try:
                return round(float(raw_value), 2)
            except (ValueError, TypeError):
                return None
        try:
            if rule.calc_type == CalcType.FIXED_LEVEL.value:
                return self._score_fixed_level(rule, raw_value)
            if rule.calc_type == CalcType.LINEAR.value:
                return self._score_linear(raw_value, full_score, min_threshold, max_threshold, positive)
            if rule.calc_type == CalcType.STEP_THRESHOLD.value:
                return self._score_step(rule, raw_value)
            if rule.calc_type == CalcType.EXPRESSION.value:
                return self._score_expression(rule, raw_value)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning("compute_score 失败: %s", e)
            return None
        return None

    @staticmethod
    def _score_fixed_level(rule: ScoreRule, raw_value: Any) -> Optional[float]:
        levels = (rule.rule_config_json or {}).get("levels", [])
        for i, lv in enumerate(levels):
            if str(lv.get("label")) == str(raw_value) or str(i) == str(raw_value):
                return round(float(lv.get("score", 0)), 2)
        return None

    @staticmethod
    def _score_linear(raw_value: Any, full_score: float, min_threshold, max_threshold, positive: bool) -> Optional[float]:
        if min_threshold is None or max_threshold is None or max_threshold == min_threshold:
            return None
        x = float(raw_value)
        ratio = (x - min_threshold) / (max_threshold - min_threshold)
        ratio = max(0.0, min(1.0, ratio))
        if not positive:
            ratio = 1.0 - ratio
        return round(ratio * full_score, 2)

    @staticmethod
    def _score_step(rule: ScoreRule, raw_value: Any) -> Optional[float]:
        x = float(raw_value)
        for step in (rule.rule_config_json or {}).get("steps", []):
            lo = step.get("min")
            hi = step.get("max")
            lo_ok = lo is None or x >= float(lo)
            hi_ok = hi is None or x < float(hi)
            if lo_ok and hi_ok:
                return round(float(step.get("score", 0)), 2)
        return None

    @staticmethod
    def _score_expression(rule: ScoreRule, raw_value: Any) -> Optional[float]:
        expr = (rule.expression or "").strip()
        if not expr or not _ALLOWED_EXPR.match(expr):
            return None
        x = float(raw_value)
        # 仅允许安全四则运算, x 为填报值
        result = eval(expr, {"__builtins__": {}}, {"x": x, "X": x})  # noqa: S307 - 表达式已白名单校验
        return round(float(result), 2)

    # ==================================================================
    # 评估任务
    # ==================================================================
    def create_task(self, template_id: int, object_id: int, task_name: str,
                    evaluate_cycle=None, org_id=None, fill_user=None,
                    start_time=None, end_time=None) -> EvaluateTask:
        svc = self._svc()
        try:
            if svc.get_template(template_id) is None:
                raise ValueError(f"评估模板不存在: {template_id}")
            if svc.get_object(object_id) is None:
                raise ValueError(f"评估对象不存在: {object_id}")
            task = EvaluateTask(template_id=template_id, object_id=object_id, task_name=task_name.strip(),
                                evaluate_cycle=evaluate_cycle, org_id=org_id, fill_user=fill_user,
                                start_time=start_time, end_time=end_time, task_status=TaskStatus.DRAFT.value)
            return svc.add_task(task)
        finally:
            svc._op.disconnect()

    def update_task(self, task_id: int, **fields: Any) -> EvaluateTask:
        svc = self._svc()
        try:
            existing = svc.get_task(task_id)
            if existing is None:
                raise ValueError(f"评估任务不存在: {task_id}")
            for k, v in fields.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            return svc.update_task(existing)
        finally:
            svc._op.disconnect()

    def delete_task(self, task_id: int) -> bool:
        svc = self._svc()
        try:
            return svc.delete_task(task_id)
        finally:
            svc._op.disconnect()

    def get_task_detail(self, task_id: int) -> Optional[Dict[str, Any]]:
        svc = self._svc()
        try:
            task = svc.get_task(task_id)
            if task is None:
                return None
            data = task.model_dump()
            data["records"] = [r.model_dump() for r in svc.list_records(task_id)]
            snap = svc.get_snapshot_by_task(task_id)
            data["snapshot"] = snap.model_dump() if snap else None
            return data
        finally:
            svc._op.disconnect()

    def list_tasks(self, template_id=None, object_id=None, task_status=None, evaluate_cycle=None,
                   org_id=None, keyword=None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        svc = self._svc()
        try:
            offset = (max(1, page) - 1) * page_size
            items = svc.list_tasks(template_id=template_id, object_id=object_id, task_status=task_status,
                                   evaluate_cycle=evaluate_cycle, org_id=org_id, keyword=keyword,
                                   limit=page_size, offset=offset)
            total = svc.count_tasks(template_id=template_id, object_id=object_id, task_status=task_status,
                                    evaluate_cycle=evaluate_cycle, org_id=org_id, keyword=keyword)
            return {"list": items, "total": total, "page": page, "page_size": page_size}
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 指标填报
    # ==================================================================
    def submit_record(self, task_id: int, indicator_id: int, raw_value=None, score_rule_id=None,
                      fill_remark=None, attach_ids=None, auto_score: bool = True) -> TaskIndicatorRecord:
        """提交/更新单指标填报; auto_score 时依据计分规则计算 real_score。"""
        svc = self._svc()
        try:
            task = svc.get_task(task_id)
            if task is None:
                raise ValueError(f"评估任务不存在: {task_id}")
            real_score = None
            rule_id = score_rule_id
            if auto_score:
                # 规则优先级: 显式 score_rule_id > 模板内独立规则
                rels = {r.indicator_id: r for r in svc.list_template_indicators(task.template_id)}
                rel = rels.get(indicator_id)
                if rule_id is None and rel is not None:
                    rule_id = rel.template_score_rule_id
                rule = svc.get_rule(rule_id) if rule_id else None
                if raw_value is not None:
                    real_score = self.compute_score(rule, raw_value)
            rec = TaskIndicatorRecord(task_id=task_id, indicator_id=indicator_id, raw_value=raw_value,
                                      real_score=real_score, score_rule_id=rule_id, fill_remark=fill_remark,
                                      attach_ids=attach_ids or [])
            saved = svc.upsert_record(rec)
            # 首次填报时将任务推进为填报中
            if task.task_status == TaskStatus.DRAFT.value:
                task.task_status = TaskStatus.FILLING.value
                svc.update_task(task)
            return saved
        finally:
            svc._op.disconnect()

    def list_records(self, task_id: int) -> List[TaskIndicatorRecord]:
        svc = self._svc()
        try:
            return svc.list_records(task_id)
        finally:
            svc._op.disconnect()

    # ==================================================================
    # 完成评估 -> 汇总总分 + 生成快照
    # ==================================================================
    def finish_task(self, task_id: int, audit_user: Optional[int] = None,
                   evaluate_conclusion: Optional[str] = None) -> Dict[str, Any]:
        """按模板权重加权汇总总分, 更新任务为已完成并固化生成结果快照。"""
        svc = self._svc()
        try:
            task = svc.get_task(task_id)
            if task is None:
                raise ValueError(f"评估任务不存在: {task_id}")
            rels = {r.indicator_id: r for r in svc.list_template_indicators(task.template_id)}
            records = {r.indicator_id: r for r in svc.list_records(task_id)}

            total_score = 0.0
            weight_sum = 0.0
            for ind_id, rel in rels.items():
                rec = records.get(ind_id)
                if rec is None or rec.real_score is None:
                    continue
                total_score += rec.real_score * (rel.weight / 100.0)
                weight_sum += rel.weight
            total_score = round(total_score, 2)

            # 更新任务
            task.total_score = total_score
            task.task_status = TaskStatus.FINISHED.value
            task.finish_time = _now_iso()
            if audit_user is not None:
                task.audit_user = audit_user
            if evaluate_conclusion is not None:
                task.evaluate_conclusion = evaluate_conclusion
            svc.update_task(task)

            # 固化快照 (一级分类汇总得分)
            obj = svc.get_object(task.object_id)
            level_scores = self._aggregate_level_scores(rels, records)
            snap = EvaluateSnapshot(
                task_id=task_id, object_id=task.object_id, template_id=task.template_id,
                object_type=(obj.object_type if obj else 0), total_score=total_score,
                level_1_category_score=level_scores, evaluate_rank=rank_of(total_score),
            )
            svc.upsert_snapshot(snap)
            return {"task": task.model_dump(), "snapshot": snap.model_dump(), "weight_covered": round(weight_sum, 2)}
        finally:
            svc._op.disconnect()

    @staticmethod
    def _aggregate_level_scores(rels: Dict[int, TemplateIndicatorRel],
                                records: Dict[int, TaskIndicatorRecord]) -> Dict[str, Any]:
        """按指标加权得分汇总 (以 indicator_id 维度输出, 供快照对比查询)。"""
        out: Dict[str, Any] = {}
        for ind_id, rel in rels.items():
            rec = records.get(ind_id)
            if rec is None or rec.real_score is None:
                continue
            out[str(ind_id)] = {
                "weight": rel.weight,
                "real_score": rec.real_score,
                "weighted": round(rec.real_score * (rel.weight / 100.0), 2),
            }
        return out

    # ==================================================================
    # 结果快照查询
    # ==================================================================
    def get_snapshot(self, task_id: int) -> Optional[EvaluateSnapshot]:
        svc = self._svc()
        try:
            return svc.get_snapshot_by_task(task_id)
        finally:
            svc._op.disconnect()

    def list_snapshots(self, object_id=None, template_id=None, object_type=None, evaluate_rank=None,
                       page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        svc = self._svc()
        try:
            offset = (max(1, page) - 1) * page_size
            items = svc.list_snapshots(object_id=object_id, template_id=template_id, object_type=object_type,
                                       evaluate_rank=evaluate_rank, limit=page_size, offset=offset)
            return {"list": items, "page": page, "page_size": page_size}
        finally:
            svc._op.disconnect()


_manager: Optional[EvaluationManager] = None


def get_evaluation_manager() -> EvaluationManager:
    """获取评估管理业务管理器单例。"""
    global _manager
    if _manager is None:
        _manager = EvaluationManager()
    return _manager
