/* 指标管理库前端逻辑 (知识空间 · IndicatorLibrary)
 * 运行于 index.html 的 iframe 中，通过 /api/km/indicator/* 与后端交互。
 */
const { createApp, ref, reactive, computed, onMounted } = Vue;
const API = '/api/km/indicator';

// 递归分类树组件
const TreeNode = {
    name: 'tree-node',
    props: ['node', 'selectedId'],
    emits: ['select', 'add-child', 'edit', 'remove'],
    data() { return { open: true }; },
    template: `
        <div class="il-tree-node">
            <div class="il-node-row" :class="{ active: selectedId === node.category_id }" @click="$emit('select', node.category_id)">
                <span class="il-node-toggle" @click.stop="open=!open" v-if="node.children && node.children.length">{{ open ? '▼' : '▶' }}</span>
                <span class="il-node-toggle" v-else>·</span>
                <span class="il-lvl-badge">L{{ node.level }}</span>
                <span class="il-node-name" :title="node.category_code">{{ node.category_name }}</span>
                <span class="il-node-actions">
                    <span class="il-node-mini" title="新增子分类" @click.stop="$emit('add-child', node.category_id, (node.level||1)+1)">＋</span>
                    <span class="il-node-mini" title="编辑" @click.stop="$emit('edit', node, node.parent_id)">✎</span>
                    <span class="il-node-mini" title="删除" @click.stop="$emit('remove', node)">🗑</span>
                </span>
            </div>
            <div class="il-children" v-if="open && node.children && node.children.length">
                <tree-node v-for="c in node.children" :key="c.category_id" :node="c" :selected-id="selectedId"
                    @select="(id)=>$emit('select', id)"
                    @add-child="(pid,lvl)=>$emit('add-child', pid, lvl)"
                    @edit="(n,pid)=>$emit('edit', n, pid)"
                    @remove="(n)=>$emit('remove', n)"></tree-node>
            </div>
        </div>
    `
};

