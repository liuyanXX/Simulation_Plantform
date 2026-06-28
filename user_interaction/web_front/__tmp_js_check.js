
        const { createApp, ref, computed, reactive } = Vue;



        createApp({

            setup() {

                // 导航

                const currentView = ref('solution');

                const navItems = [

                    { key: 'solution', label: '方案管理' },

                    { key: 'understanding', label: '方案理解' },

                    { key: 'decomposition', label: '方案拆分' },

                    { key: 'display', label: '信息展示' },

                    { key: 'simulation', label: '仿真管理' },

                    { key: 'evaluation', label: '评估管理' },

                    { key: 'knowledge', label: '知识管理' }

                ];



                const switchView = (view) => {

                    currentView.value = view;

                };



                // 消息提示

                const toasts = ref([]);

                let toastId = 0;



                const showToast = (title, message, type = 'info') => {

                    const id = ++toastId;

                    toasts.value.push({ id, title, message, type });

                    setTimeout(() => {

                        toasts.value = toasts.value.filter(t => t.id !== id);

                    }, 3000);

                };



                // 方案管理

                const solutionList = ref([]);

                const solutionTotal = ref(0);

                const solutionPage = ref(1);

                const solutionPageSize = ref(10);

                const solutionSearchQuery = ref('');

                const selectedSolutionIds = ref([]);

                const showSolutionDetailModal = ref(false);

                const showUploadModal = ref(false);

                const solutionDetail = reactive({});



                const solutionUploadForm = reactive({

                    document_id: '',

                    version: '1.0',

                    document_type: 'main',

                    description: '',

                    created_by: '',

                    uploadedFiles: []

                });



                const canUploadSolution = computed(() => {

                    return solutionUploadForm.document_id && solutionUploadForm.uploadedFiles.length > 0;

                });



                const loadSolutionList = async () => {

                    try {

                        const response = await fetch(`/api/solution/list?page=${solutionPage.value}&page_size=${solutionPageSize.value}&keyword=${solutionSearchQuery.value || ''}`);

                        const data = await response.json();

                        if (data.success) {

                            solutionList.value = data.data.list;

                            solutionTotal.value = data.data.total;

                        }

                    } catch (error) {

                        console.error('获取方案列表失败:', error);

                    }

                };



                const searchSolutions = () => {

                    solutionPage.value = 1;

                    loadSolutionList();

                };



                const clearSolutionSearch = () => {

                    solutionSearchQuery.value = '';

                    solutionPage.value = 1;

                    loadSolutionList();

                };



                const prevSolutionPage = () => {

                    if (solutionPage.value > 1) {

                        solutionPage.value--;

                        loadSolutionList();

                    }

                };



                const nextSolutionPage = () => {

                    if (solutionPage.value < Math.ceil(solutionTotal.value / solutionPageSize.value)) {

                        solutionPage.value++;

                        loadSolutionList();

                    }

                };



                const toggleSelectAllSolutions = () => {

                    if (selectedSolutionIds.value.length === solutionList.value.length) {

                        selectedSolutionIds.value = [];

                    } else {

                        selectedSolutionIds.value = solutionList.value.map(s => s.document_id);

                    }

                };



                const toggleSolutionSelection = (solutionId) => {

                    const idx = selectedSolutionIds.value.indexOf(solutionId);

                    if (idx >= 0) {

                        selectedSolutionIds.value.splice(idx, 1);

                    } else {

                        selectedSolutionIds.value.push(solutionId);

                    }

                };



                const viewSolutionDetail = async (item) => {

                    Object.assign(solutionDetail, item);

                    showSolutionDetailModal.value = true;

                };



                const deleteSolution = async (documentId) => {

                    if (!confirm('确定要删除这个文档吗？')) return;

                    try {

                        const response = await fetch(`/api/solution/delete_document?document_id=${documentId}`, {

                            method: 'DELETE'

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('删除成功', '文档已删除');

                            loadSolutionList();

                        } else {

                            showToast('删除失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('删除文档失败:', error);

                        showToast('删除失败', '网络请求失败', 'error');

                    }

                };



                const batchDeleteSolutions = async () => {

                    if (!confirm(`确定要删除选中的 ${selectedSolutionIds.value.length} 个文档吗？`)) return;

                    try {

                        const response = await fetch('/api/solution/batch_delete_documents', {

                            method: 'POST',

                            headers: {

                                'Content-Type': 'application/json'

                            },

                            body: JSON.stringify({ document_ids: selectedSolutionIds.value })

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('删除成功', `已删除 ${selectedSolutionIds.value.length} 个文档`);

                            selectedSolutionIds.value = [];

                            loadSolutionList();

                        } else {

                            showToast('删除失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('批量删除文档失败:', error);

                        showToast('删除失败', '网络请求失败', 'error');

                    }

                };

                const handleDocumentSelect = (event) => {

                    const files = event.target.files;

                    if (files) {

                        Array.from(files).forEach(file => {

                            solutionUploadForm.uploadedFiles.push(file);

                        });

                    }

                    event.target.value = '';

                };



                const handleDocumentDrop = (event) => {

                    const files = event.dataTransfer.files;

                    if (files) {

                        Array.from(files).forEach(file => {

                            solutionUploadForm.uploadedFiles.push(file);

                        });

                    }

                };

                const openFilePicker = (inputId) => {
                    const el = document.getElementById(inputId);
                    if (el) { el.click(); }
                    else { console.warn('openFilePicker: element not found:', inputId); }
                };



                const uploadSolution = async () => {

                    if (!solutionUploadForm.document_id || solutionUploadForm.uploadedFiles.length === 0) {

                        showToast('验证失败', '文档ID和文件为必填项', 'error');

                        return;

                    }



                    const formData = new FormData();

                    formData.append('document_id', solutionUploadForm.document_id);

                    formData.append('version', solutionUploadForm.version);

                    formData.append('document_type', solutionUploadForm.document_type);

                    formData.append('description', solutionUploadForm.description);

                    formData.append('created_by', solutionUploadForm.created_by);



                    solutionUploadForm.uploadedFiles.forEach((file) => {

                        formData.append('files', file);

                    });



                    try {

                        const response = await fetch('/api/solution/upload_document', {

                            method: 'POST',

                            body: formData

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('上传成功', `文档 [${solutionUploadForm.document_id}] 已上传`);

                            showUploadModal.value = false;

                            Object.assign(solutionUploadForm, {

                                document_id: '',

                                version: '1.0',

                                document_type: 'main',

                                description: '',

                                created_by: '',

                                uploadedFiles: []

                            });

                            loadSolutionList();

                        } else {

                            showToast('上传失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('上传文档失败:', error);

                        showToast('上传失败', '网络请求失败', 'error');

                    }

                };



                const downloadSolutionDocument = async (documentId) => {

                    try {

                        const response = await fetch(`/api/solution/download?document_id=${documentId}`);

                        if (response.ok) {

                            const blob = await response.blob();

                            const contentDisposition = response.headers.get('Content-Disposition');

                            const fileName = contentDisposition ? contentDisposition.split('filename=')[1].replace(/['"]/g, '') : 'document';

                            const url = window.URL.createObjectURL(blob);

                            const a = document.createElement('a');

                            a.href = url;

                            a.download = fileName;

                            document.body.appendChild(a);

                            a.click();

                            document.body.removeChild(a);

                            window.URL.revokeObjectURL(url);

                        } else {

                            showToast('下载失败', '服务器返回错误', 'error');

                        }

                    } catch (error) {

                        console.error('下载文档失败:', error);

                        showToast('下载失败', '网络请求失败', 'error');

                    }

                };



                const getSolutionStatusName = (status) => {

                    const statusMap = {

                        'draft': '草稿',

                        'review': '审核中',

                        'approved': '已批准',

                        'active': '执行中',

                        'suspended': '已暂停',

                        'completed': '已完成',

                        'archived': '已归档'

                    };

                    return statusMap[status] || status;

                };



                const getSolutionStatusClass = (status) => {

                    const classMap = {

                        'draft': 'status-draft',

                        'review': 'status-review',

                        'approved': 'status-approved',

                        'active': 'status-active',

                        'suspended': 'status-suspended',

                        'completed': 'status-completed',

                        'archived': 'status-archived'

                    };

                    return classMap[status] || '';

                };



                const getSolutionPriorityName = (priority) => {

                    const priorityMap = {

                        'low': '低',

                        'medium': '中',

                        'high': '高',

                        'critical': '紧急'

                    };

                    return priorityMap[priority] || priority;

                };



                const getDocumentTypeName = (type) => {

                    const typeMap = {

                        'main': '主文档',

                        'attachment': '附件',

                        'reference': '参考文档'

                    };

                    return typeMap[type] || type;

                };



                const getDocumentStatusName = (status) => {

                    const statusMap = {

                        'pending': '待理解',

                        'processing': '处理中',

                        'understood': '已理解',

                        'failed': '失败'

                    };

                    return statusMap[status] || status;

                };



                const getDocumentStatusClass = (status) => {

                    const classMap = {

                        'pending': 'status-pending',

                        'processing': 'status-processing',

                        'understood': 'status-understood',

                        'failed': 'status-failed'

                    };

                    return classMap[status] || '';

                };



                const formatFileSize = (bytes) => {

                    if (!bytes) return '0 B';

                    const k = 1024;

                    const sizes = ['B', 'KB', 'MB', 'GB'];

                    const i = Math.floor(Math.log(bytes) / Math.log(k));

                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];

                };



                const formatDateTime = (dateStr) => {

                    if (!dateStr) return '';

                    try {

                        const date = new Date(dateStr);

                        return date.toLocaleString('zh-CN', {

                            year: 'numeric',

                            month: '2-digit',

                            day: '2-digit',

                            hour: '2-digit',

                            minute: '2-digit'

                        });

                    } catch {

                        return dateStr;

                    }

                };



                loadSolutionList();



                // 方案理解

                const pendingDocs = ref([]);

                const pendingDocsTotal = ref(0);

                const pendingDocsPage = ref(1);

                const pendingDocsPageSize = ref(5);

                

                const understoodSolutions = ref([]);

                const understoodSolutionsTotal = ref(0);

                const understoodSolutionsPage = ref(1);

                const understoodSolutionsPageSize = ref(10);

                const understoodSolutionsSearchQuery = ref('');

                const selectedUnderstoodSolutionIds = ref([]);

                

                const showPendingDocDetailModal = ref(false);

                const showUnderstoodSolutionDetailModal = ref(false);

                const showStructuredSolutionModal = ref(false);

                const pendingDocDetail = reactive({});

                const understoodSolutionDetail = reactive({});

                

                const structuredSolutionForm = reactive({

                    solution_id: '',

                    name: '',

                    version: '1.0',

                    status: 'draft',

                    priority: 'medium',

                    purpose: '',

                    objectives: [],

                    initiatives: [],

                    working_mechanism: '',

                    organization: [],

                    personnel: [],

                    roles: [],

                    work_content: '',

                    constraints: [],

                    risks: [],

                    issues: [],

                    other_notes: '',

                    tags: [],

                    description: '',

                    owner: '',

                    created_by: '',

                    effective_date: '',

                    expiry_date: '',

                    uploadedDocuments: []

                });



                const newStructuredObjective = ref('');

                const newStructuredInitiative = ref('');

                const newStructuredOrg = ref('');

                const newStructuredRole = ref('');

                const newStructuredPersonnel = ref('');

                const newStructuredRisk = ref('');

                const newStructuredIssue = ref('');

                const newStructuredConstraint = ref('');

                const newStructuredTag = ref('');



                const loadPendingDocuments = async () => {

                    try {

                        const response = await fetch(`/api/solution/pending_documents?page=${pendingDocsPage.value}&page_size=${pendingDocsPageSize.value}`);

                        const data = await response.json();

                        if (data.success) {

                            pendingDocs.value = data.data.list;

                            pendingDocsTotal.value = data.data.total;

                        }

                    } catch (error) {

                        console.error('获取待理解文档列表失败:', error);

                    }

                };



                const loadUnderstoodSolutions = async () => {

                    try {

                        const response = await fetch(`/api/solution/list?page=${understoodSolutionsPage.value}&page_size=${understoodSolutionsPageSize.value}&keyword=${understoodSolutionsSearchQuery.value || ''}`);

                        const data = await response.json();

                        if (data.success) {

                            understoodSolutions.value = data.data.list;

                            understoodSolutionsTotal.value = data.data.total;

                        }

                    } catch (error) {

                        console.error('获取方案对象列表失败:', error);

                    }

                };



                const searchUnderstoodSolutions = () => {

                    understoodSolutionsPage.value = 1;

                    loadUnderstoodSolutions();

                };



                const clearUnderstoodSolutionSearch = () => {

                    understoodSolutionsSearchQuery.value = '';

                    understoodSolutionsPage.value = 1;

                    loadUnderstoodSolutions();

                };



                const viewPendingDocDetail = async (item) => {

                    try {

                        const response = await fetch(`/api/solution/download?document_id=${item.document_id}`);

                        if (response.ok) {

                            Object.assign(pendingDocDetail, item);

                        } else {

                            Object.assign(pendingDocDetail, item);

                        }

                    } catch (error) {

                        console.error('获取文档详情失败:', error);

                        Object.assign(pendingDocDetail, item);

                    }

                    showPendingDocDetailModal.value = true;

                };



                const viewUnderstoodSolutionDetail = async (item) => {

                    try {

                        const response = await fetch(`/api/solution/detail?solution_id=${item.solution_id}`);

                        const data = await response.json();

                        if (data.success) {

                            Object.assign(understoodSolutionDetail, data.data);

                        } else {

                            Object.assign(understoodSolutionDetail, item);

                        }

                    } catch (error) {

                        console.error('获取方案详情失败:', error);

                        Object.assign(understoodSolutionDetail, item);

                    }

                    showUnderstoodSolutionDetailModal.value = true;

                };



                const startConversion = async (documentId) => {

                    if (!confirm('确定要启动方案理解转换吗？')) return;

                    try {

                        const response = await fetch('/api/solution/start_conversion', {

                            method: 'POST',

                            headers: {

                                'Content-Type': 'application/json'

                            },

                            body: JSON.stringify({ document_id: documentId })

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('转换成功', `已成功理解方案: ${data.data.solution_name}`);

                            loadPendingDocuments();

                            loadUnderstoodSolutions();

                        } else {

                            showToast('转换失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('启动转换失败:', error);

                        showToast('转换失败', '网络请求失败', 'error');

                    }

                };



                const updateUnderstoodSolution = async () => {

                    if (!understoodSolutionDetail.solution_id) {

                        showToast('验证失败', '方案ID不能为空', 'error');

                        return;

                    }



                    try {

                        const response = await fetch('/api/solution/update', {

                            method: 'POST',

                            headers: {

                                'Content-Type': 'application/json'

                            },

                            body: JSON.stringify(understoodSolutionDetail)

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('更新成功', `方案 [${understoodSolutionDetail.name}] 已更新`);

                            showUnderstoodSolutionDetailModal.value = false;

                            loadUnderstoodSolutions();

                        } else {

                            showToast('更新失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('更新方案失败:', error);

                        showToast('更新失败', '网络请求失败', 'error');

                    }

                };



                const toggleSelectAllUnderstoodSolutions = () => {

                    if (selectedUnderstoodSolutionIds.value.length === understoodSolutions.value.length) {

                        selectedUnderstoodSolutionIds.value = [];

                    } else {

                        selectedUnderstoodSolutionIds.value = understoodSolutions.value.map(s => s.solution_id);

                    }

                };



                const toggleUnderstoodSolutionSelection = (solutionId) => {

                    const idx = selectedUnderstoodSolutionIds.value.indexOf(solutionId);

                    if (idx >= 0) {

                        selectedUnderstoodSolutionIds.value.splice(idx, 1);

                    } else {

                        selectedUnderstoodSolutionIds.value.push(solutionId);

                    }

                };



                const batchDeleteUnderstoodSolutions = async () => {

                    if (!confirm(`确定要删除选中的 ${selectedUnderstoodSolutionIds.value.length} 个方案吗？相关文档状态将回退到未理解状态。`)) return;

                    try {

                        const response = await fetch('/api/solution/batch_delete_with_rollback', {

                            method: 'POST',

                            headers: {

                                'Content-Type': 'application/json'

                            },

                            body: JSON.stringify({ solution_ids: selectedUnderstoodSolutionIds.value })

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('删除成功', data.message);

                            selectedUnderstoodSolutionIds.value = [];

                            loadUnderstoodSolutions();

                            loadPendingDocuments();

                        } else {

                            showToast('删除失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('批量删除方案失败:', error);

                        showToast('删除失败', '网络请求失败', 'error');

                    }

                };

                const handleStructuredDocumentSelect = (event) => {

                    const files = event.target.files;

                    if (files) {

                        Array.from(files).forEach(file => {

                            const reader = new FileReader();

                            reader.onload = (e) => {

                                structuredSolutionForm.uploadedDocuments.push({

                                    file_name: file.name,

                                    file_content: e.target.result,

                                    format: file.name.split('.').pop().toLowerCase(),

                                    size: file.size,

                                    version: '1.0',

                                    document_type: structuredSolutionForm.uploadedDocuments.length === 0 ? 'main' : 'attachment'

                                });

                            };

                            reader.readAsDataURL(file);

                        });

                    }

                    event.target.value = '';

                };



                const handleStructuredDocumentDrop = (event) => {

                    const files = event.dataTransfer.files;

                    if (files) {

                        Array.from(files).forEach(file => {

                            const reader = new FileReader();

                            reader.onload = (e) => {

                                structuredSolutionForm.uploadedDocuments.push({

                                    file_name: file.name,

                                    file_content: e.target.result,

                                    format: file.name.split('.').pop().toLowerCase(),

                                    size: file.size,

                                    version: '1.0',

                                    document_type: structuredSolutionForm.uploadedDocuments.length === 0 ? 'main' : 'attachment'

                                });

                            };

                            reader.readAsDataURL(file);

                        });

                    }

                };



                const saveStructuredSolution = async () => {

                    if (!structuredSolutionForm.solution_id || !structuredSolutionForm.name) {

                        showToast('验证失败', '方案ID和名称为必填项', 'error');

                        return;

                    }



                    const formData = new FormData();

                    formData.append('solution_id', structuredSolutionForm.solution_id);

                    formData.append('name', structuredSolutionForm.name);

                    formData.append('version', structuredSolutionForm.version);

                    formData.append('status', structuredSolutionForm.status);

                    formData.append('priority', structuredSolutionForm.priority);

                    formData.append('purpose', structuredSolutionForm.purpose);

                    formData.append('objectives', JSON.stringify(structuredSolutionForm.objectives));

                    formData.append('initiatives', JSON.stringify(structuredSolutionForm.initiatives));

                    formData.append('working_mechanism', structuredSolutionForm.working_mechanism);

                    formData.append('organization', JSON.stringify(structuredSolutionForm.organization));

                    formData.append('personnel', JSON.stringify(structuredSolutionForm.personnel));

                    formData.append('roles', JSON.stringify(structuredSolutionForm.roles));

                    formData.append('work_content', structuredSolutionForm.work_content);

                    formData.append('constraints', JSON.stringify(structuredSolutionForm.constraints));

                    formData.append('risks', JSON.stringify(structuredSolutionForm.risks));

                    formData.append('issues', JSON.stringify(structuredSolutionForm.issues));

                    formData.append('other_notes', structuredSolutionForm.other_notes);

                    formData.append('tags', JSON.stringify(structuredSolutionForm.tags));

                    formData.append('description', structuredSolutionForm.description);

                    formData.append('owner', structuredSolutionForm.owner);

                    formData.append('created_by', structuredSolutionForm.created_by);

                    formData.append('effective_date', structuredSolutionForm.effective_date);

                    formData.append('expiry_date', structuredSolutionForm.expiry_date);



                    structuredSolutionForm.uploadedDocuments.forEach((doc, index) => {

                        formData.append(`documents[${index}][file_name]`, doc.file_name);

                        formData.append(`documents[${index}][file_content]`, doc.file_content);

                        formData.append(`documents[${index}][format]`, doc.format);

                        formData.append(`documents[${index}][size]`, doc.size);

                        formData.append(`documents[${index}][version]`, doc.version);

                        formData.append(`documents[${index}][document_type]`, doc.document_type);

                    });



                    try {

                        const response = await fetch('/api/solution/upload', {

                            method: 'POST',

                            body: formData

                        });

                        const data = await response.json();

                        if (data.success) {

                            showToast('保存成功', `方案 [${structuredSolutionForm.name}] 已保存`);

                            showStructuredSolutionModal.value = false;

                            Object.assign(structuredSolutionForm, {

                                solution_id: '',

                                name: '',

                                version: '1.0',

                                status: 'draft',

                                priority: 'medium',

                                purpose: '',

                                objectives: [],

                                initiatives: [],

                                working_mechanism: '',

                                organization: [],

                                personnel: [],

                                roles: [],

                                work_content: '',

                                constraints: [],

                                risks: [],

                                issues: [],

                                other_notes: '',

                                tags: [],

                                description: '',

                                owner: '',

                                created_by: '',

                                effective_date: '',

                                expiry_date: '',

                                uploadedDocuments: []

                            });

                            newStructuredObjective.value = '';

                            newStructuredInitiative.value = '';

                            newStructuredOrg.value = '';

                            newStructuredRole.value = '';

                            newStructuredPersonnel.value = '';

                            newStructuredRisk.value = '';

                            newStructuredIssue.value = '';

                            newStructuredConstraint.value = '';

                            newStructuredTag.value = '';

                            loadUnderstoodSolutions();

                        } else {

                            showToast('保存失败', data.message, 'error');

                        }

                    } catch (error) {

                        console.error('保存方案失败:', error);

                        showToast('保存失败', '网络请求失败', 'error');

                    }

                };



                loadPendingDocuments();

                loadUnderstoodSolutions();



                // 方案拆分

                const decompositionForm = reactive({

                    solution_id: '',

                    strategy: 'auto'

                });

                const decompositionResult = ref(null);



                const splitSolution = () => {

                    if (!decompositionForm.solution_id) {

                        showToast('提示', '请先选择方案', 'warning');

                        return;

                    }

                    decompositionResult.value = {

                        task_count: 12,

                        flow_group_count: 3,

                        graph_id: 'GRAPH_' + decompositionForm.solution_id

                    };

                    showToast('拆分完成', '方案已成功拆分', 'success');

                };



                // 信息展示

                const displaySolutionId = ref('');



                // 仿真管理

                const simulationForm = reactive({

                    solution_id: '',

                    manifest_id: ''

                });

                const isSimulating = ref(false);

                const simulationStatus = ref(null);

                const simulationLogs = ref([]);

                let simulationTimer = null;



                const startSimulation = () => {

                    if (!simulationForm.solution_id) {

                        showToast('提示', '请先选择方案', 'warning');

                        return;

                    }



                    isSimulating.value = true;

                    simulationStatus.value = {

                        simulation_id: 'SIM_' + simulationForm.solution_id + '_' + Date.now(),

                        status: 'running',

                        progress: 0

                    };

                    simulationLogs.value = [

                        { time: new Date().toLocaleTimeString(), level: 'info', message: '仿真启动中...' },

                        { time: new Date().toLocaleTimeString(), level: 'info', message: '加载方案配置...' },

                        { time: new Date().toLocaleTimeString(), level: 'info', message: '初始化仿真环境...' }

                    ];



                    showToast('仿真启动', '仿真已开始运行', 'success');



                    // 模拟进度更新

                    simulationTimer = setInterval(() => {

                        if (simulationStatus.value.progress < 100) {

                            simulationStatus.value.progress += Math.random() * 15;

                            if (simulationStatus.value.progress > 100) {

                                simulationStatus.value.progress = 100;

                                simulationStatus.value.status = 'completed';

                                isSimulating.value = false;

                                clearInterval(simulationTimer);

                                simulationLogs.value.push({

                                    time: new Date().toLocaleTimeString(),

                                    level: 'info',

                                    message: '仿真完成！'

                                });

                                showToast('仿真完成', '仿真已成功完成', 'success');

                            } else {

                                simulationLogs.value.push({

                                    time: new Date().toLocaleTimeString(),

                                    level: 'info',

                                    message: `仿真进行中... 进度: ${Math.floor(simulationStatus.value.progress)}%`

                                });

                            }

                        }

                    }, 2000);

                };



                const stopSimulation = () => {

                    if (simulationTimer) {

                        clearInterval(simulationTimer);

                    }

                    isSimulating.value = false;

                    if (simulationStatus.value) {

                        simulationStatus.value.status = 'stopped';

                    }

                    simulationLogs.value.push({

                        time: new Date().toLocaleTimeString(),

                        level: 'warn',

                        message: '仿真已手动停止'

                    });

                    showToast('仿真停止', '仿真已停止', 'warning');

                };



                // 评估管理

                const evaluationStep = ref(0);

                const evaluationForm = reactive({

                    solution_id: '',

                    evaluation_id: '',

                    selected_agents: [],

                    selected_indices: [],

                    use_simulation_log: false,

                    simulation_id: ''

                });



                const availableIndices = ref([

                    { index_id: 'IDX_COMP_001', name: '目标完整性', description: '评估方案目标的完整性' },

                    { index_id: 'IDX_COMP_002', name: '举措完整性', description: '评估方案举措的完整性' },

                    { index_id: 'IDX_COMP_003', name: '资源完整性', description: '评估方案资源的完整性' },

                    { index_id: 'IDX_RAT_001', name: '目标合理性', description: '评估方案目标的合理性' },

                    { index_id: 'IDX_RAT_002', name: '举措合理性', description: '评估方案举措的合理性' },

                    { index_id: 'IDX_SIM_001', name: '仿真结果分析', description: '基于仿真结果的分析评估' }

                ]);



                const availableAgents = ref([

                    { agent_id: 'COMP_001', agent_name: '完整性评估Agent', index_ids: ['IDX_COMP_001', 'IDX_COMP_002', 'IDX_COMP_003'] },

                    { agent_id: 'RAT_001', agent_name: '合理性评估Agent', index_ids: ['IDX_RAT_001', 'IDX_RAT_002'] },

                    { agent_id: 'SIM_001', agent_name: '仿真分析Agent', index_ids: ['IDX_SIM_001'] }

                ]);



                const evaluationResult = reactive({

                    evaluation_id: '',

                    solution_id: '',

                    status: 'pending',

                    overall_score: null,

                    agent_results: [],

                    index_scores: [],

                    recommendations: [],

                    start_time: null,

                    end_time: null

                });



                const toggleIndex = (indexId) => {

                    const idx = evaluationForm.selected_indices.indexOf(indexId);

                    if (idx >= 0) {

                        evaluationForm.selected_indices.splice(idx, 1);

                    } else {

                        evaluationForm.selected_indices.push(indexId);

                    }

                };



                const isAgentSelected = (agentId) => {

                    return evaluationForm.selected_agents.some(a => a.agent_id === agentId);

                };



                const toggleAgent = (agent) => {

                    const idx = evaluationForm.selected_agents.findIndex(a => a.agent_id === agent.agent_id);

                    if (idx >= 0) {

                        evaluationForm.selected_agents.splice(idx, 1);

                    } else {

                        evaluationForm.selected_agents.push({

                            agent_id: agent.agent_id,

                            agent_name: agent.agent_name,

                            index_ids: agent.index_ids,

                            is_selected: true

                        });

                    }

                };



                const canStartEvaluation = computed(() => {

                    return evaluationForm.solution_id &&

                           evaluationForm.evaluation_id &&

                           evaluationForm.selected_indices.length > 0 &&

                           evaluationForm.selected_agents.length > 0;

                });



                let evaluationTimer = null;



                const startEvaluation = () => {

                    evaluationStep.value = 1;

                    Object.assign(evaluationResult, {

                        evaluation_id: evaluationForm.evaluation_id,

                        solution_id: evaluationForm.solution_id,

                        status: 'running',

                        overall_score: null,

                        agent_results: [],

                        index_scores: [],

                        recommendations: [],

                        start_time: new Date()

                    });



                    showToast('评估启动', '评估已开始运行', 'success');



                    // 模拟评估过程

                    evaluationTimer = setTimeout(() => {

                        Object.assign(evaluationResult, {

                            status: 'completed',

                            overall_score: 87.5,

                            agent_results: [

                                { agent_name: '完整性评估Agent', score: 90, conclusion: '方案目标、举措和资源描述完整' },

                                { agent_name: '合理性评估Agent', score: 85, conclusion: '方案整体合理，部分细节可优化' }

                            ],

                            index_scores: [

                                { index_name: '目标完整性', score: 92 },

                                { index_name: '举措完整性', score: 88 },

                                { index_name: '目标合理性', score: 85 },

                                { index_name: '举措合理性', score: 83 }

                            ],

                            recommendations: [

                                '建议补充更详细的资源分配计划',

                                '方案目标可以进一步量化',

                                '建议增加风险应对措施的细节描述'

                            ],

                            end_time: new Date()

                        });

                        showToast('评估完成', '评估结果已生成', 'success');

                    }, 5000);

                };



                const abortEvaluation = () => {

                    if (evaluationTimer) {

                        clearTimeout(evaluationTimer);

                    }

                    evaluationResult.status = 'aborted';

                    evaluationResult.end_time = new Date();

                    showToast('评估中止', '评估已中止', 'warning');

                };



                // ========== 知识管理 ==========



                // 知识库列表

                const knowledgeBases = ref([

                    { id: 'evaluation', name: '评价指标库', description: '评估相关的知识条目' },

                    { id: 'decomposition', name: '方案拆解库', description: '方案拆解相关的知识条目' },

                    { id: 'simulation', name: '仿真知识库', description: '仿真相关的知识条目' },

                    { id: 'other', name: '其他知识库', description: '其他类型的知识条目' }

                ]);



                // 当前选中的知识库（默认选中评价指标库）

                const selectedKnowledgeBase = ref('evaluation');



                // 知识条目列表

                const knowledgeList = ref([]);



                // 搜索相关

                const knowledgeSearchQuery = ref('');

                const isSearching = ref(false);



                // 分页相关

                const knowledgePage = ref(1);

                const knowledgePageSize = ref(10);

                const knowledgeTotal = ref(0);

                

                // 选中的知识ID列表（用于批量删除）

                const selectedKnowledgeIds = ref([]);

                

                // 弹窗控制

                const showDetailModal = ref(false);

                const showEditModal = ref(false);

                const showKnowledgeUploadModal = ref(false);

                

                // 知识详情

                const knowledgeDetail = ref({});

                

                // 编辑表单

                const editForm = reactive({

                    knowledge_id: '',

                    title: '',

                    summary: '',

                    content: '',

                    tags: [],

                    category: ''

                });

                const newEditTag = ref('');

                

                // 上传表单

                // 上传表单（包含所有知识库类型的字段）

                const uploadForm = reactive({

                    knowledge_base: '',

                    // 评价指标库字段

                    index_id: '',

                    name: '',

                    description: '',

                    evaluation_method: '',

                    index_type: 'completeness',

                    index_level: 'level_1',

                    parent_id: '',

                    weight: 1.0,

                    score_min: 0,

                    score_max: 100,

                    agent_ids: [],

                    // 方案拆解库字段

                    task_id: '',

                    task_name: '',

                    content: '',

                    execute_role: '',

                    expected_start_time: '',

                    expected_end_time: '',

                    resource_consumption: 0,

                    priority: 'medium',

                    output_target_role: '',

                    task_type: 'normal',

                    // 仿真知识库和其他知识库字段

                    knowledge_id: '',

                    title: '',

                    summary: '',

                    simulation_type: 'normal',

                    tags: [],

                    category: 'evaluation'

                });

                const newUploadTag = ref('');

                const newAgentId = ref('');



                // 知识库切换时重置表单

                const onKnowledgeBaseChange = () => {

                    // 重置所有字段

                    uploadForm.index_id = '';

                    uploadForm.name = '';

                    uploadForm.description = '';

                    uploadForm.evaluation_method = '';

                    uploadForm.index_type = 'completeness';

                    uploadForm.index_level = 'level_1';

                    uploadForm.parent_id = '';

                    uploadForm.weight = 1.0;

                    uploadForm.score_min = 0;

                    uploadForm.score_max = 100;

                    uploadForm.agent_ids = [];

                    uploadForm.task_id = '';

                    uploadForm.task_name = '';

                    uploadForm.content = '';

                    uploadForm.execute_role = '';

                    uploadForm.expected_start_time = '';

                    uploadForm.expected_end_time = '';

                    uploadForm.resource_consumption = 0;

                    uploadForm.priority = 'medium';

                    uploadForm.output_target_role = '';

                    uploadForm.task_type = 'normal';

                    uploadForm.knowledge_id = '';

                    uploadForm.title = '';

                    uploadForm.summary = '';

                    uploadForm.simulation_type = 'normal';

                    uploadForm.tags = [];

                    uploadForm.category = uploadForm.knowledge_base;

                    newUploadTag.value = '';

                    newAgentId.value = '';

                };



                // 验证是否可以上传

                const canUploadKnowledge = computed(() => {

                    if (!uploadForm.knowledge_base) return false;



                    // 评价指标库验证

                    if (uploadForm.knowledge_base === 'evaluation') {

                        return uploadForm.index_id && uploadForm.name && uploadForm.description && uploadForm.evaluation_method;

                    }



                    // 方案拆解库验证

                    if (uploadForm.knowledge_base === 'decomposition') {

                        return uploadForm.task_id && uploadForm.task_name && uploadForm.content && uploadForm.execute_role && uploadForm.expected_start_time && uploadForm.expected_end_time;

                    }



                    // 仿真知识库和其他知识库验证

                    if (uploadForm.knowledge_base === 'simulation' || uploadForm.knowledge_base === 'other') {

                        return uploadForm.knowledge_id && uploadForm.title && uploadForm.summary && uploadForm.content;

                    }



                    return false;

                });

                

                // 选择知识库

                const selectKnowledgeBase = async (kbId) => {

                    selectedKnowledgeBase.value = kbId;

                    knowledgePage.value = 1;

                    selectedKnowledgeIds.value = [];

                    knowledgeSearchQuery.value = '';

                    isSearching.value = false;

                    await loadKnowledgeList();

                };



                // 加载知识列表

                const loadKnowledgeList = async () => {

                    try {

                        // 构建URL参数

                        let url = `/api/knowledge/list?category=${selectedKnowledgeBase.value}&page=${knowledgePage.value}&pageSize=${knowledgePageSize.value}`;



                        const response = await fetch(url);

                        const data = await response.json();



                        if (data.success) {

                            // 如果有搜索关键词，进行客户端过滤

                            if (knowledgeSearchQuery.value && knowledgeSearchQuery.value.trim()) {

                                const query = knowledgeSearchQuery.value.toLowerCase();

                                const allItems = data.data.items || [];

                                const filteredItems = allItems.filter(item =>

                                    item.title.toLowerCase().includes(query) ||

                                    item.summary.toLowerCase().includes(query) ||

                                    item.content.toLowerCase().includes(query) ||

                                    (item.tags && item.tags.some(tag => tag.toLowerCase().includes(query)))

                                );

                                knowledgeList.value = filteredItems;

                                knowledgeTotal.value = data.data.total;

                            } else {

                                knowledgeList.value = data.data.items || [];

                                knowledgeTotal.value = data.data.total || 0;

                            }

                        } else {

                            showToast('加载失败', data.message || '获取知识列表失败', 'error');

                        }

                    } catch (error) {

                        console.error('加载知识列表失败:', error);

                        // 如果API不存在，使用模拟数据

                        const mockData = [

                            {

                                knowledge_id: 'KNOW_EVAL_001',

                                title: 'SMART原则详解',

                                summary: 'SMART原则是设定目标的五大准则',

                                content: 'SMART原则详解内容...',

                                tags: ['目标管理', 'SMART'],

                                category: 'evaluation',

                                created_at: '2026-06-20 10:00:00'

                            },

                            {

                                knowledge_id: 'KNOW_EVAL_002',

                                title: '资源需求分析方法',

                                summary: '介绍如何系统分析方案所需资源',

                                content: '资源需求分析方法内容...',

                                tags: ['资源管理', '分析'],

                                category: 'evaluation',

                                created_at: '2026-06-21 10:00:00'

                            },

                            {

                                knowledge_id: 'KNOW_EVAL_003',

                                title: '风险评估矩阵',

                                summary: '用于评估和管理项目风险的工具',

                                content: '风险评估矩阵是项目管理中的重要工具...',

                                tags: ['风险管理', '评估工具'],

                                category: 'evaluation',

                                created_at: '2026-06-22 10:00:00'

                            },

                            {

                                knowledge_id: 'KNOW_EVAL_004',

                                title: '技术可行性分析方法',

                                summary: '评估技术方案可行性的系统方法',

                                content: '技术可行性分析主要包括以下方面...',

                                tags: ['技术评估', '可行性研究'],

                                category: 'evaluation',

                                created_at: '2026-06-23 10:00:00'

                            }

                        ];



                        // 如果有搜索关键词，进行客户端过滤

                        if (knowledgeSearchQuery.value && knowledgeSearchQuery.value.trim()) {

                            const query = knowledgeSearchQuery.value.toLowerCase();

                            const filteredItems = mockData.filter(item =>

                                item.title.toLowerCase().includes(query) ||

                                item.summary.toLowerCase().includes(query) ||

                                item.content.toLowerCase().includes(query) ||

                                (item.tags && item.tags.some(tag => tag.toLowerCase().includes(query)))

                            );

                            knowledgeList.value = filteredItems;

                            knowledgeTotal.value = filteredItems.length;

                        } else {

                            knowledgeList.value = mockData;

                            knowledgeTotal.value = mockData.length;

                        }

                    }

                };



                // 上一页

                const prevKnowledgePage = () => {

                    if (knowledgePage.value > 1) {

                        knowledgePage.value--;

                        loadKnowledgeList();

                    }

                };



                // 下一页

                const nextKnowledgePage = () => {

                    const maxPage = Math.ceil(knowledgeTotal.value / knowledgePageSize.value);

                    if (knowledgePage.value < maxPage) {

                        knowledgePage.value++;

                        loadKnowledgeList();

                    }

                };



                // 搜索知识

                const searchKnowledge = async () => {

                    knowledgePage.value = 1;

                    isSearching.value = true;

                    await loadKnowledgeList();

                    if (knowledgeSearchQuery.value) {

                        showToast('搜索完成', `找到 ${knowledgeTotal.value} 条相关知识`, 'success');

                    }

                };



                // 清除搜索

                const clearSearch = async () => {

                    knowledgeSearchQuery.value = '';

                    isSearching.value = false;

                    knowledgePage.value = 1;

                    await loadKnowledgeList();

                    showToast('已清除', '已清除搜索条件', 'success');

                };



                // 获取知识库名称

                const getKnowledgeBaseName = (kbId) => {

                    const kb = knowledgeBases.value.find(k => k.id === kbId);

                    return kb ? kb.name : kbId;

                };



                // 获取指标类型名称

                const getIndexTypeName = (type) => {

                    const typeMap = {

                        'completeness': '完整性',

                        'rationality': '合理性',

                        'feasibility': '可行性',

                        'risk': '风险',

                        'efficiency': '效率',

                        'compliance': '合规性',

                        'strategy': '战略',

                        'resource': '资源',

                        'benefit': '收益',

                        'other': '其他'

                    };

                    return typeMap[type] || type;

                };



                // 获取指标层级名称

                const getIndexLevelName = (level) => {

                    const levelMap = {

                        'level_1': '一级指标',

                        'level_2': '二级指标',

                        'level_3': '三级指标',

                        'level_4': '四级指标'

                    };

                    return levelMap[level] || level;

                };



                // 获取优先级名称

                const getPriorityName = (priority) => {

                    const priorityMap = {

                        'high': '高',

                        'medium': '中',

                        'low': '低'

                    };

                    return priorityMap[priority] || priority;

                };



                // 获取任务类型名称

                const getTaskTypeName = (type) => {

                    const typeMap = {

                        'normal': '普通任务',

                        'start': '起始任务',

                        'end': '结束任务',

                        'halt': '暂停任务'

                    };

                    return typeMap[type] || type;

                };



                // 获取仿真场景类型名称

                const getSimulationTypeName = (type) => {

                    const typeMap = {

                        'normal': '正常场景',

                        'abnormal': '异常场景',

                        'boundary': '边界场景',

                        'concurrent': '并发场景',

                        'timing': '时序场景'

                    };

                    return typeMap[type] || type;

                };

                

                // 切换知识选择

                const toggleKnowledgeSelection = (knowledgeId) => {

                    const idx = selectedKnowledgeIds.value.indexOf(knowledgeId);

                    if (idx >= 0) {

                        selectedKnowledgeIds.value.splice(idx, 1);

                    } else {

                        selectedKnowledgeIds.value.push(knowledgeId);

                    }

                };

                

                // 查看知识详情

                const viewKnowledgeDetail = async (item) => {

                    try {

                        const response = await fetch(`/api/knowledge/detail?knowledge_id=${item.knowledge_id}`);

                        const data = await response.json();

                        

                        if (data.success) {

                            knowledgeDetail.value = data.data;

                        } else {

                            knowledgeDetail.value = item;

                        }

                    } catch (error) {

                        console.error('获取知识详情失败:', error);

                        knowledgeDetail.value = item;

                    }

                    showDetailModal.value = true;

                };

                

                // 编辑知识

                const editKnowledgeItem = (item) => {

                    Object.assign(editForm, {

                        knowledge_id: item.knowledge_id,

                        title: item.title,

                        summary: item.summary,

                        content: item.content,

                        tags: [...(item.tags || [])],

                        category: item.category || selectedKnowledgeBase.value

                    });

                    showEditModal.value = true;

                };

                

                // 保存编辑

                const saveKnowledgeEdit = async () => {

                    if (!editForm.title || !editForm.summary || !editForm.content) {

                        showToast('验证失败', '标题、摘要和内容为必填项', 'error');

                        return;

                    }

                    

                    try {

                        const response = await fetch('/api/knowledge/update', {

                            method: 'POST',

                            headers: { 'Content-Type': 'application/json' },

                            body: JSON.stringify(editForm)

                        });

                        

                        const data = await response.json();

                        

                        if (data.success) {

                            showToast('保存成功', '知识已更新', 'success');

                            showEditModal.value = false;

                            await loadKnowledgeList();

                        } else {

                            showToast('保存失败', data.message || '更新知识失败', 'error');

                        }

                    } catch (error) {

                        console.error('保存知识失败:', error);

                        showToast('保存失败', '网络请求失败', 'error');

                    }

                };

                

                // 批量删除知识

                const batchDeleteKnowledge = async () => {

                    if (selectedKnowledgeIds.value.length === 0) {

                        showToast('提示', '请先选择要删除的知识', 'warning');

                        return;

                    }

                    

                    if (!confirm(`确定要删除选中的 ${selectedKnowledgeIds.value.length} 条知识吗？`)) {

                        return;

                    }

                    

                    try {

                        const response = await fetch('/api/knowledge/delete', {

                            method: 'POST',

                            headers: { 'Content-Type': 'application/json' },

                            body: JSON.stringify({ knowledge_ids: selectedKnowledgeIds.value })

                        });

                        

                        const data = await response.json();

                        

                        if (data.success) {

                            showToast('删除成功', `已删除 ${selectedKnowledgeIds.value.length} 条知识`, 'success');

                            selectedKnowledgeIds.value = [];

                            await loadKnowledgeList();

                        } else {

                            showToast('删除失败', data.message || '删除知识失败', 'error');

                        }

                    } catch (error) {

                        console.error('删除知识失败:', error);

                        showToast('删除失败', '网络请求失败', 'error');

                    }

                };

                

                // 上传知识

                // 上传知识

                const uploadKnowledge = async () => {

                    // 根据知识库类型验证必填字段

                    if (!uploadForm.knowledge_base) {

                        showToast('验证失败', '请选择知识库', 'error');

                        return;

                    }



                    let requestData = {};



                    // 根据知识库类型构建不同的请求数据

                    if (uploadForm.knowledge_base === 'evaluation') {

                        // 评价指标库

                        if (!uploadForm.index_id || !uploadForm.name || !uploadForm.description || !uploadForm.evaluation_method) {

                            showToast('验证失败', '指标ID、名称、说明和评价方法为必填项', 'error');

                            return;

                        }

                        requestData = {

                            knowledge_base: 'evaluation',

                            index_id: uploadForm.index_id,

                            name: uploadForm.name,

                            description: uploadForm.description,

                            evaluation_method: uploadForm.evaluation_method,

                            index_type: uploadForm.index_type,

                            index_level: uploadForm.index_level,

                            parent_id: uploadForm.parent_id || null,

                            weight: uploadForm.weight,

                            score_range: [uploadForm.score_min, uploadForm.score_max],

                            agent_ids: uploadForm.agent_ids,

                            is_active: true

                        };

                    } else if (uploadForm.knowledge_base === 'decomposition') {

                        // 方案拆解库

                        if (!uploadForm.task_id || !uploadForm.task_name || !uploadForm.content || !uploadForm.execute_role || !uploadForm.expected_start_time || !uploadForm.expected_end_time) {

                            showToast('验证失败', '任务ID、名称、内容、执行角色、期望开始时间和期望结束时间为必填项', 'error');

                            return;

                        }

                        requestData = {

                            knowledge_base: 'decomposition',

                            task_id: uploadForm.task_id,

                            task_name: uploadForm.task_name,

                            content: uploadForm.content,

                            execute_role: uploadForm.execute_role,

                            expected_start_time: uploadForm.expected_start_time,

                            expected_end_time: uploadForm.expected_end_time,

                            resource_consumption: uploadForm.resource_consumption,

                            priority: uploadForm.priority,

                            output_target_role: uploadForm.output_target_role,

                            task_type: uploadForm.task_type,

                            is_completed: false

                        };

                    } else if (uploadForm.knowledge_base === 'simulation') {

                        // 仿真知识库

                        if (!uploadForm.knowledge_id || !uploadForm.title || !uploadForm.summary || !uploadForm.content) {

                            showToast('验证失败', '知识ID、标题、摘要和内容为必填项', 'error');

                            return;

                        }

                        requestData = {

                            knowledge_base: 'simulation',

                            knowledge_id: uploadForm.knowledge_id,

                            title: uploadForm.title,

                            summary: uploadForm.summary,

                            content: uploadForm.content,

                            simulation_type: uploadForm.simulation_type,

                            tags: uploadForm.tags,

                            category: 'simulation',

                            index_ids: [],

                            is_active: true

                        };

                    } else if (uploadForm.knowledge_base === 'other') {

                        // 其他知识库

                        if (!uploadForm.knowledge_id || !uploadForm.title || !uploadForm.summary || !uploadForm.content) {

                            showToast('验证失败', '知识ID、标题、摘要和内容为必填项', 'error');

                            return;

                        }

                        requestData = {

                            knowledge_base: 'other',

                            knowledge_id: uploadForm.knowledge_id,

                            title: uploadForm.title,

                            summary: uploadForm.summary,

                            content: uploadForm.content,

                            tags: uploadForm.tags,

                            category: 'other',

                            index_ids: [],

                            is_active: true

                        };

                    }



                    try {

                        const response = await fetch('/api/knowledge/add', {

                            method: 'POST',

                            headers: { 'Content-Type': 'application/json' },

                            body: JSON.stringify(requestData)

                        });



                        const data = await response.json();



                        if (data.success) {

                            showToast('上传成功', '知识已添加到知识库', 'success');

                            showKnowledgeUploadModal.value = false;

                            // 重置上传表单

                            onKnowledgeBaseChange();

                            // 如果上传到了当前选中的知识库，刷新列表

                            if (uploadForm.knowledge_base === selectedKnowledgeBase.value) {

                                await loadKnowledgeList();

                            }

                        } else {

                            showToast('上传失败', data.message || '添加知识失败', 'error');

                        }

                    } catch (error) {

                        console.error('上传知识失败:', error);

                        showToast('上传失败', '网络请求失败', 'error');

                    }

                };

                

                // 初始化加载知识列表

                loadKnowledgeList();



                return {

                    currentView,

                    navItems,

                    switchView,

                    toasts,

                    showToast,



                    // 方案管理

                    solutionList,

                    solutionTotal,

                    solutionPage,

                    solutionPageSize,

                    solutionSearchQuery,

                    selectedSolutionIds,

                    showSolutionDetailModal,

                    showUploadModal,

                    solutionDetail,

                    solutionUploadForm,

                    canUploadSolution,

                    loadSolutionList,

                    searchSolutions,

                    clearSolutionSearch,

                    prevSolutionPage,

                    nextSolutionPage,

                    toggleSelectAllSolutions,

                    toggleSolutionSelection,

                    viewSolutionDetail,

                    deleteSolution,

                    batchDeleteSolutions,

                    handleDocumentSelect,

                    handleDocumentDrop,

                    openFilePicker,

                    uploadSolution,

                    downloadSolutionDocument,

                    getSolutionStatusName,

                    getSolutionStatusClass,

                    getSolutionPriorityName,

                    getDocumentTypeName,

                    getDocumentStatusName,

                    getDocumentStatusClass,

                    formatFileSize,

                    formatDateTime,



                    // 方案理解

                    pendingDocs,

                    pendingDocsTotal,

                    pendingDocsPage,

                    pendingDocsPageSize,

                    understoodSolutions,

                    understoodSolutionsTotal,

                    understoodSolutionsPage,

                    understoodSolutionsPageSize,

                    understoodSolutionsSearchQuery,

                    selectedUnderstoodSolutionIds,

                    showPendingDocDetailModal,

                    showUnderstoodSolutionDetailModal,

                    showStructuredSolutionModal,

                    pendingDocDetail,

                    understoodSolutionDetail,

                    structuredSolutionForm,

                    newStructuredObjective,

                    newStructuredInitiative,

                    newStructuredOrg,

                    newStructuredRole,

                    newStructuredPersonnel,

                    newStructuredRisk,

                    newStructuredIssue,

                    newStructuredConstraint,

                    newStructuredTag,

                    loadPendingDocuments,

                    loadUnderstoodSolutions,

                    searchUnderstoodSolutions,

                    clearUnderstoodSolutionSearch,

                    viewPendingDocDetail,

                    viewUnderstoodSolutionDetail,

                    startConversion,

                    updateUnderstoodSolution,

                    toggleSelectAllUnderstoodSolutions,

                    toggleUnderstoodSolutionSelection,

                    batchDeleteUnderstoodSolutions,

                    handleStructuredDocumentSelect,

                    handleStructuredDocumentDrop,

                    saveStructuredSolution,



                    // 方案拆分

                    decompositionForm,

                    decompositionResult,

                    splitSolution,



                    // 信息展示

                    displaySolutionId,



                    // 仿真管理

                    simulationForm,

                    isSimulating,

                    simulationStatus,

                    simulationLogs,

                    startSimulation,

                    stopSimulation,



                    // 评估管理

                    evaluationStep,

                    evaluationForm,

                    availableIndices,

                    availableAgents,

                    evaluationResult,

                    toggleIndex,

                    isAgentSelected,

                    toggleAgent,

                    canStartEvaluation,

                    startEvaluation,

                    abortEvaluation,



                    // 知识管理

                    knowledgeBases,

                    selectedKnowledgeBase,

                    knowledgeList,

                    knowledgeSearchQuery,

                    knowledgePage,

                    knowledgePageSize,

                    knowledgeTotal,

                    selectedKnowledgeIds,

                    showDetailModal,

                    showEditModal,

                    showKnowledgeUploadModal,

                    knowledgeDetail,

                    editForm,

                    newEditTag,

                    uploadForm,

                    newUploadTag,

                    newAgentId,

                    onKnowledgeBaseChange,

                    canUploadKnowledge,

                    selectKnowledgeBase,

                    loadKnowledgeList,

                    prevKnowledgePage,

                    nextKnowledgePage,

                    searchKnowledge,

                    clearSearch,

                    getKnowledgeBaseName,

                    getIndexTypeName,

                    getIndexLevelName,

                    getPriorityName,

                    getTaskTypeName,

                    getSimulationTypeName,

                    toggleKnowledgeSelection,

                    viewKnowledgeDetail,

                    editKnowledgeItem,

                    saveKnowledgeEdit,

                    batchDeleteKnowledge,

                    uploadKnowledge

                };

            }

        }).mount('#app');

