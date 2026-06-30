# -*- coding: utf-8 -*-
"""方案元空间路由模块

提供方案元空间方案的列表、创建、详情、删除等API接口。
支持文件按方案ID分目录存储（主文档/附件文档/参考文档）。
"""
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from bo.smeta.solution import (
    Solution,
    SolutionBaseInfo,
    SolutionKeyInfo,
    SolutionDocInfo,
    SolutionStatus,
    new_solution,
)
from data_storage_services.sql_db_services.smeta.solution_service import SmetaSolutionService


router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SOLUTIONS_DIR = os.path.join(BASE_DIR, "Files", "Solutions")


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _save_file(file: UploadFile, dest_dir: str, file_id: str) -> dict:
    _ensure_dir(dest_dir)
    original_name = file.filename or "unknown"
    ext = os.path.splitext(original_name)[1]
    saved_name = f"{file_id}{ext}"
    saved_path = os.path.join(dest_dir, saved_name)
    
    content = file.file.read()
    with open(saved_path, "wb") as f:
        f.write(content)
    
    return {
        "file_id": file_id,
        "file_name": original_name,
        "saved_name": saved_name,
        "saved_path": saved_path,
        "size": len(content),
    }


def _ok(data=None, message="ok"):
    return JSONResponse({"success": True, "message": message, "data": data})


def _err(message, code=400):
    return JSONResponse({"success": False, "message": message, "data": None}, status_code=code)