createApp({
    components: { TreeNode },
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

        function parseTags(s) { return (s || '').split(',').map(x => x.trim()).filter(Boolean); }
        function dataTypeName(t) { return ({ 1: '定量数值', 2: '定性打分', 3: '布尔合规', 4: '枚举选项' })[t] || '未知'; }
        function statusName(s) { return ({ 0: '停用', 1: '正常', 2: '草稿' })[s] || '未知'; }
        function attachTypeName(t) { return ({ 1: '行业标准', 2: '打分示例', 3: '评估细则' })[t] || '附件'; }

        // 分类
        const categoryTree = ref([]);
        const flatCategories = ref([]);
        const selectedCategoryId = ref(null);
        const totalAll = ref(0);

        function flatten(nodes, out) {
            for (const n of nodes) { out.push(n); if (n.children && n.children.length) flatten(n.children, out); }
        }
        async function loadCategories() {
            const d = await api(`${API}/category/tree`);
            if (d.success) {
                categoryTree.value = d.data.tree || [];
                const flat = []; flatten(categoryTree.value, flat); flatCategories.value = flat;
            }
        }
        const currentCategoryName = computed(() => {
            if (selectedCategoryId.value === null) return '全部指标';
            const c = flatCategories.value.find(x => x.category_id === selectedCategoryId.value);
            return c ? c.category_name : '指标列表';
        });

        // 指标列表
        const indicators = ref([]);
        const total = ref(0);
        const page = ref(1);
        const pageSize = ref(10);
        const keyword = ref('');
        const filterDataType = ref(null);
        const filterStatus = ref(null);
        const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

        async function reload() {
            const params = new URLSearchParams();
            params.set('page', page.value);
            params.set('page_size', pageSize.value);
            if (selectedCategoryId.value !== null) params.set('category_id', selectedCategoryId.value);
            if (filterDataType.value !== null) params.set('data_type', filterDataType.value);
            if (filterStatus.value !== null) params.set('status', filterStatus.value);
            if (keyword.value) params.set('keyword', keyword.value);
            const d = await api(`${API}/list?${params.toString()}`);
            if (d.success) { indicators.value = d.data.list || []; total.value = d.data.total || 0; }
            else toast('加载失败', d.message, 'err');
        }
        async function loadTotalAll() {
            const d = await api(`${API}/list?page=1&page_size=1`);
            if (d.success) totalAll.value = d.data.total || 0;
        }
        function selectCategory(id) { selectedCategoryId.value = id; page.value = 1; reload(); }

        // 分类弹窗
        const showCategoryModal = ref(false);
        const categoryForm = reactive({ category_id: null, category_name: '', category_code: '', parent_id: 0, level: 1, sort: 0, scene_tag: '', remark: '', status: 1 });
        function openCategoryModal(node, parentId, level) {
            if (node) {
                Object.assign(categoryForm, {
                    category_id: node.category_id, category_name: node.category_name, category_code: node.category_code,
                    parent_id: node.parent_id || 0, level: node.level || 1, sort: node.sort || 0,
                    scene_tag: (node.scene_tag || []).join(','), remark: node.remark || '', status: node.status,
                });
            } else {
                Object.assign(categoryForm, {
                    category_id: null, category_name: '', category_code: '', parent_id: parentId || 0,
                    level: level || 1, sort: 0, scene_tag: '', remark: '', status: 1,
                });
            }
            showCategoryModal.value = true;
        }
        async function submitCategory() {
            const body = {
                category_name: categoryForm.category_name.trim(),
                category_code: categoryForm.category_code.trim(),
                parent_id: categoryForm.parent_id || 0,
                level: categoryForm.level, sort: categoryForm.sort || 0,
                scene_tag: parseTags(categoryForm.scene_tag),
                remark: categoryForm.remark || null, status: categoryForm.status,
            };
            const url = categoryForm.category_id
                ? `${API}/category/update?category_id=${categoryForm.category_id}`
                : `${API}/category/create`;
            const d = await api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) { toast('保存成功', '分类已保存'); showCategoryModal.value = false; await loadCategories(); }
            else toast('保存失败', d.message, 'err');
        }
        async function deleteCategory(node) {
            if (!confirm(`确定删除分类「${node.category_name}」吗？`)) return;
            const d = await api(`${API}/category/delete?category_id=${node.category_id}`, { method: 'DELETE' });
            if (d.success) {
                toast('删除成功', '分类已删除');
                if (selectedCategoryId.value === node.category_id) selectedCategoryId.value = null;
                await loadCategories(); reload();
            } else toast('删除失败', d.message, 'err');
        }

        // 指标弹窗
        const showIndicatorModal = ref(false);
        const indicatorForm = reactive({});
        function resetIndicatorForm() {
            Object.assign(indicatorForm, {
                indicator_id: null, category_id: selectedCategoryId.value, indicator_name: '', indicator_code: '',
                indicator_desc: '', data_type: 1, unit: '', standard_value: '', min_threshold: null, max_threshold: null,
                positive_flag: 1, default_score_rule_id: null, tag_list: '', version: 1, status: 1,
            });
        }
        function openIndicatorModal(ind) {
            if (ind) {
                Object.assign(indicatorForm, {
                    indicator_id: ind.indicator_id, category_id: ind.category_id, indicator_name: ind.indicator_name,
                    indicator_code: ind.indicator_code, indicator_desc: ind.indicator_desc || '', data_type: ind.data_type,
                    unit: ind.unit || '', standard_value: ind.standard_value || '', min_threshold: ind.min_threshold,
                    max_threshold: ind.max_threshold, positive_flag: ind.positive_flag,
                    default_score_rule_id: ind.default_score_rule_id, tag_list: (ind.tag_list || []).join(','),
                    version: ind.version, status: ind.status,
                });
            } else {
                resetIndicatorForm();
                if (indicatorForm.category_id === null && flatCategories.value.length) {
                    indicatorForm.category_id = flatCategories.value[0].category_id;
                }
            }
            showIndicatorModal.value = true;
        }
        const canSubmitIndicator = computed(() =>
            !!indicatorForm.category_id && !!(indicatorForm.indicator_name || '').trim() && !!(indicatorForm.indicator_code || '').trim()
        );
        async function submitIndicator() {
            const body = {
                category_id: indicatorForm.category_id,
                indicator_name: indicatorForm.indicator_name.trim(),
                indicator_code: indicatorForm.indicator_code.trim(),
                indicator_desc: indicatorForm.indicator_desc || null,
                data_type: indicatorForm.data_type, unit: indicatorForm.unit || null,
                standard_value: indicatorForm.standard_value || null,
                min_threshold: (indicatorForm.min_threshold === '' ? null : indicatorForm.min_threshold),
                max_threshold: (indicatorForm.max_threshold === '' ? null : indicatorForm.max_threshold),
                positive_flag: indicatorForm.positive_flag,
                default_score_rule_id: (indicatorForm.default_score_rule_id === '' ? null : indicatorForm.default_score_rule_id),
                tag_list: parseTags(indicatorForm.tag_list),
                version: indicatorForm.version || 1, status: indicatorForm.status,
            };
            const url = indicatorForm.indicator_id
                ? `${API}/update?indicator_id=${indicatorForm.indicator_id}`
                : `${API}/create`;
            const d = await api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (d.success) {
                toast('保存成功', '指标已保存'); showIndicatorModal.value = false;
                await loadCategories(); await loadTotalAll(); reload();
            } else toast('保存失败', d.message, 'err');
        }
        async function deleteIndicator(ind) {
            if (!confirm(`确定删除指标「${ind.indicator_name}」及其附件吗？`)) return;
            const d = await api(`${API}/delete?indicator_id=${ind.indicator_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '指标已删除'); await loadTotalAll(); reload(); }
            else toast('删除失败', d.message, 'err');
        }

        // 详情 + 附件
        const showDetailModal = ref(false);
        const detail = ref(null);
        const attachForm = reactive({ show: false, file_name: '', file_url: '', attach_type: 1 });
        async function viewIndicator(ind) {
            const d = await api(`${API}/detail?indicator_id=${ind.indicator_id}`);
            if (d.success) { detail.value = d.data; attachForm.show = false; showDetailModal.value = true; }
            else toast('加载失败', d.message, 'err');
        }
        function openAttachForm() { Object.assign(attachForm, { show: true, file_name: '', file_url: '', attach_type: 1 }); }
        async function submitAttach() {
            const d = await api(`${API}/attach/create`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    indicator_id: detail.value.indicator_id, file_name: attachForm.file_name.trim(),
                    file_url: attachForm.file_url.trim(), attach_type: attachForm.attach_type,
                })
            });
            if (d.success) { toast('添加成功', '附件已添加'); attachForm.show = false; await viewIndicator(detail.value); }
            else toast('添加失败', d.message, 'err');
        }
        async function deleteAttach(a) {
            if (!confirm(`删除附件「${a.file_name}」？`)) return;
            const d = await api(`${API}/attach/delete?attach_id=${a.attach_id}`, { method: 'DELETE' });
            if (d.success) { toast('删除成功', '附件已删除'); await viewIndicator(detail.value); }
            else toast('删除失败', d.message, 'err');
        }

        onMounted(async () => { await loadCategories(); await loadTotalAll(); reload(); });

        return {
            toasts,
            categoryTree, flatCategories, selectedCategoryId, totalAll, currentCategoryName,
            indicators, total, page, pageSize, keyword, filterDataType, filterStatus, totalPages,
            reload, selectCategory,
            showCategoryModal, categoryForm, openCategoryModal, submitCategory, deleteCategory,
            showIndicatorModal, indicatorForm, canSubmitIndicator, openIndicatorModal, submitIndicator, deleteIndicator,
            showDetailModal, detail, attachForm, viewIndicator, openAttachForm, submitAttach, deleteAttach,
            dataTypeName, statusName, attachTypeName,
        };
    }
}).mount('#app');
