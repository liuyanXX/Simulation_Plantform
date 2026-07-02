const { createApp, ref, computed, reactive, onMounted, watch } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const { apiFetch: _apiFetch, showToast: _showToast, toasts, removeToast, formatDateTime } = C;

const API_BASE = '/api/system';

const apiFetch = typeof _apiFetch === 'function' ? _apiFetch : async (url, opts = {}) => {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
};

const showToast = typeof _showToast === 'function' ? _showToast : (title, detail, type) => {
    console.log(`[Toast] ${type}: ${title} - ${detail}`);
};

createApp({
    setup() {
        const tabs = ref([
            { key: 'org',    icon: '🏢', label: '组织', count: -1, desc: '组织架构维护' },
            { key: 'emp',    icon: '👤', label: '人员', count: -1, desc: '人员信息与状态' },
            { key: 'role',   icon: '🛡️', label: '角色', count: -1, desc: '角色定义维护' },
            { key: 'perm',   icon: '🔑', label: '权限', count: -1, desc: '员工-角色 指派/回收' },
            { key: 'worker', icon: '🤖', label: '智能员工', count: -1, desc: '智能员工注册与设定' },
            { key: 'reg',    icon: '📇', label: '智能员工注册', count: -1, desc: '智能员工类型 / 全路径类名 / 最大数量 注册管理' },
        ]);
        // 侧边栏分组菜单：系统管理 → 智能员工管理 → 智能员工注册
        const menuGroups = computed(() => ([
            { title: '系统对象', items: tabs.value.filter(t => ['org', 'emp', 'role', 'perm'].indexOf(t.key) !== -1) },
            { title: '智能员工管理', items: tabs.value.filter(t => ['worker', 'reg'].indexOf(t.key) !== -1) },
        ]));
        const currentTab = ref('org');
        const keyword = ref('');
        const isLoading = ref(false);
        const list = ref([]);
        const total = ref(0);
        const currentPage = ref(1);
        const pageSize = ref(10);
        
        const loadStatus = ref('加载中...');
        const loadStatusType = ref('info');
        
        const loadStatusClass = computed(() => {
            return `status-${loadStatusType.value}`;
        });

        const orgParents = ref([]);
        const allRoles = ref([]);
        const employeeRoles = ref({});

        const orgTypeLabels = { COMPANY: '公司', DEPARTMENT: '部门', TEAM: '团队', GROUP: '小组', ORG: '其它' };
        function orgTypeLabel(v) { return orgTypeLabels[v] || v || '-'; }
        const orgFilter = reactive({ status: '', org_type: '', parent_id: '' });
        const empFilter = reactive({ status: '', org_id: '' });
        const roleFilter = reactive({ status: '' });
        const workerFilter = reactive({ department: '' });
        const regFilter = reactive({ status: '' });

        const showModal = ref(false);
        const modalTitle = ref('');
        const isSubmitting = ref(false);
        const isEditing = ref(false);
        const form = reactive({
            _edit_id: null,
            org_code: '', org_name: '', org_type: 'DEPARTMENT', parent_id: null,
            sort_order: 0, status: 'active', description: '',
            emp_code: '', emp_name: '', position: '', org_id: null,
            email: '', phone: '',
            role_code: '', role_name: '',
            employee_id: '', name: '', department: '',
            daily_work_hours: 8, roles_raw: '',
            worker_type: '', worker_name: '', class_path: '', max_count: 0
        });

        const showRoleModal = ref(false);
        const roleModalEmployee = ref(null);
        const selectedRoleIds = ref([]);

        const currentTabTitle = computed(() => {
            const t = tabs.value.find(x => x.key === currentTab.value);
            return t ? t.label : '';
        });
        const currentTabDesc = computed(() => {
            const t = tabs.value.find(x => x.key === currentTab.value);
            return t ? t.desc : '';
        });
        const currentTabPlaceholder = computed(() => {
            const m = {
                org: '按组织名称 / 编码 / 说明搜索',
                emp: '按姓名 / 工号 / 职位搜索',
                role: '按角色名称 / 编码搜索',
                perm: '按员工姓名 / 工号搜索',
                worker: '按智能员工姓名 / 员工ID搜索',
                reg: '按类型 / 名称 / 类名搜索'
            };
            return m[currentTab.value] || '输入关键词搜索';
        });
        const currentTabAddLabel = computed(() => {
            const m = { org: '新增组织', emp: '新增人员', role: '新增角色', worker: '新增智能员工', reg: '新增注册' };
            return m[currentTab.value] || '';
        });
        const emptyHint = computed(() => {
            if (keyword.value) return '未找到匹配结果，可清除关键词重试';
            const m = { org: '暂无组织，请点击“新增组织”添加。', emp: '暂无人员，请点击“新增人员”添加。', role: '暂无角色，请点击“新增角色”添加。', perm: '暂无员工数据。', worker: '暂无智能员工，请点击“新增智能员工”添加。', reg: '暂无智能员工注册，请点击“新增注册”添加。' };
            return m[currentTab.value] || '暂无数据';
        });

        const totalPages = computed(() => {
            const ps = pageSize.value || 10;
            const t = total.value || 0;
            return Math.max(1, Math.ceil(t / ps));
        });

        const paginatedList = computed(() => {
            if (!list.value || !list.value.length) return [];
            const ps = pageSize.value || 10;
            const p = currentPage.value || 1;
            const start = (p - 1) * ps;
            return list.value.slice(start, start + ps);
        });

        function statusLabel(s) {
            const m = {
                active: '在用', disabled: '停用', archived: '归档', resigned: '离职'
            };
            return m[s] || s || '-';
        }
        function statusClass(s) {
            if (s === 'active') return 'success';
            if (s === 'disabled' || s === 'resigned') return 'warning';
            if (s === 'archived') return 'info';
            return 'info';
        }

        function selectTab(k) {
            if (currentTab.value === k) return;
            currentTab.value = k;
            keyword.value = '';
            currentPage.value = 1;
            reloadList();
        }

        async function reloadList() {
            isLoading.value = true;
            try {
                const tab = currentTab.value;
                const ps = pageSize.value || 10;
                const p = currentPage.value || 1;
                let url;
                if (tab === 'org') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (orgFilter.status) qs.set('status', orgFilter.status);
                    if (orgFilter.org_type) qs.set('org_type', orgFilter.org_type);
                    if (orgFilter.parent_id) qs.set('parent_id', orgFilter.parent_id);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/organizations?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                    refreshOrgParents();
                } else if (tab === 'emp') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (empFilter.status) qs.set('status', empFilter.status);
                    if (empFilter.org_id) qs.set('org_id', empFilter.org_id);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/employees?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                    refreshAllRoles();
                    await batchLoadEmployeeRoles();
                } else if (tab === 'role') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (roleFilter.status) qs.set('status', roleFilter.status);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/roles?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                } else if (tab === 'perm') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/employees?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                    refreshAllRoles();
                    await batchLoadEmployeeRoles();
                } else if (tab === 'worker') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (workerFilter.department) qs.set('department', workerFilter.department);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/workers?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                } else if (tab === 'reg') {
                    const qs = new URLSearchParams();
                    qs.set('page', p);
                    qs.set('page_size', ps);
                    if (regFilter.status) qs.set('status', regFilter.status);
                    if (keyword.value) qs.set('keyword', keyword.value);
                    url = `${API_BASE}/worker-registries?${qs.toString()}`;
                    const data = await apiFetch(url);
                    if (data && data.success && data.data) {
                        list.value = data.data.list || [];
                        total.value = data.data.total || 0;
                    } else {
                        list.value = []; total.value = 0;
                    }
                }
                if (currentPage.value > totalPages.value) {
                    currentPage.value = totalPages.value;
                }
                updateTabsCount();
            } catch (e) {
                list.value = []; total.value = 0;
            } finally {
                isLoading.value = false;
            }
        }

        function updateTabsCount() {
            tabs.value.forEach(t => {
                if (t.key === currentTab.value) {
                    t.count = total.value || 0;
                } else {
                    t.count = -1;
                }
            });
        }

        async function refreshOrgParents() {
            try {
                const data = await apiFetch(`${API_BASE}/organizations?page=1&page_size=500`);
                if (data && data.success && data.data) {
                    orgParents.value = data.data.list || [];
                }
            } catch (e) { orgParents.value = []; }
        }

        async function refreshAllRoles() {
            try {
                const data = await apiFetch(`${API_BASE}/roles?page=1&page_size=500`);
                if (data && data.success && data.data) {
                    allRoles.value = data.data.list || [];
                }
            } catch (e) { allRoles.value = []; }
        }

        function getOrgNameById(id) {
            const o = (orgParents.value || []).find(x => x.id === id);
            return o ? o.org_name : '';
        }

        async function batchLoadEmployeeRoles() {
            const empList = list.value || [];
            const ids = empList.map(e => e.id).filter(Boolean);
            const results = {};
            for (const id of ids) {
                try {
                    const data = await apiFetch(`${API_BASE}/employees/${id}/roles`);
                    if (data && data.success) {
                        results[id] = Array.isArray(data.data) ? data.data : [];
                    } else {
                        results[id] = [];
                    }
                } catch (e) { results[id] = []; }
            }
            employeeRoles.value = results;
        }

        function doSearch() {
            currentPage.value = 1;
            reloadList();
        }
        function clearSearch() {
            keyword.value = '';
            currentPage.value = 1;
            reloadList();
        }

        // ========== 弹窗 ==========
        function resetForm() {
            Object.assign(form, {
                _edit_id: null,
                org_code: '', org_name: '', org_type: 'DEPARTMENT', parent_id: null,
                sort_order: 0, status: 'active', description: '',
                emp_code: '', emp_name: '', position: '', org_id: null,
                email: '', phone: '',
                role_code: '', role_name: '',
                employee_id: '', name: '', department: '',
                daily_work_hours: 8, roles_raw: '',
                worker_type: '', worker_name: '', class_path: '', max_count: 0
            });
        }

        function openAddModal() {
            const tab = currentTab.value;
            if (tab === 'perm') return;
            if (tab === 'worker') {
                modalTitle.value = '新增智能员工';
            } else if (tab === 'org') {
                modalTitle.value = '新增组织';
            } else if (tab === 'emp') {
                modalTitle.value = '新增人员';
            } else if (tab === 'role') {
                modalTitle.value = '新增角色';
            } else if (tab === 'reg') {
                modalTitle.value = '新增智能员工注册';
            }
            isEditing.value = false;
            resetForm();
            showModal.value = true;
        }

        function openEditOrg(o) {
            modalTitle.value = '编辑组织';
            isEditing.value = true;
            resetForm();
            Object.assign(form, {
                _edit_id: o.id,
                org_code: o.org_code || '',
                org_name: o.org_name || '',
                org_type: o.org_type || 'DEPARTMENT',
                parent_id: o.parent_id,
                sort_order: o.sort_order || 0,
                status: o.status || 'active',
                description: o.description || ''
            });
            showModal.value = true;
        }
        function openEditEmp(e) {
            modalTitle.value = '编辑人员';
            isEditing.value = true;
            resetForm();
            Object.assign(form, {
                _edit_id: e.id,
                emp_code: e.emp_code || '',
                emp_name: e.emp_name || '',
                position: e.position || '',
                org_id: e.org_id,
                email: e.email || '',
                phone: e.phone || '',
                status: e.status || 'active'
            });
            showModal.value = true;
        }
        function openEditRole(r) {
            modalTitle.value = '编辑角色';
            isEditing.value = true;
            resetForm();
            Object.assign(form, {
                _edit_id: r.id,
                role_code: r.role_code || '',
                role_name: r.role_name || '',
                status: r.status || 'active',
                description: r.description || ''
            });
            showModal.value = true;
        }
        function openEditWorker(w) {
            modalTitle.value = '编辑智能员工';
            isEditing.value = true;
            resetForm();
            Object.assign(form, {
                _edit_id: w.employee_id,
                employee_id: w.employee_id || '',
                name: w.name || '',
                department: w.department || '',
                daily_work_hours: w.daily_work_hours || 8,
                roles_raw: Array.isArray(w.roles) ? w.roles.join(', ') : (w.roles || '')
            });
            showModal.value = true;
        }

        function openEditReg(r) {
            modalTitle.value = '编辑智能员工注册';
            isEditing.value = true;
            resetForm();
            Object.assign(form, {
                _edit_id: r.id,
                worker_type: r.worker_type || '',
                worker_name: r.worker_name || '',
                class_path: r.class_path || '',
                max_count: r.max_count || 0,
                status: r.status || 'active',
                description: r.description || ''
            });
            showModal.value = true;
        }

        function confirmDeleteOrg(o) {
            if (!confirm(`确定删除组织「${o.org_name}」及其子组织与下属人员？`)) return;
            deleteEntity('org', o.id);
        }
        function confirmDeleteEmp(e) {
            if (!confirm(`确定删除人员「${e.emp_name} (${e.emp_code})」？`)) return;
            deleteEntity('emp', e.id);
        }
        function confirmDeleteRole(r) {
            if (!confirm(`确定删除角色「${r.role_name}」？（员工角色关联也将删除）`)) return;
            deleteEntity('role', r.id);
        }
        function confirmDeleteWorker(w) {
            if (!confirm(`确定删除智能员工「${w.name} (${w.employee_id})」？`)) return;
            deleteEntity('worker', w.employee_id);
        }

        function confirmDeleteReg(r) {
            if (!confirm(`确定删除智能员工注册「${r.worker_name} (${r.worker_type})」？`)) return;
            deleteEntity('reg', r.id);
        }

        async function deleteEntity(tab, id) {
            try {
                let url, method = 'DELETE';
                if (tab === 'org')       url = `${API_BASE}/organizations/${id}?cascade=true`;
                else if (tab === 'emp')  url = `${API_BASE}/employees/${id}`;
                else if (tab === 'role') url = `${API_BASE}/roles/${id}`;
                else if (tab === 'worker') url = `${API_BASE}/workers/${encodeURIComponent(id)}`;
                else if (tab === 'reg') url = `${API_BASE}/worker-registries/${id}`;
                const res = await apiFetch(url, { method });
                if (res && res.success) {
                    showToast('删除成功', '对象已删除', 'success');
                    await reloadList();
                }
            } catch (e) {}
        }

        async function submitModal() {
            const tab = currentTab.value;
            isSubmitting.value = true;
            try {
                if (tab === 'org') {
                    const payload = {
                        org_code: form.org_code.trim(),
                        org_name: form.org_name.trim(),
                        org_type: form.org_type,
                        parent_id: form.parent_id || null,
                        sort_order: Number(form.sort_order) || 0,
                        status: form.status,
                        description: form.description || ''
                    };
                    let url, method, body;
                    if (isEditing.value) {
                        url = `${API_BASE}/organizations/${form._edit_id}`;
                        method = 'PUT';
                    } else {
                        url = `${API_BASE}/organizations`;
                        method = 'POST';
                    }
                    body = JSON.stringify(payload);
                    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body });
                    if (res && res.success) {
                        showToast('保存成功', '组织已保存', 'success');
                        showModal.value = false;
                        await reloadList();
                    }
                } else if (tab === 'emp') {
                    const payload = {
                        emp_code: form.emp_code.trim(),
                        emp_name: form.emp_name.trim(),
                        position: form.position || '',
                        org_id: form.org_id || null,
                        email: form.email || '',
                        phone: form.phone || '',
                        status: form.status
                    };
                    let url, method, body;
                    if (isEditing.value) {
                        url = `${API_BASE}/employees/${form._edit_id}`;
                        method = 'PUT';
                    } else {
                        url = `${API_BASE}/employees`;
                        method = 'POST';
                    }
                    body = JSON.stringify(payload);
                    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body });
                    if (res && res.success) {
                        showToast('保存成功', '人员已保存', 'success');
                        showModal.value = false;
                        await reloadList();
                    }
                } else if (tab === 'role') {
                    const payload = {
                        role_code: form.role_code.trim(),
                        role_name: form.role_name.trim(),
                        status: form.status,
                        description: form.description || ''
                    };
                    let url, method, body;
                    if (isEditing.value) {
                        url = `${API_BASE}/roles/${form._edit_id}`;
                        method = 'PUT';
                    } else {
                        url = `${API_BASE}/roles`;
                        method = 'POST';
                    }
                    body = JSON.stringify(payload);
                    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body });
                    if (res && res.success) {
                        showToast('保存成功', '角色已保存', 'success');
                        showModal.value = false;
                        await reloadList();
                    }
                } else if (tab === 'worker') {
                    const roles = String(form.roles_raw || '').split(/[,，\s]+/).map(s => s.trim()).filter(Boolean);
                    const payload = {
                        employee_id: form.employee_id.trim(),
                        name: form.name.trim(),
                        department: form.department || '',
                        daily_work_hours: Number(form.daily_work_hours) || 8,
                        roles
                    };
                    let url, method, body;
                    if (isEditing.value) {
                        url = `${API_BASE}/workers/${encodeURIComponent(form._edit_id)}`;
                        method = 'PUT';
                    } else {
                        url = `${API_BASE}/workers`;
                        method = 'POST';
                    }
                    body = JSON.stringify(payload);
                    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body });
                    if (res && res.success) {
                        showToast('保存成功', '智能员工已保存', 'success');
                        showModal.value = false;
                        await reloadList();
                    }
                } else if (tab === 'reg') {
                    const payload = {
                        worker_type: String(form.worker_type || '').trim(),
                        worker_name: String(form.worker_name || '').trim(),
                        class_path: String(form.class_path || '').trim(),
                        max_count: Number(form.max_count) || 0,
                        status: form.status || 'active',
                        description: form.description || ''
                    };
                    let url, method, body;
                    if (isEditing.value) {
                        url = `${API_BASE}/worker-registries/${form._edit_id}`;
                        method = 'PUT';
                    } else {
                        url = `${API_BASE}/worker-registries`;
                        method = 'POST';
                    }
                    body = JSON.stringify(payload);
                    const res = await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body });
                    if (res && res.success) {
                        showToast('保存成功', '智能员工注册已保存', 'success');
                        showModal.value = false;
                        await reloadList();
                    } else if (res && res.success === false) {
                        showToast('保存失败', res.message || '', 'error');
                    }
                }
            } catch (e) {
                showToast('保存失败', String(e && e.message || e), 'error');
            } finally {
                isSubmitting.value = false;
            }
        }

        // ========== 角色指派弹窗 ==========
        async function openRoleModal(emp) {
            roleModalEmployee.value = emp;
            await refreshAllRoles();
            let currentRoles = employeeRoles.value[emp.id] || [];
            selectedRoleIds.value = currentRoles.map(r => r.id);
            showRoleModal.value = true;
        }

        async function toggleEmployeeRole(roleId) {
            const emp = roleModalEmployee.value;
            if (!emp) return;
            const idx = selectedRoleIds.value.indexOf(roleId);
            try {
                if (idx >= 0) {
                    selectedRoleIds.value.splice(idx, 1);
                    const data = await apiFetch(`${API_BASE}/employees/${emp.id}/roles/${roleId}`, { method: 'DELETE' });
                    if (!data || data.success === false) {
                        showToast('操作失败', (data && data.message) || '回收角色失败', 'error');
                        selectedRoleIds.value.splice(0, idx, roleId);
                    } else {
                        showToast('已回收角色', '', 'success');
                    }
                } else {
                    selectedRoleIds.value.push(roleId);
                    const data = await apiFetch(`${API_BASE}/employees/${emp.id}/roles/${roleId}`, { method: 'POST' });
                    if (!data || data.success === false) {
                        showToast('操作失败', (data && data.message) || '指派角色失败', 'error');
                        selectedRoleIds.value.pop();
                    } else {
                        showToast('已指派角色', '', 'success');
                    }
                }
                await batchLoadEmployeeRoles();
            } catch (e) {
                showToast('操作异常', String(e && e.message || e), 'error');
            }
        }

        onMounted(async () => {
            try {
                loadStatus.value = '正在加载组织数据...';
                loadStatusType.value = 'info';
                await refreshOrgParents();
                loadStatus.value = `已加载 ${orgParents.value.length} 个父组织，正在查询列表...`;
                await reloadList();
                loadStatus.value = `加载完成，共 ${total.value} 条记录`;
                loadStatusType.value = 'success';
            } catch (e) {
                loadStatus.value = `加载失败: ${e.message}`;
                loadStatusType.value = 'error';
                console.error('初始化失败:', e);
            }
        });

        return {
            toasts, removeToast,
            // state
            tabs, currentTab,
            menuGroups,
            keyword, isLoading,
            list, total, currentPage, pageSize,
            loadStatus, loadStatusClass,
            orgFilter, empFilter, roleFilter, workerFilter, regFilter,
            orgParents, allRoles, employeeRoles,
            showModal, modalTitle, isSubmitting, isEditing, form,
            showRoleModal, roleModalEmployee, selectedRoleIds,
            // computed
            currentTabTitle, currentTabDesc, currentTabPlaceholder, currentTabAddLabel,
            totalPages, paginatedList, emptyHint,
            // helpers
            statusLabel, statusClass,
            orgTypeLabel,
            getOrgNameById,
            // actions
            selectTab, reloadList, doSearch, clearSearch,
            openAddModal, openEditOrg, openEditEmp, openEditRole, openEditWorker,
            confirmDeleteOrg, confirmDeleteEmp, confirmDeleteRole, confirmDeleteWorker,
            openEditReg, confirmDeleteReg,
            submitModal,
            openRoleModal, toggleEmployeeRole
        };
    }
}).mount('#app');