@router.get("/list")
async def list_solutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    status: Optional[str] = Query(None),
):
    """获取方案列表（分页）"""
    try:
        svc = SmetaSolutionService()
        offset = (page - 1) * page_size
        
        solutions = svc.list_all(
            limit=page_size,
            offset=offset,
            status=status or None,
        )
        total = svc.count(
            status=status or None,
        )
        
        result_list = []
        for sol in solutions:
            if keyword and keyword.lower() not in sol.base.solution_name.lower():
                if sol.base.summary and keyword.lower() not in sol.base.summary.lower():
                    continue
            flat = sol.to_flat_dict(include_revisions=False)
            result_list.append({
                "id": flat.get("id", ""),
                "solution_name": flat.get("solution_name", ""),
                "major_version": flat.get("major_version", 1),
                "minor_version": flat.get("minor_version", 0),
                "version_label": sol.version_label,
                "status": flat.get("status", ""),
                "category": flat.get("category", ""),
                "summary": flat.get("summary", ""),
                "main_docs_count": len(flat.get("doc_main_docs", []) or []),
                "attachments_count": len(flat.get("doc_attachments", []) or []),
                "references_count": len(flat.get("doc_references", []) or []),
                "created_at": flat.get("created_at", ""),
                "updated_at": flat.get("updated_at", ""),
            })
        
        if keyword:
            filtered = [s for s in result_list if keyword.lower() in s["solution_name"].lower() or (s["summary"] and keyword.lower() in s["summary"].lower())]
            result_list = filtered
            total = len(filtered)
        
        svc._op.disconnect()
        return _ok({
            "list": result_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        return _err(f"查询方案列表失败: {e}")


@router.get("/detail")
async def get_solution_detail(solution_id: str = Query(...)):
    """获取方案详情"""
    try:
        svc = SmetaSolutionService()
        solution = svc.get_by_id(solution_id)
        svc._op.disconnect()
        
        if not solution:
            return _err("方案不存在", 404)
        
        flat = solution.to_flat_dict()
        # 补充前端展示所需的派生字段
        flat["version_label"] = solution.version_label
        flat["main_docs_count"] = len(flat.get("doc_main_docs", []) or [])
        flat["attachments_count"] = len(flat.get("doc_attachments", []) or [])
        flat["references_count"] = len(flat.get("doc_references", []) or [])

        # 组装文档列表（含文件名与下载所需的 file_id），供前端展示与下载
        def _build_docs(file_ids, category):
            sub = {"main": "main_docs", "att": "attachments", "ref": "references"}[category]
            doc_dir = os.path.join(SOLUTIONS_DIR, solution_id, sub)
            items = []
            for fid in (file_ids or []):
                file_name = fid
                if os.path.isdir(doc_dir):
                    for fn in os.listdir(doc_dir):
                        if os.path.splitext(fn)[0] == fid:
                            file_name = fn
                            break
                items.append({"file_id": fid, "file_name": file_name})
            return items

        flat["main_docs_list"] = _build_docs(flat.get("doc_main_docs", []), "main")
        flat["attachments_list"] = _build_docs(flat.get("doc_attachments", []), "att")
        flat["references_list"] = _build_docs(flat.get("doc_references", []), "ref")
        return _ok(flat)
    except Exception as e:
        return _err(f"查询方案详情失败: {e}")


@router.get("/download")
async def download_solution_doc(file_id: str = Query(...)):
    """下载方案文档。

    file_id 形如 {solution_id}_{main|att|ref}_{idx}，
    文件按 Files/Solutions/{solution_id}/{main_docs|attachments|references}/{file_id}{ext} 存储。
    """
    from fastapi.responses import FileResponse
    from urllib.parse import quote
    try:
        # 解析 file_id 中的方案ID与类别
        if "_main_" in file_id:
            solution_id, sub = file_id.split("_main_")[0], "main_docs"
        elif "_att_" in file_id:
            solution_id, sub = file_id.split("_att_")[0], "attachments"
        elif "_ref_" in file_id:
            solution_id, sub = file_id.split("_ref_")[0], "references"
        else:
            return _err("非法的文件标识", 400)

        doc_dir = os.path.join(SOLUTIONS_DIR, solution_id, sub)
        if not os.path.isdir(doc_dir):
            return _err("文件不存在", 404)

        target = None
        for fn in os.listdir(doc_dir):
            if os.path.splitext(fn)[0] == file_id:
                target = os.path.join(doc_dir, fn)
                break
        if not target or not os.path.isfile(target):
            return _err("文件不存在", 404)

        filename = os.path.basename(target)
        return FileResponse(
            target,
            media_type="application/octet-stream",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
            },
        )
    except Exception as e:
        return _err(f"下载文档失败: {e}")


@router.post("/create")
async def create_solution(
    solution_name: str = Form(...),
    major_version: int = Form(1),
    minor_version: int = Form(0),
    status: str = Form("草稿"),
    category: str = Form(""),
    summary: str = Form(""),
    purpose: str = Form("[]"),
    objectives: str = Form("[]"),
    measures: str = Form("[]"),
    organizations: str = Form("[]"),
    personnel: str = Form("[]"),
    work_mechanism: str = Form(""),
    work_content: str = Form(""),
    constraints: str = Form("[]"),
    risk_list: str = Form("[]"),
    issue_list: str = Form("[]"),
    notes: str = Form(""),
    main_docs: List[UploadFile] = File(None),
    attachments: List[UploadFile] = File(None),
    references: List[UploadFile] = File(None),
):
    """创建新方案（支持文件上传）"""
    try:
        solution_id = uuid.uuid4().hex
        
        solution = new_solution(
            solution_name=solution_name.strip(),
            modifier="system",
            summary=summary or None,
            category=category or None,
        )
        solution.base.id = solution_id
        solution.base.major_version = major_version
        solution.base.minor_version = minor_version
        solution.base.status = status
        
        purpose_list = json.loads(purpose) if purpose else []
        objectives_list = json.loads(objectives) if objectives else []
        measures_list = json.loads(measures) if measures else []
        organizations_list = json.loads(organizations) if organizations else []
        personnel_list = json.loads(personnel) if personnel else []
        constraints_list = json.loads(constraints) if constraints else []
        risk_list_val = json.loads(risk_list) if risk_list else []
        issue_list_val = json.loads(issue_list) if issue_list else []
        
        solution.key = SolutionKeyInfo(
            purpose=purpose_list,
            objectives=objectives_list,
            measures=measures_list,
            organizations=organizations_list,
            personnel=personnel_list,
            work_mechanism=work_mechanism or None,
            work_content=work_content or None,
            constraints=constraints_list,
            risk_list=risk_list_val,
            issue_list=issue_list_val,
            notes=notes or None,
        )
        
        solution_dir = os.path.join(SOLUTIONS_DIR, solution_id)
        main_dir = os.path.join(solution_dir, "main_docs")
        att_dir = os.path.join(solution_dir, "attachments")
        ref_dir = os.path.join(solution_dir, "references")
        
        main_doc_ids = []
        if main_docs:
            for idx, f in enumerate(main_docs):
                file_id = f"{solution_id}_main_{idx}"
                info = _save_file(f, main_dir, file_id)
                main_doc_ids.append(info["file_id"])
        
        attachment_ids = []
        if attachments:
            for idx, f in enumerate(attachments):
                file_id = f"{solution_id}_att_{idx}"
                info = _save_file(f, att_dir, file_id)
                attachment_ids.append(info["file_id"])
        
        reference_ids = []
        if references:
            for idx, f in enumerate(references):
                file_id = f"{solution_id}_ref_{idx}"
                info = _save_file(f, ref_dir, file_id)
                reference_ids.append(info["file_id"])
        
        solution.doc = SolutionDocInfo(
            main_docs=main_doc_ids,
            attachments=attachment_ids,
            references=reference_ids,
        )
        
        svc = SmetaSolutionService()
        svc.add(solution)
        svc._op.disconnect()
        
        return _ok({
            "solution_id": solution_id,
            "solution_name": solution_name,
            "main_docs_count": len(main_doc_ids),
            "attachments_count": len(attachment_ids),
            "references_count": len(reference_ids),
        })
    except Exception as e:
        return _err(f"创建方案失败: {e}")


@router.delete("/delete")
async def delete_solution(solution_id: str = Query(...)):
    """删除方案"""
    try:
        svc = SmetaSolutionService()
        existing = svc.get_by_id(solution_id)
        if not existing:
            svc._op.disconnect()
            return _err("方案不存在", 404)
        
        svc.delete(solution_id)
        svc._op.disconnect()
        
        solution_dir = os.path.join(SOLUTIONS_DIR, solution_id)
        if os.path.exists(solution_dir):
            import shutil
            shutil.rmtree(solution_dir, ignore_errors=True)
        
        return _ok({"solution_id": solution_id})
    except Exception as e:
        return _err(f"删除方案失败: {e}")


@router.post("/batch_delete")
async def batch_delete_solutions(
    solution_ids: List[str] = [],
):
    """批量删除方案"""
    try:
        if not solution_ids:
            return _err("请选择要删除的方案")
        
        svc = SmetaSolutionService()
        deleted_count = 0
        
        for sid in solution_ids:
            existing = svc.get_by_id(sid)
            if existing:
                svc.delete(sid)
                deleted_count += 1
                
                solution_dir = os.path.join(SOLUTIONS_DIR, sid)
                if os.path.exists(solution_dir):
                    import shutil
                    shutil.rmtree(solution_dir, ignore_errors=True)
        
        svc._op.disconnect()
        return _ok({"deleted_count": deleted_count})
    except Exception as e:
        return _err(f"批量删除方案失败: {e}")
