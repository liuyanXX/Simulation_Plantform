const { createApp, ref, computed, reactive, onMounted, watch, nextTick } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
    splitTags, formatDateTime, showToast, removeToast, toasts, apiFetch
} = C;

const INDEX_TYPE_OPTIONS = [
    { value: 'completeness', label: '完整性' },
    { value: 'rationality',   label: '合理性' },
    { value: 'feasibility',   label: '可行性' },
    { value: 'risk',         label: '风险评估' },
    { value: 'efficiency',   label: '效率评估' },
    { value: 'compliance',   label: '合规性' },
    { value: 'strategy',     label: '战略性' },
    { value: 'resource',      label: '资源' },
    { value: 'benefit',      label: '效益' },
    { value: 'other',        label: '其他' },
];

const INDEX_LEVEL_OPTIONS = [
    { value: 'level_1', label: '一级指标' },
    { value: 'level_2', label: '二级指标' },
    { value: 'level_3', label: '三级指标' },
    { value: 'level_4', label: '四级指标' },
];

const PRIORITY_OPTIONS = [
    { value: 'high',   label: '高' },
    { value: 'medium', label: '中' },
    { value: 'low',    label: '低' },
];

const TASK_TYPE_OPTIONS = [
    { value: 'normal',      label: '常规任务' },
    { value: 'preparation', label: '准备任务' },
    { value: 'execution',   label: '执行任务' },
    { value: 'review',      label: '复核任务' },
];

const SIMULATION_TYPE_OPTIONS = [
    { value: 'normal',            label: '常规仿真' },
    { value: 'mission_rehearsal', label: '任务推演' },
    { value: 'combat',            label: '作战仿真' },
    { value: 'training',          label: '训练仿真' },
];

