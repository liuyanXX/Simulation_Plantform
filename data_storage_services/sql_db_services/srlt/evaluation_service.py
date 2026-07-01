"""结果空间 · 指标评估管理持久化服务 (SrltEvaluationService)

对应表:
  - srlt_object_type_dict        评估对象类型字典
  - srlt_evaluate_object         评估对象主表
  - srlt_evaluate_template       评估模板主表
  - srlt_template_indicator_rel  模板指标关联权重表
  - srlt_score_rule              指标计分规则表
  - srlt_evaluate_task           评估任务主表
  - srlt_task_indicator_record   评估指标填报明细表
  - srlt_evaluate_snapshot       评估结果快照宽表

JSON 字段 (ext_json / rule_config_json / level_1_category_score) 在 DB 中以 TEXT 存储;
attach_ids 以逗号分隔 TEXT 存储; Service 层负责序列化/反序列化。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from data_storage_services.SQLite.sqlite_operator import SQLiteOperator
from bo.srlt.evaluation import (
    EvaluateObject,
    EvaluateSnapshot,
    EvaluateTask,
    EvaluateTemplate,
    ObjectTypeDict,
    ScoreRule,
    TaskIndicatorRecord,
    TemplateIndicatorRel,
)

logger = logging.getLogger("SrltEvaluationService")


def _dump_json(obj: Any) -> str:
    if obj is None:
        return "{}"
    return json.dumps(obj, ensure_ascii=False)


def _load_json(raw: Any) -> Dict[str, Any]:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _join_ids(ids: Optional[List[str]]) -> str:
    if not ids:
        return ""
    return ",".join(str(i).strip() for i in ids if str(i).strip())


def _split_ids(raw: Any) -> List[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(i).strip() for i in raw if str(i).strip()]
    return [i.strip() for i in str(raw).split(",") if i.strip()]


class SrltEvaluationService:
    """指标评估管理持久化服务。"""

    def __init__(
        self,
        db_path: Optional[str] = None,
        db_name: Optional[str] = None,
        operator: Optional[SQLiteOperator] = None,
    ) -> None:
        if operator is not None:
            self._op = operator
        else:
            self._op = SQLiteOperator(db_path=db_path or "DB/SQLite", db_name=db_name or "simulation.db")
            self._op.connect()

    def __enter__(self) -> "SrltEvaluationService":
        return self

    def __exit__(self, *args: Any) -> None:
        self._op.disconnect()

    @property
    def cursor(self):
        return self._op.cursor

    @property
    def connection(self):
        return self._op.connection

    # ==================================================================
    # 2.2.1 评估对象类型字典
    # ==================================================================
    def list_object_types(self) -> List[ObjectTypeDict]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_object_type_dict ORDER BY type_id ASC")
        return [
            ObjectTypeDict(
                type_id=r["type_id"], type_code=r["type_code"],
                type_name=r["type_name"], remark=dict(r).get("remark"),
            )
            for r in cur.fetchall()
        ]

    # ==================================================================
    # 2.2.2 评估对象
    # ==================================================================
    def add_object(self, obj: EvaluateObject) -> EvaluateObject:
        cur = self.cursor
        cur.execute(
            "SELECT 1 FROM srlt_evaluate_object WHERE object_type = ? AND object_code = ?",
            [obj.object_type, obj.object_code],
        )
        if cur.fetchone() is not None:
            raise ValueError(f"对象编码已存在(同类型): {obj.object_code}")
        cur.execute(
            "INSERT INTO srlt_evaluate_object "
            "(object_type, object_name, object_code, org_id, ext_json, status, create_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [obj.object_type, obj.object_name, obj.object_code, obj.org_id,
             _dump_json(obj.ext_json), obj.status, obj.create_time],
        )
        self.connection.commit()
        obj.object_id = cur.lastrowid
        return obj

    def update_object(self, obj: EvaluateObject) -> EvaluateObject:
        if obj.object_id is None:
            raise ValueError("update_object 需要 object_id")
        cur = self.cursor
        cur.execute(
            "UPDATE srlt_evaluate_object SET object_type=?, object_name=?, object_code=?, "
            "org_id=?, ext_json=?, status=? WHERE object_id=?",
            [obj.object_type, obj.object_name, obj.object_code, obj.org_id,
             _dump_json(obj.ext_json), obj.status, obj.object_id],
        )
        self.connection.commit()
        return obj

    def delete_object(self, object_id: int) -> bool:
        cur = self.cursor
        cur.execute("SELECT COUNT(*) AS c FROM srlt_evaluate_task WHERE object_id=?", [object_id])
        if int(dict(cur.fetchone())["c"]) > 0:
            raise ValueError("对象已被评估任务引用, 无法删除")
        cur.execute("DELETE FROM srlt_evaluate_object WHERE object_id=?", [object_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_object(self, object_id: int) -> Optional[EvaluateObject]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_evaluate_object WHERE object_id=?", [object_id])
        row = cur.fetchone()
        return self._row_to_object(dict(row)) if row else None

    def list_objects(
        self, *, object_type: Optional[int] = None, org_id: Optional[int] = None,
        status: Optional[int] = None, keyword: Optional[str] = None,
        limit: int = 100, offset: int = 0,
    ) -> List[EvaluateObject]:
        where, params = self._object_filter(object_type, org_id, status, keyword)
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM srlt_evaluate_object {where} ORDER BY object_id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_object(dict(r)) for r in cur.fetchall()]

    def count_objects(
        self, *, object_type: Optional[int] = None, org_id: Optional[int] = None,
        status: Optional[int] = None, keyword: Optional[str] = None,
    ) -> int:
        where, params = self._object_filter(object_type, org_id, status, keyword)
        cur = self.cursor
        cur.execute(f"SELECT COUNT(*) AS c FROM srlt_evaluate_object {where}", params)
        return int(dict(cur.fetchone())["c"])

    @staticmethod
    def _object_filter(object_type, org_id, status, keyword):
        clauses, params = [], []
        if object_type is not None:
            clauses.append("object_type = ?"); params.append(object_type)
        if org_id is not None:
            clauses.append("org_id = ?"); params.append(org_id)
        if status is not None:
            clauses.append("status = ?"); params.append(status)
        if keyword:
            like = f"%{keyword}%"
            clauses.append("(object_name LIKE ? OR object_code LIKE ?)"); params.extend([like, like])
        return (("WHERE " + " AND ".join(clauses)) if clauses else ""), params

    # ==================================================================
    # 2.4 计分规则
    # ==================================================================
    def add_rule(self, rule: ScoreRule) -> ScoreRule:
        cur = self.cursor
        cur.execute(
            "INSERT INTO srlt_score_rule (rule_name, calc_type, rule_config_json, expression, remark) "
            "VALUES (?, ?, ?, ?, ?)",
            [rule.rule_name, rule.calc_type, _dump_json(rule.rule_config_json), rule.expression, rule.remark],
        )
        self.connection.commit()
        rule.rule_id = cur.lastrowid
        return rule

    def update_rule(self, rule: ScoreRule) -> ScoreRule:
        if rule.rule_id is None:
            raise ValueError("update_rule 需要 rule_id")
        cur = self.cursor
        cur.execute(
            "UPDATE srlt_score_rule SET rule_name=?, calc_type=?, rule_config_json=?, expression=?, remark=? "
            "WHERE rule_id=?",
            [rule.rule_name, rule.calc_type, _dump_json(rule.rule_config_json), rule.expression, rule.remark, rule.rule_id],
        )
        self.connection.commit()
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        cur = self.cursor
        cur.execute("DELETE FROM srlt_score_rule WHERE rule_id=?", [rule_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_rule(self, rule_id: int) -> Optional[ScoreRule]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_score_rule WHERE rule_id=?", [rule_id])
        row = cur.fetchone()
        return self._row_to_rule(dict(row)) if row else None

    def list_rules(self, *, calc_type: Optional[int] = None) -> List[ScoreRule]:
        cur = self.cursor
        if calc_type is not None:
            cur.execute("SELECT * FROM srlt_score_rule WHERE calc_type=? ORDER BY rule_id DESC", [calc_type])
        else:
            cur.execute("SELECT * FROM srlt_score_rule ORDER BY rule_id DESC")
        return [self._row_to_rule(dict(r)) for r in cur.fetchall()]

    # ==================================================================
    # 2.3 评估模板 + 指标关联
    # ==================================================================
    def add_template(self, tpl: EvaluateTemplate) -> EvaluateTemplate:
        cur = self.cursor
        cur.execute("SELECT 1 FROM srlt_evaluate_template WHERE template_code=?", [tpl.template_code])
        if cur.fetchone() is not None:
            raise ValueError(f"模板编码已存在: {tpl.template_code}")
        cur.execute(
            "INSERT INTO srlt_evaluate_template "
            "(template_name, template_code, scene_type, template_desc, total_score, is_preset, version, status, create_user, create_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tpl.template_name, tpl.template_code, tpl.scene_type, tpl.template_desc, tpl.total_score,
             tpl.is_preset, tpl.version, tpl.status, tpl.create_user, tpl.create_time],
        )
        self.connection.commit()
        tpl.template_id = cur.lastrowid
        return tpl

    def update_template(self, tpl: EvaluateTemplate) -> EvaluateTemplate:
        if tpl.template_id is None:
            raise ValueError("update_template 需要 template_id")
        cur = self.cursor
        cur.execute(
            "UPDATE srlt_evaluate_template SET template_name=?, template_code=?, scene_type=?, "
            "template_desc=?, total_score=?, is_preset=?, version=?, status=?, create_user=? "
            "WHERE template_id=?",
            [tpl.template_name, tpl.template_code, tpl.scene_type, tpl.template_desc, tpl.total_score,
             tpl.is_preset, tpl.version, tpl.status, tpl.create_user, tpl.template_id],
        )
        self.connection.commit()
        return tpl

    def delete_template(self, template_id: int) -> bool:
        cur = self.cursor
        cur.execute("SELECT COUNT(*) AS c FROM srlt_evaluate_task WHERE template_id=?", [template_id])
        if int(dict(cur.fetchone())["c"]) > 0:
            raise ValueError("模板已被评估任务引用, 无法删除")
        cur.execute("DELETE FROM srlt_template_indicator_rel WHERE template_id=?", [template_id])
        cur.execute("DELETE FROM srlt_evaluate_template WHERE template_id=?", [template_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_template(self, template_id: int) -> Optional[EvaluateTemplate]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_evaluate_template WHERE template_id=?", [template_id])
        row = cur.fetchone()
        return self._row_to_template(dict(row)) if row else None

    def list_templates(
        self, *, scene_type: Optional[int] = None, is_preset: Optional[int] = None,
        status: Optional[int] = None, keyword: Optional[str] = None,
        limit: int = 100, offset: int = 0,
    ) -> List[EvaluateTemplate]:
        where, params = self._template_filter(scene_type, is_preset, status, keyword)
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM srlt_evaluate_template {where} ORDER BY template_id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_template(dict(r)) for r in cur.fetchall()]

    def count_templates(
        self, *, scene_type: Optional[int] = None, is_preset: Optional[int] = None,
        status: Optional[int] = None, keyword: Optional[str] = None,
    ) -> int:
        where, params = self._template_filter(scene_type, is_preset, status, keyword)
        cur = self.cursor
        cur.execute(f"SELECT COUNT(*) AS c FROM srlt_evaluate_template {where}", params)
        return int(dict(cur.fetchone())["c"])

    @staticmethod
    def _template_filter(scene_type, is_preset, status, keyword):
        clauses, params = [], []
        if scene_type is not None:
            clauses.append("scene_type = ?"); params.append(scene_type)
        if is_preset is not None:
            clauses.append("is_preset = ?"); params.append(is_preset)
        if status is not None:
            clauses.append("status = ?"); params.append(status)
        if keyword:
            like = f"%{keyword}%"
            clauses.append("(template_name LIKE ? OR template_code LIKE ?)"); params.extend([like, like])
        return (("WHERE " + " AND ".join(clauses)) if clauses else ""), params

    # ----- 模板指标关联 -----
    def set_template_indicators(self, template_id: int, rels: List[TemplateIndicatorRel]) -> List[TemplateIndicatorRel]:
        """全量重置模板指标关联。"""
        cur = self.cursor
        cur.execute("DELETE FROM srlt_template_indicator_rel WHERE template_id=?", [template_id])
        out: List[TemplateIndicatorRel] = []
        for rel in rels:
            rel.template_id = template_id
            cur.execute(
                "INSERT INTO srlt_template_indicator_rel "
                "(template_id, indicator_id, weight, template_score_rule_id, sort, must_fill) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [rel.template_id, rel.indicator_id, rel.weight, rel.template_score_rule_id, rel.sort, rel.must_fill],
            )
            rel.rel_id = cur.lastrowid
            out.append(rel)
        self.connection.commit()
        return out

    def list_template_indicators(self, template_id: int) -> List[TemplateIndicatorRel]:
        cur = self.cursor
        cur.execute(
            "SELECT * FROM srlt_template_indicator_rel WHERE template_id=? ORDER BY sort ASC, rel_id ASC",
            [template_id],
        )
        return [self._row_to_rel(dict(r)) for r in cur.fetchall()]

    # ==================================================================
    # 2.5.1 评估任务
    # ==================================================================
    def add_task(self, task: EvaluateTask) -> EvaluateTask:
        cur = self.cursor
        cur.execute(
            "INSERT INTO srlt_evaluate_task "
            "(template_id, object_id, task_name, evaluate_cycle, start_time, end_time, task_status, "
            "total_score, evaluate_conclusion, fill_user, audit_user, org_id, create_time, finish_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [task.template_id, task.object_id, task.task_name, task.evaluate_cycle, task.start_time,
             task.end_time, task.task_status, task.total_score, task.evaluate_conclusion, task.fill_user,
             task.audit_user, task.org_id, task.create_time, task.finish_time],
        )
        self.connection.commit()
        task.task_id = cur.lastrowid
        return task

    def update_task(self, task: EvaluateTask) -> EvaluateTask:
        if task.task_id is None:
            raise ValueError("update_task 需要 task_id")
        cur = self.cursor
        cur.execute(
            "UPDATE srlt_evaluate_task SET template_id=?, object_id=?, task_name=?, evaluate_cycle=?, "
            "start_time=?, end_time=?, task_status=?, total_score=?, evaluate_conclusion=?, fill_user=?, "
            "audit_user=?, org_id=?, finish_time=? WHERE task_id=?",
            [task.template_id, task.object_id, task.task_name, task.evaluate_cycle, task.start_time,
             task.end_time, task.task_status, task.total_score, task.evaluate_conclusion, task.fill_user,
             task.audit_user, task.org_id, task.finish_time, task.task_id],
        )
        self.connection.commit()
        return task

    def delete_task(self, task_id: int) -> bool:
        cur = self.cursor
        cur.execute("DELETE FROM srlt_task_indicator_record WHERE task_id=?", [task_id])
        cur.execute("DELETE FROM srlt_evaluate_snapshot WHERE task_id=?", [task_id])
        cur.execute("DELETE FROM srlt_evaluate_task WHERE task_id=?", [task_id])
        self.connection.commit()
        return cur.rowcount > 0

    def get_task(self, task_id: int) -> Optional[EvaluateTask]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_evaluate_task WHERE task_id=?", [task_id])
        row = cur.fetchone()
        return self._row_to_task(dict(row)) if row else None

    def list_tasks(
        self, *, template_id: Optional[int] = None, object_id: Optional[int] = None,
        task_status: Optional[int] = None, evaluate_cycle: Optional[str] = None,
        org_id: Optional[int] = None, keyword: Optional[str] = None,
        limit: int = 100, offset: int = 0,
    ) -> List[EvaluateTask]:
        where, params = self._task_filter(template_id, object_id, task_status, evaluate_cycle, org_id, keyword)
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM srlt_evaluate_task {where} ORDER BY task_id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_task(dict(r)) for r in cur.fetchall()]

    def count_tasks(
        self, *, template_id: Optional[int] = None, object_id: Optional[int] = None,
        task_status: Optional[int] = None, evaluate_cycle: Optional[str] = None,
        org_id: Optional[int] = None, keyword: Optional[str] = None,
    ) -> int:
        where, params = self._task_filter(template_id, object_id, task_status, evaluate_cycle, org_id, keyword)
        cur = self.cursor
        cur.execute(f"SELECT COUNT(*) AS c FROM srlt_evaluate_task {where}", params)
        return int(dict(cur.fetchone())["c"])

    @staticmethod
    def _task_filter(template_id, object_id, task_status, evaluate_cycle, org_id, keyword):
        clauses, params = [], []
        if template_id is not None:
            clauses.append("template_id = ?"); params.append(template_id)
        if object_id is not None:
            clauses.append("object_id = ?"); params.append(object_id)
        if task_status is not None:
            clauses.append("task_status = ?"); params.append(task_status)
        if evaluate_cycle:
            clauses.append("evaluate_cycle = ?"); params.append(evaluate_cycle)
        if org_id is not None:
            clauses.append("org_id = ?"); params.append(org_id)
        if keyword:
            clauses.append("task_name LIKE ?"); params.append(f"%{keyword}%")
        return (("WHERE " + " AND ".join(clauses)) if clauses else ""), params

    # ==================================================================
    # 2.5.2 指标填报明细
    # ==================================================================
    def upsert_record(self, rec: TaskIndicatorRecord) -> TaskIndicatorRecord:
        """按 (task_id, indicator_id) 维度插入或更新填报明细。"""
        cur = self.cursor
        cur.execute(
            "SELECT record_id FROM srlt_task_indicator_record WHERE task_id=? AND indicator_id=?",
            [rec.task_id, rec.indicator_id],
        )
        existing = cur.fetchone()
        if existing:
            rec.record_id = dict(existing)["record_id"]
            cur.execute(
                "UPDATE srlt_task_indicator_record SET raw_value=?, real_score=?, score_rule_id=?, "
                "fill_remark=?, attach_ids=? WHERE record_id=?",
                [rec.raw_value, rec.real_score, rec.score_rule_id, rec.fill_remark,
                 _join_ids(rec.attach_ids), rec.record_id],
            )
        else:
            cur.execute(
                "INSERT INTO srlt_task_indicator_record "
                "(task_id, indicator_id, raw_value, real_score, score_rule_id, fill_remark, attach_ids, create_time) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [rec.task_id, rec.indicator_id, rec.raw_value, rec.real_score, rec.score_rule_id,
                 rec.fill_remark, _join_ids(rec.attach_ids), rec.create_time],
            )
            rec.record_id = cur.lastrowid
        self.connection.commit()
        return rec

    def list_records(self, task_id: int) -> List[TaskIndicatorRecord]:
        cur = self.cursor
        cur.execute(
            "SELECT * FROM srlt_task_indicator_record WHERE task_id=? ORDER BY record_id ASC",
            [task_id],
        )
        return [self._row_to_record(dict(r)) for r in cur.fetchall()]

    def delete_record(self, record_id: int) -> bool:
        cur = self.cursor
        cur.execute("DELETE FROM srlt_task_indicator_record WHERE record_id=?", [record_id])
        self.connection.commit()
        return cur.rowcount > 0

    # ==================================================================
    # 2.6 评估结果快照
    # ==================================================================
    def upsert_snapshot(self, snap: EvaluateSnapshot) -> EvaluateSnapshot:
        """按 task_id 一对一插入或更新快照。"""
        cur = self.cursor
        cur.execute("SELECT snapshot_id FROM srlt_evaluate_snapshot WHERE task_id=?", [snap.task_id])
        existing = cur.fetchone()
        if existing:
            snap.snapshot_id = dict(existing)["snapshot_id"]
            cur.execute(
                "UPDATE srlt_evaluate_snapshot SET object_id=?, template_id=?, object_type=?, total_score=?, "
                "level_1_category_score=?, evaluate_rank=?, snapshot_time=? WHERE snapshot_id=?",
                [snap.object_id, snap.template_id, snap.object_type, snap.total_score,
                 _dump_json(snap.level_1_category_score), snap.evaluate_rank, snap.snapshot_time, snap.snapshot_id],
            )
        else:
            cur.execute(
                "INSERT INTO srlt_evaluate_snapshot "
                "(task_id, object_id, template_id, object_type, total_score, level_1_category_score, evaluate_rank, snapshot_time) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [snap.task_id, snap.object_id, snap.template_id, snap.object_type, snap.total_score,
                 _dump_json(snap.level_1_category_score), snap.evaluate_rank, snap.snapshot_time],
            )
            snap.snapshot_id = cur.lastrowid
        self.connection.commit()
        return snap

    def get_snapshot_by_task(self, task_id: int) -> Optional[EvaluateSnapshot]:
        cur = self.cursor
        cur.execute("SELECT * FROM srlt_evaluate_snapshot WHERE task_id=?", [task_id])
        row = cur.fetchone()
        return self._row_to_snapshot(dict(row)) if row else None

    def list_snapshots(
        self, *, object_id: Optional[int] = None, template_id: Optional[int] = None,
        object_type: Optional[int] = None, evaluate_rank: Optional[str] = None,
        limit: int = 100, offset: int = 0,
    ) -> List[EvaluateSnapshot]:
        clauses, params = [], []
        if object_id is not None:
            clauses.append("object_id = ?"); params.append(object_id)
        if template_id is not None:
            clauses.append("template_id = ?"); params.append(template_id)
        if object_type is not None:
            clauses.append("object_type = ?"); params.append(object_type)
        if evaluate_rank:
            clauses.append("evaluate_rank = ?"); params.append(evaluate_rank)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        cur = self.cursor
        cur.execute(
            f"SELECT * FROM srlt_evaluate_snapshot {where} ORDER BY snapshot_time DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [self._row_to_snapshot(dict(r)) for r in cur.fetchall()]

    # ==================================================================
    # 行 -> 业务对象
    # ==================================================================
    def _row_to_object(self, r: Dict[str, Any]) -> EvaluateObject:
        return EvaluateObject(
            object_id=r["object_id"], object_type=int(r["object_type"]), object_name=r["object_name"],
            object_code=r["object_code"], org_id=r.get("org_id"), ext_json=_load_json(r.get("ext_json")),
            status=int(r.get("status") if r.get("status") is not None else 1), create_time=r["create_time"],
        )

    def _row_to_rule(self, r: Dict[str, Any]) -> ScoreRule:
        return ScoreRule(
            rule_id=r["rule_id"], rule_name=r["rule_name"], calc_type=int(r.get("calc_type") or 1),
            rule_config_json=_load_json(r.get("rule_config_json")), expression=r.get("expression"), remark=r.get("remark"),
        )

    def _row_to_template(self, r: Dict[str, Any]) -> EvaluateTemplate:
        return EvaluateTemplate(
            template_id=r["template_id"], template_name=r["template_name"], template_code=r["template_code"],
            scene_type=int(r.get("scene_type") or 1), template_desc=r.get("template_desc"),
            total_score=int(r.get("total_score") or 100), is_preset=int(r.get("is_preset") or 0),
            version=int(r.get("version") or 1), status=int(r.get("status") if r.get("status") is not None else 1),
            create_user=r.get("create_user"), create_time=r["create_time"],
        )

    def _row_to_rel(self, r: Dict[str, Any]) -> TemplateIndicatorRel:
        return TemplateIndicatorRel(
            rel_id=r["rel_id"], template_id=int(r["template_id"]), indicator_id=int(r["indicator_id"]),
            weight=float(r.get("weight") or 0), template_score_rule_id=r.get("template_score_rule_id"),
            sort=int(r.get("sort") or 0), must_fill=int(r.get("must_fill") if r.get("must_fill") is not None else 1),
        )

    def _row_to_task(self, r: Dict[str, Any]) -> EvaluateTask:
        return EvaluateTask(
            task_id=r["task_id"], template_id=int(r["template_id"]), object_id=int(r["object_id"]),
            task_name=r["task_name"], evaluate_cycle=r.get("evaluate_cycle"), start_time=r.get("start_time"),
            end_time=r.get("end_time"), task_status=int(r.get("task_status") or 0), total_score=r.get("total_score"),
            evaluate_conclusion=r.get("evaluate_conclusion"), fill_user=r.get("fill_user"), audit_user=r.get("audit_user"),
            org_id=r.get("org_id"), create_time=r["create_time"], finish_time=r.get("finish_time"),
        )

    def _row_to_record(self, r: Dict[str, Any]) -> TaskIndicatorRecord:
        return TaskIndicatorRecord(
            record_id=r["record_id"], task_id=int(r["task_id"]), indicator_id=int(r["indicator_id"]),
            raw_value=r.get("raw_value"), real_score=r.get("real_score"), score_rule_id=r.get("score_rule_id"),
            fill_remark=r.get("fill_remark"), attach_ids=_split_ids(r.get("attach_ids")), create_time=r["create_time"],
        )

    def _row_to_snapshot(self, r: Dict[str, Any]) -> EvaluateSnapshot:
        return EvaluateSnapshot(
            snapshot_id=r["snapshot_id"], task_id=int(r["task_id"]), object_id=int(r["object_id"]),
            template_id=int(r["template_id"]), object_type=int(r["object_type"]), total_score=r.get("total_score"),
            level_1_category_score=_load_json(r.get("level_1_category_score")), evaluate_rank=r.get("evaluate_rank"),
            snapshot_time=r["snapshot_time"],
        )
