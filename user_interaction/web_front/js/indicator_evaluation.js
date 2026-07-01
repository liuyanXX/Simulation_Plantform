/* 指标评估管理前端逻辑 (结果空间 · IndicatorEvaluation)
 * 运行于 index.html 的 iframe 中，通过 /api/srlt/evaluation/* 与后端交互。
 * 指标来源于知识空间指标管理库 /api/km/indicator/*。
 */
const { createApp, ref, reactive, computed, onMounted } = Vue;
const API = '/api/srlt/evaluation';
const KM_API = '/api/km/indicator';

createApp({
    setup() {
        // Toast
        const toasts = ref([]);
        let toastId = 0;
        function toast(title, msg = '', type = 'ok') {
            const id = ++toastId;
            toasts.value.push({ id, title, msg, type });
            setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, 3000);
        }
        async function api(url, opts = {}) {
            const res = await fetch(url, opts);
            return res.json().catch(() => ({ success: false, message: 'HTTP ' + res.status }));
        }
        const pages = (total, size) => Math.max(1, Math.ceil((total || 0) / size));

        // 字典/映射
        const objectTypes = ref([]);
        function typeName(id) { const t = objectTypes.value.find(x => x.type_id === id); return t ? t.type_name : ('类型' + id); }
        function calcTypeName(t) { return ({ 1: '固定分档', 2: '线性公式', 3: '阶梯阈值', 4: '自定义表达式' })[t] || '未知'; }
        function sceneName(s) { return ({ 1: '企业绩效', 2: '软件系统', 3: '需求评审', 4: '流程效能' })[s] || '未知'; }
        function taskStatusName(s) { return ({ 0: '草稿', 1: '填报中', 2: '待审核', 3: '已完成', 4: '作废' })[s] || '未知'; }
        function taskStatusClass(s) { return ({ 0: '', 1: 'cyan', 2: 'amber', 3: 'green', 4: 'red' })[s] || ''; }
        function rankColor(r) { return ({ '优秀': '#4ade80', '良好': '#22d3ee', '合格': '#a3e635', '待改进': '#fbbf24', '不合格': '#fca5a5' })[r] || '#cbd5e1'; }

        const tab = ref('object');
        function switchTab(t) {
            tab.value = t;
            if (t === 'object') loadObjects();
            else if (t === 'rule') loadRules();
            else if (t === 'template') loadTemplates();
            else if (t === 'task') loadTasks();
            else if (t === 'snapshot') loadSnapshots();
        }

        // ===================== 评估对象 =====================
        const objects = ref([]); const objTotal = ref(0); const objPage = ref(1); const objPageSize = ref(10);
        const objKeyword = ref(''); const objTypeFilter = ref(null);
        async function loadObjects() {
            const p = new URLSearchParams({ page: objPage.value, page_size: objPageSize.value });
            if (objTypeFilter.value !== null) p.set('object_type', objTypeFilter.value);
            if (objKeyword.value) p.set('keyword', objKeyword.value);
            const d = await api(`${API}/object/list?${p}`);
            if (d.success) { objects.value = d.data.list || []; objTotal.value = d.data.total || 0; }
        }
        const showObjModal = ref(false);
        const objForm = reactive({});
        function openObjModal(o) {
            if (o) Object.assign(objForm, { object_id: o.object_id, object_type: o.object_type, object_name: o.object_name, object_code: o.object_code, org_id: o.org_id, status: o.status, ext_json_text: JSON.stringify(o.ext_json || {}) });
            else Object.assign(objForm, { object_id: null, object_type: (objectTypes.value[0] || {}).type_id || 1, object_name: '', object_code: '', org_id: null, status: 1, ext_json_text: '' });
            showObjModal.value = true;
        }
        function parseJson(text, fallback) { if (!text || !text.trim()) return fallback; try { return JSON.parse(text); } catch { toast('JSON格式错误', text, 'err'); throw new Error('bad json'); } }
        async function submitObj() {
            let ext; try { ext = parseJson(objForm.ext_json_text, {}); } catch { return; }
            const body = { object_type: objForm.object_type, object_name: objForm.object_name.trim(), object_code: objForm.object_code.trim(), org_id: objForm.org_id, ext_json: ext, status: objForm.status };
            const url = objForm.object_id ? `${API}/object/update?object_id=${objForm.object_id}` : `${API}/object/create`;
            const d = await api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) { toast('保存成功', '评估对象已保存'); showObjModal.value = false; loadObjects(); }
            else toast('保存失败', d.message, 'err');
        }
        async function deleteObj(o) {
            if (!confirm(`确定删除对象「${o.object_name}」吗？`)) return;
            const d = await api(`${API}/object/delete?object_id=${o.object_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '评估对象已删除'); loadObjects(); } else toast('删除失败', d.message, 'err');
        }

        // ===================== 计分规则 =====================
        const rules = ref([]); const ruleTypeFilter = ref(null);
        async function loadRules() {
            const p = new URLSearchParams(); if (ruleTypeFilter.value !== null) p.set('calc_type', ruleTypeFilter.value);
            const d = await api(`${API}/rule/list?${p}`);
            if (d.success) rules.value = d.data.list || [];
        }
        const showRuleModal = ref(false);
        const ruleForm = reactive({});
        function openRuleModal(r) {
            if (r) Object.assign(ruleForm, { rule_id: r.rule_id, rule_name: r.rule_name, calc_type: r.calc_type, expression: r.expression || '', remark: r.remark || '', rule_config_text: JSON.stringify(r.rule_config_json || {}) });
            else Object.assign(ruleForm, { rule_id: null, rule_name: '', calc_type: 1, expression: '', remark: '', rule_config_text: '' });
            showRuleModal.value = true;
        }
        async function submitRule() {
            let cfg; try { cfg = parseJson(ruleForm.rule_config_text, {}); } catch { return; }
            const body = { rule_name: ruleForm.rule_name.trim(), calc_type: ruleForm.calc_type, rule_config_json: cfg, expression: ruleForm.expression || null, remark: ruleForm.remark || null };
            const url = ruleForm.rule_id ? `${API}/rule/update?rule_id=${ruleForm.rule_id}` : `${API}/rule/create`;
            const d = await api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) { toast('保存成功', '计分规则已保存'); showRuleModal.value = false; loadRules(); }
            else toast('保存失败', d.message, 'err');
        }
        async function deleteRule(r) {
            if (!confirm(`确定删除规则「${r.rule_name}」吗？`)) return;
            const d = await api(`${API}/rule/delete?rule_id=${r.rule_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '计分规则已删除'); loadRules(); } else toast('删除失败', d.message, 'err');
        }

        // ===================== 评估模板 =====================
        const templates = ref([]); const tplTotal = ref(0); const tplPage = ref(1); const tplPageSize = ref(10);
        const tplKeyword = ref(''); const tplSceneFilter = ref(null);
        async function loadTemplates() {
            const p = new URLSearchParams({ page: tplPage.value, page_size: tplPageSize.value });
            if (tplSceneFilter.value !== null) p.set('scene_type', tplSceneFilter.value);
            if (tplKeyword.value) p.set('keyword', tplKeyword.value);
            const d = await api(`${API}/template/list?${p}`);
            if (d.success) { templates.value = d.data.list || []; tplTotal.value = d.data.total || 0; }
        }
        const showTplModal = ref(false);
        const tplForm = reactive({});
        function openTplModal(t) {
            if (t) Object.assign(tplForm, { template_id: t.template_id, template_name: t.template_name, template_code: t.template_code, scene_type: t.scene_type, total_score: t.total_score, is_preset: t.is_preset, status: t.status, template_desc: t.template_desc || '' });
            else Object.assign(tplForm, { template_id: null, template_name: '', template_code: '', scene_type: 1, total_score: 100, is_preset: 0, status: 1, template_desc: '' });
            showTplModal.value = true;
        }
        async function submitTpl() {
            const body = { template_name: tplForm.template_name.trim(), template_code: tplForm.template_code.trim(), scene_type: tplForm.scene_type, total_score: tplForm.total_score, is_preset: tplForm.is_preset, status: tplForm.status, template_desc: tplForm.template_desc || null };
            const url = tplForm.template_id ? `${API}/template/update?template_id=${tplForm.template_id}` : `${API}/template/create`;
            const d = await api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) { toast('保存成功', '评估模板已保存'); showTplModal.value = false; loadTemplates(); }
            else toast('保存失败', d.message, 'err');
        }
        async function deleteTpl(t) {
            if (!confirm(`确定删除模板「${t.template_name}」吗？`)) return;
            const d = await api(`${API}/template/delete?template_id=${t.template_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '评估模板已删除'); loadTemplates(); } else toast('删除失败', d.message, 'err');
        }

        // 模板指标配置
        const showTplIndModal = ref(false);
        const curTpl = ref(null);
        const tplIndRows = ref([]);
        const kmIndicators = ref([]);
        const weightSum = computed(() => Math.round(tplIndRows.value.reduce((s, r) => s + (Number(r.weight) || 0), 0) * 100) / 100);
        async function loadKmIndicators() {
            const d = await api(`${KM_API}/list?page=1&page_size=100`);
            if (d.success) kmIndicators.value = d.data.list || [];
        }
        function indName(id) { const i = kmIndicators.value.find(x => x.indicator_id === id); return i ? i.indicator_name : ('指标#' + id); }
        async function openTplIndicators(t) {
            curTpl.value = t;
            await loadKmIndicators();
            if (rules.value.length === 0) await loadRules();
            const d = await api(`${API}/template/indicators?template_id=${t.template_id}`);
            tplIndRows.value = (d.success ? d.data.list : []).map(r => ({ indicator_id: r.indicator_id, weight: r.weight, template_score_rule_id: r.template_score_rule_id, sort: r.sort, must_fill: r.must_fill }));
            showTplIndModal.value = true;
        }
        function addIndRow() { tplIndRows.value.push({ indicator_id: null, weight: 0, template_score_rule_id: null, sort: tplIndRows.value.length + 1, must_fill: 1 }); }
        async function submitTplIndicators() {
            const indicators = tplIndRows.value.filter(r => r.indicator_id).map((r, i) => ({ indicator_id: r.indicator_id, weight: Number(r.weight) || 0, template_score_rule_id: r.template_score_rule_id, sort: i + 1, must_fill: r.must_fill }));
            const d = await api(`${API}/template/set_indicators?template_id=${curTpl.value.template_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ indicators }) });
            if (d.success) { toast('保存成功', '模板指标已配置'); showTplIndModal.value = false; } else toast('保存失败', d.message, 'err');
        }

        // ===================== 评估任务 =====================
        const tasks = ref([]); const taskTotal = ref(0); const taskPage = ref(1); const taskPageSize = ref(10);
        const taskKeyword = ref(''); const taskStatusFilter = ref(null);
        const allTemplates = ref([]); const allObjects = ref([]);
        async function loadTasks() {
            const p = new URLSearchParams({ page: taskPage.value, page_size: taskPageSize.value });
            if (taskStatusFilter.value !== null) p.set('task_status', taskStatusFilter.value);
            if (taskKeyword.value) p.set('keyword', taskKeyword.value);
            const d = await api(`${API}/task/list?${p}`);
            if (d.success) { tasks.value = d.data.list || []; taskTotal.value = d.data.total || 0; }
        }
        const showTaskModal = ref(false);
        const taskForm = reactive({});
        async function openTaskModal() {
            Object.assign(taskForm, { template_id: null, object_id: null, task_name: '', evaluate_cycle: '', fill_user: null });
            const [dt, dobj] = await Promise.all([api(`${API}/template/list?page=1&page_size=100&status=1`), api(`${API}/object/list?page=1&page_size=100&status=1`)]);
            allTemplates.value = dt.success ? dt.data.list : [];
            allObjects.value = dobj.success ? dobj.data.list : [];
            showTaskModal.value = true;
        }
        async function submitTask() {
            const body = { template_id: taskForm.template_id, object_id: taskForm.object_id, task_name: taskForm.task_name.trim(), evaluate_cycle: taskForm.evaluate_cycle || null, fill_user: taskForm.fill_user };
            const d = await api(`${API}/task/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) { toast('创建成功', '评估任务已创建'); showTaskModal.value = false; loadTasks(); } else toast('创建失败', d.message, 'err');
        }
        async function deleteTask(t) {
            if (!confirm(`确定删除任务「${t.task_name}」吗？`)) return;
            const d = await api(`${API}/task/delete?task_id=${t.task_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '评估任务已删除'); loadTasks(); } else toast('删除失败', d.message, 'err');
        }
        const showTaskDetail = ref(false);
        const taskDetail = ref(null);
        async function viewTask(t) {
            const d = await api(`${API}/task/detail?task_id=${t.task_id}`);
            if (d.success) { taskDetail.value = d.data; showTaskDetail.value = true; } else toast('加载失败', d.message, 'err');
        }

        // 填报计分
        const showFillModal = ref(false);
        const curTask = ref(null);
        const fillRows = ref([]);
        const finishConclusion = ref('');
        async function openFillModal(t) {
            curTask.value = t;
            finishConclusion.value = t.evaluate_conclusion || '';
            await loadKmIndicators();
            const [dRel, dRec] = await Promise.all([api(`${API}/template/indicators?template_id=${t.template_id}`), api(`${API}/record/list?task_id=${t.task_id}`)]);
            const recMap = {};
            (dRec.success ? dRec.data.list : []).forEach(r => { recMap[r.indicator_id] = r; });
            fillRows.value = (dRel.success ? dRel.data.list : []).map(rel => {
                const rec = recMap[rel.indicator_id] || {};
                return { indicator_id: rel.indicator_id, weight: rel.weight, raw_value: rec.raw_value || '', real_score: (rec.real_score === undefined ? null : rec.real_score), fill_remark: rec.fill_remark || '' };
            });
            showFillModal.value = true;
        }
        async function doSubmitRecord(row) {
            if (!row.indicator_id) return;
            const d = await api(`${API}/record/submit`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task_id: curTask.value.task_id, indicator_id: row.indicator_id, raw_value: row.raw_value, fill_remark: row.fill_remark, auto_score: true }) });
            if (d.success) { row.real_score = d.data.real_score; } else toast('填报失败', d.message, 'err');
        }
        async function finishTask() {
            if (!confirm('确定完成评估？将按权重汇总总分并生成结果快照。')) return;
            const d = await api(`${API}/task/finish?task_id=${curTask.value.task_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ evaluate_conclusion: finishConclusion.value || null }) });
            if (d.success) { toast('评估完成', `总分 ${d.data.task.total_score} · ${d.data.snapshot.evaluate_rank}`); showFillModal.value = false; loadTasks(); }
            else toast('完成失败', d.message, 'err');
        }

        // ===================== 结果快照 =====================
        const snapshots = ref([]); const snapRankFilter = ref(null);
        async function loadSnapshots() {
            const p = new URLSearchParams({ page: 1, page_size: 50 });
            if (snapRankFilter.value !== null) p.set('evaluate_rank', snapRankFilter.value);
            const d = await api(`${API}/snapshot/list?${p}`);
            if (d.success) snapshots.value = d.data.list || [];
        }

        onMounted(async () => {
            const d = await api(`${API}/object_type/list`);
            if (d.success) objectTypes.value = d.data.list || [];
            loadObjects();
        });

        return {
            toasts, tab, switchTab, pages,
            objectTypes, typeName, calcTypeName, sceneName, taskStatusName, taskStatusClass, rankColor,
            // object
            objects, objTotal, objPage, objPageSize, objKeyword, objTypeFilter, loadObjects,
            showObjModal, objForm, openObjModal, submitObj, deleteObj,
            // rule
            rules, ruleTypeFilter, loadRules, showRuleModal, ruleForm, openRuleModal, submitRule, deleteRule,
            // template
            templates, tplTotal, tplPage, tplPageSize, tplKeyword, tplSceneFilter, loadTemplates,
            showTplModal, tplForm, openTplModal, submitTpl, deleteTpl,
            showTplIndModal, curTpl, tplIndRows, kmIndicators, weightSum, indName,
            openTplIndicators, addIndRow, submitTplIndicators,
            // task
            tasks, taskTotal, taskPage, taskPageSize, taskKeyword, taskStatusFilter, loadTasks,
            allTemplates, allObjects, showTaskModal, taskForm, openTaskModal, submitTask, deleteTask,
            showTaskDetail, taskDetail, viewTask,
            showFillModal, curTask, fillRows, finishConclusion, openFillModal, doSubmitRecord, finishTask,
            // snapshot
            snapshots, snapRankFilter, loadSnapshots,
        };
    }
}).mount('#app');