createApp({
    setup() {
        const knowledgeBases = ref([
            { id: 'decomposition', name: '方案拆解库',   description: '方案拆解任务相关的知识条目（Knowledge 对象）',                 object_type: 'Knowledge' },
            { id: 'simulation',    name: '仿真知识库',   description: '仿真相关的知识条目（Knowledge 对象）',                        object_type: 'Knowledge' },
            { id: 'other',          name: '其他知识库',   description: '其他类型的知识条目（Knowledge 对象）',                        object_type: 'Knowledge' },
        ]);

        const selectedKnowledgeBase = ref('decomposition');
        const isEvaluation = computed(() => false);

        const keyword = ref('');
        const isSearching = ref(false);

        const knowledgeItems = ref([]);
        const knowledgeTotal = ref(0);
        const knowledgePage = ref(1);
        const knowledgePageSize = ref(10);
        const selectedKnowledgeIds = ref([]);

        const showKnowledgeDetail = ref(false);
        const showEditModal = ref(false);
        const showKnowledgeUploadModal = ref(false);
        const currentKnowledge = ref({});

        const uploading = ref(false);
        const uploadTagsInput = ref('');
        const editTagsInput = ref('');

        const uploadForm = reactive({
            knowledge_base: 'decomposition',
            index_id: '', name: '', description: '',
            evaluation_method: '', index_type: 'completeness',
            index_level: 'level_1', parent_id: '', weight: 1.0,
            score_min: 0, score_max: 100, agent_ids_input: '',
            task_id: '', task_name: '',
            content: '', execute_role: '',
            expected_start_time: '', expected_end_time: '',
            resource_consumption: 0, priority: 'medium',
            output_target_role: '', task_type: 'normal',
            knowledge_id: '', title: '', summary: '',
            simulation_type: 'normal',
            tags: []
        });

        const editForm = reactive({
            _isIndex: false,
            index_id: '', name: '', description: '',
            evaluation_method: '', index_type: '',
            index_level: '', parent_id: '', weight: 1.0,
            score_min: 0, score_max: 100, agent_ids_input: '',
            knowledge_id: '', title: '', summary: '',
            content: '', tags: [], category: ''
        });

        const currentBaseName = computed(() => {
            const kb = (knowledgeBases.value || []).find(b => b.id === selectedKnowledgeBase.value);
            return kb ? kb.name : '知识管理';
        });

        const currentObjectType = computed(() => {
            const kb = (knowledgeBases.value || []).find(b => b.id === selectedKnowledgeBase.value);
            return kb ? kb.object_type : 'Knowledge';
        });

        const pagedKnowledge = computed(() => {
            const all = knowledgeItems.value || [];
            const ps = knowledgePageSize.value || 10;
            const p = knowledgePage.value || 1;
            const start = (p - 1) * ps;
            return all.slice(start, start + ps);
        });

        const knowledgeTotalPages = computed(() => {
            const ps = knowledgePageSize.value || 10;
            const total = knowledgeTotal.value || 0;
            if (total <= 0) return 1;
            return Math.max(1, Math.ceil(total / ps));
        });

        const knowledgeCurrentPage = computed({
            get: () => knowledgePage.value,
            set: (v) => {
                const n = Number(v);
                if (Number.isFinite(n) && n >= 1) knowledgePage.value = n;
            }
        });

        const isPageAllSelected = computed(() => {
            const keyField = isEvaluation.value ? 'index_id' : 'knowledge_id';
            const pageIds = (pagedKnowledge.value || []).map(k => k[keyField]);
            if (!pageIds.length) return false;
            return pageIds.every(id => selectedKnowledgeIds.value.includes(id));
        });

        const canUploadKnowledge = computed(() => {
            const base = uploadForm.knowledge_base;
            if (!base) return false;
            if (base === 'decomposition') {
                return !!(uploadForm.task_id && uploadForm.task_name && uploadForm.content
                          && uploadForm.execute_role && uploadForm.expected_start_time && uploadForm.expected_end_time);
            }
            return !!(uploadForm.knowledge_id && uploadForm.title && uploadForm.summary && uploadForm.content);
        });

        const canSaveEdit = computed(() => {
            return !!(editForm.knowledge_id && editForm.title && editForm.summary && editForm.content);
        });

        function resetUploadForm() {
            Object.assign(uploadForm, {
                knowledge_base: selectedKnowledgeBase.value || 'decomposition',
                index_id: '', name: '', description: '',
                evaluation_method: '', index_type: 'completeness',
                index_level: 'level_1', parent_id: '', weight: 1.0,
                score_min: 0, score_max: 100, agent_ids_input: '',
                task_id: '', task_name: '',
                content: '', execute_role: '',
                expected_start_time: '', expected_end_time: '',
                resource_consumption: 0, priority: 'medium',
                output_target_role: '', task_type: 'normal',
                knowledge_id: '', title: '', summary: '',
                simulation_type: 'normal',
                tags: []
            });
            uploadTagsInput.value = '';
        }

        function resetEditForm() {
            Object.assign(editForm, {
                _isIndex: false,
                index_id: '', name: '', description: '',
                evaluation_method: '', index_type: '',
                index_level: '', parent_id: '', weight: 1.0,
                score_min: 0, score_max: 100, agent_ids_input: '',
                knowledge_id: '', title: '', summary: '',
                content: '', tags: [], category: selectedKnowledgeBase.value || 'decomposition'
            });
            editTagsInput.value = '';
        }

        function parseTags(input) {
            if (!input) return [];
            return String(input).split(/[,，\s]+/).map(s => s.trim()).filter(Boolean);
        }

        function joinTags(arr) {
            if (!Array.isArray(arr)) return '';
            return arr.join(', ');
        }

        function buildListUrl({ isSearch = false } = {}) {
            const ps = knowledgePageSize.value || 10;
            const p = knowledgePage.value || 1;
            const base = selectedKnowledgeBase.value || 'decomposition';
            let url;
            if (isSearch) {
                const kw = encodeURIComponent(keyword.value || '');
                url = `/api/knowledge/search?keyword=${kw}&category=${encodeURIComponent(base)}&page=${p}&pageSize=${ps}`;
            } else {
                url = `/api/knowledge/list?category=${encodeURIComponent(base)}&page=${p}&pageSize=${ps}`;
            }
            return url;
        }

        async function loadKnowledgeList(opts) {
            const { isSearch = false } = opts || {};
            try {
                const url = buildListUrl({ isSearch });
                const data = await apiFetch(url);
                if (data && data.success && data.data) {
                    const d = data.data;
                    const items = Array.isArray(d.items) ? d.items : [];
                    items.forEach(i => { i.__key = i.knowledge_id; });
                    knowledgeItems.value = items;
                    knowledgeTotal.value = Number(d.total) || items.length;
                    if (knowledgeTotalPages.value > 0 && knowledgePage.value > knowledgeTotalPages.value) {
                        knowledgePage.value = knowledgeTotalPages.value;
                    }
                } else {
                    knowledgeItems.value = [];
                    knowledgeTotal.value = 0;
                }
            } catch (e) {
                knowledgeItems.value = [];
                knowledgeTotal.value = 0;
            } finally {
                isSearching.value = false;
            }
        }

        async function doSearch() {
            if (!keyword.value || !keyword.value.trim()) {
                showToast('提示', '请输入检索关键词', 'warning');
                return;
            }
            isSearching.value = true;
            knowledgePage.value = 1;
            selectedKnowledgeIds.value = [];
            await loadKnowledgeList({ isSearch: true });
            showToast('检索完成', `在「${currentBaseName.value}」中找到 ${knowledgeTotal.value} 条结果`, 'success');
        }

        function clearSearch() {
            keyword.value = '';
            selectedKnowledgeIds.value = [];
            knowledgePage.value = 1;
            loadKnowledgeList({ isSearch: false });
        }

        async function selectKnowledgeBase(kbId) {
            if (!kbId) return;
            selectedKnowledgeBase.value = kbId;
            keyword.value = '';
            knowledgePage.value = 1;
            selectedKnowledgeIds.value = [];
            await loadKnowledgeList({ isSearch: false });
        }

        function onPageSizeChange() {
            knowledgePage.value = 1;
            loadKnowledgeList({ isSearch: !!keyword.value });
        }

        function onPageChange() {
            loadKnowledgeList({ isSearch: !!keyword.value });
        }

        async function viewKnowledgeDetail(item) {
            if (!item) return;
            showKnowledgeDetail.value = true;
            currentKnowledge.value = { ...item };
            try {
                const data = await apiFetch(`/api/knowledge/detail?knowledge_id=${encodeURIComponent(item.knowledge_id)}`);
                if (data && data.success && data.data) {
                    currentKnowledge.value = { ...data.data, __key: data.data.knowledge_id };
                }
            } catch (e) {}
        }

        function toggleKnowledgeSelection(key) {
            if (!key) return;
            const idx = selectedKnowledgeIds.value.indexOf(key);
            if (idx >= 0) {
                selectedKnowledgeIds.value.splice(idx, 1);
            } else {
                selectedKnowledgeIds.value.push(key);
            }
        }

        function selectAllOnPage() {
            const keyField = isEvaluation.value ? 'index_id' : 'knowledge_id';
            const pageIds = (pagedKnowledge.value || []).map(k => k[keyField]).filter(Boolean);
            if (!pageIds.length) return;
            if (isPageAllSelected.value) {
                selectedKnowledgeIds.value = selectedKnowledgeIds.value.filter(id => !pageIds.includes(id));
            } else {
                const existing = new Set(selectedKnowledgeIds.value);
                pageIds.forEach(id => existing.add(id));
                selectedKnowledgeIds.value = Array.from(existing);
            }
        }

        async function batchDeleteKnowledge() {
            if (!selectedKnowledgeIds.value.length) {
                showToast('未选择', '请先勾选要删除的知识条目', 'warning');
                return;
            }
            try {
                const payload = { knowledge_ids: selectedKnowledgeIds.value.slice() };
                const data = await apiFetch('/api/knowledge/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const cnt = (data && data.data && data.data.deleted_count) || selectedKnowledgeIds.value.length;
                selectedKnowledgeIds.value = [];
                showToast('删除成功', `已从数据库删除 ${cnt} 条知识`, 'success');
                await loadKnowledgeList({ isSearch: !!keyword.value });
            } catch (e) {}
        }

        function openUploadModal() {
            resetUploadForm();
            uploadForm.knowledge_base = selectedKnowledgeBase.value;
            showKnowledgeUploadModal.value = true;
        }

        function parseAgentIdsInput(input) {
            if (!input) return [];
            return String(input).split(/[,，\s]+/).map(s => s.trim()).filter(Boolean);
        }

        async function submitUpload() {
            if (!canUploadKnowledge.value || uploading.value) return;
            uploading.value = true;
            try {
                const base = uploadForm.knowledge_base;
                let payload = null;

                if (base === 'decomposition') {
                    const tags = parseTags(uploadTagsInput.value);
                    payload = {
                        knowledge_base: 'decomposition',
                        knowledge_id: uploadForm.task_id,
                        title: uploadForm.task_name,
                        summary: uploadForm.content,
                        content: uploadForm.content,
                        tags: tags,
                        category: 'decomposition',
                    };
                    const data = await apiFetch('/api/knowledge/add', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if (data && data.success) {
                        showToast('上传成功', `${uploadForm.task_id} ${uploadForm.task_name} 已保存到方案拆解库`, 'success');
                        showKnowledgeUploadModal.value = false;
                        await loadKnowledgeList({ isSearch: !!keyword.value });
                    }
                } else {
                    const tags = parseTags(uploadTagsInput.value);
                    payload = {
                        knowledge_base: base,
                        knowledge_id: uploadForm.knowledge_id,
                        title: uploadForm.title,
                        summary: uploadForm.summary,
                        content: uploadForm.content,
                        tags: tags,
                        category: base,
                    };
                    const data = await apiFetch('/api/knowledge/add', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if (data && data.success) {
                        showToast('上传成功', `${uploadForm.knowledge_id || uploadForm.title} 已保存到知识库`, 'success');
                        showKnowledgeUploadModal.value = false;
                        await loadKnowledgeList({ isSearch: !!keyword.value });
                    }
                }
            } catch (e) {} finally {
                uploading.value = false;
            }
        }

        function editCurrentFromDetail() {
            const it = currentKnowledge.value || {};
            resetEditForm();
            editForm._isIndex = false;
            editForm.knowledge_id = it.knowledge_id || '';
            editForm.title = it.title || '';
            editForm.summary = it.summary || '';
            editForm.content = it.content || '';
            editForm.category = it.category || selectedKnowledgeBase.value;
            editForm.tags = Array.isArray(it.tags) ? it.tags.slice() : parseTags(it.tags || '');
            editTagsInput.value = joinTags(editForm.tags);
            showKnowledgeDetail.value = false;
            showEditModal.value = true;
        }

        function editKnowledgeItem(item) {
            if (!item) return;
            resetEditForm();
            editForm._isIndex = false;
            editForm.knowledge_id = item.knowledge_id || '';
            editForm.title = item.title || '';
            editForm.summary = item.summary || '';
            editForm.content = item.content || '';
            editForm.category = item.category || selectedKnowledgeBase.value;
            editForm.tags = Array.isArray(item.tags) ? item.tags.slice() : parseTags(item.tags || '');
            editTagsInput.value = joinTags(editForm.tags);
            showKnowledgeUploadModal.value = false;
            showKnowledgeDetail.value = false;
            showEditModal.value = true;
        }

        async function saveKnowledgeEdit() {
            if (!canSaveEdit.value) {
                showToast('验证失败', '请至少填写必填字段', 'warning');
                return;
            }
            try {
                editForm.tags = parseTags(editTagsInput.value);
                const payload = {
                    knowledge_id: editForm.knowledge_id,
                    title: editForm.title,
                    summary: editForm.summary,
                    content: editForm.content,
                    tags: editForm.tags,
                    category: editForm.category || selectedKnowledgeBase.value
                };
                const data = await apiFetch('/api/knowledge/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (data && data.success) {
                    showToast('保存成功', `${editForm.knowledge_id} 已更新到数据库`, 'success');
                    showEditModal.value = false;
                    await loadKnowledgeList({ isSearch: !!keyword.value });
                }
            } catch (e) {}
        }

        onMounted(() => {
            loadKnowledgeList({ isSearch: false });
        });

        function openIndicatorLibrary() {
            // 知识管理页运行在 index.html 的 iframe 中，切换 iframe 到指标管理库页面
            window.location.href = 'indicator_library.html';
        }

        return {
            // 工具
            toasts, removeToast,
            splitTags, joinTags, formatDateTime,
            // 基础
            knowledgeBases, selectedKnowledgeBase, currentBaseName, currentObjectType,
            isEvaluation,
            keyword, isSearching,
            // 列表
            knowledgeItems, knowledgeTotal, knowledgePageSize,
            knowledgeCurrentPage, knowledgePage, onPageChange,
            pagedKnowledge, knowledgeTotalPages,
            selectedKnowledgeIds, isPageAllSelected,
            // 弹窗
            showKnowledgeDetail, showEditModal, showKnowledgeUploadModal,
            currentKnowledge, editForm, uploadForm, uploadTagsInput, editTagsInput,
            uploading, canUploadKnowledge, canSaveEdit,
            // 选项
            INDEX_TYPE_OPTIONS, INDEX_LEVEL_OPTIONS,
            PRIORITY_OPTIONS, TASK_TYPE_OPTIONS, SIMULATION_TYPE_OPTIONS,
            // 方法
            selectKnowledgeBase, onPageSizeChange, loadKnowledgeList,
            doSearch, clearSearch,
            viewKnowledgeDetail, toggleKnowledgeSelection, selectAllOnPage,
            batchDeleteKnowledge,
            openUploadModal, submitUpload,
            editKnowledgeItem, editCurrentFromDetail, saveKnowledgeEdit,
            openIndicatorLibrary
        };
    }
}).mount('#app');
