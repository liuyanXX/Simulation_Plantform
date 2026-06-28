const SP_Common = (() => {
  let VueLib = (typeof Vue !== 'undefined') ? Vue : null;
  const getVue = () => VueLib || Vue;

  const ref = VueLib ? VueLib.ref : (v) => Vue.ref(v);
  const reactive = VueLib ? VueLib.reactive : (v) => Vue.reactive(v);

  const safeJsonParse = (x) => {
    if (x == null) return null;
    if (typeof x !== 'string') return x;
    try { return JSON.parse(x); } catch { return null; }
  };

  const safeLen = (x) => {
    if (x == null) return 0;
    if (Array.isArray(x)) return x.length;
    if (typeof x === 'string') return x.length;
    if (typeof x === 'object') return Object.keys(x).length;
    return 0;
  };

  const splitTags = (input) => {
    if (!input) return [];
    if (Array.isArray(input)) return input.map(String);
    if (typeof input !== 'string') return [];
    return input.split(/[,，\s]+/).map(t => t.trim()).filter(Boolean);
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

  let toastId = 0;
  const toasts = ref([]);

  const showToast = (title, message, type = 'info') => {
    const id = ++toastId;
    toasts.value.push({ id, title, message, type });
    setTimeout(() => {
      if (toasts && toasts.value) {
        toasts.value = toasts.value.filter(t => t.id !== id);
      }
    }, 3000);
  };

  const removeToast = (id) => {
    if (toasts && toasts.value) {
      toasts.value = toasts.value.filter(t => t.id !== id);
    }
  };

  const openFilePicker = (inputId) => {
    const el = document.getElementById(inputId);
    if (el) { el.click(); }
    else { console.warn('openFilePicker: element not found:', inputId); }
  };

  const handleDocumentSelect = (event, form, filesKey = 'uploadedFiles') => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        if (form && Array.isArray(form[filesKey])) form[filesKey].push(file);
      });
    }
    event.target.value = '';
  };

  const handleDocumentDrop = (event, form, filesKey = 'uploadedFiles') => {
    const files = event.dataTransfer.files;
    if (files) {
      Array.from(files).forEach(file => {
        if (form && Array.isArray(form[filesKey])) form[filesKey].push(file);
      });
    }
  };

  const apiFetch = async (url, opts = {}) => {
    try {
      const res = await fetch(url, opts);
      const text = await res.text();
      let data;
      try { data = JSON.parse(text); } catch { data = text; }
      if (data && typeof data === 'object' && data.success === false) {
        showToast(data.message || '请求失败', (data.detail || ''), 'error');
      }
      return data;
    } catch (e) {
      showToast('网络错误', String(e && e.message || e), 'error');
      throw e;
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

  const getIndexLevelName = (level) => {
    const levelMap = {
      'level_1': '一级指标',
      'level_2': '二级指标',
      'level_3': '三级指标',
      'level_4': '四级指标'
    };
    return levelMap[level] || level;
  };

  const getPriorityName = (priority) => {
    const priorityMap = {
      'high': '高',
      'medium': '中',
      'low': '低'
    };
    return priorityMap[priority] || priority;
  };

  const getTaskTypeName = (type) => {
    const typeMap = {
      'normal': '普通任务',
      'start': '起始任务',
      'end': '结束任务',
      'halt': '暂停任务'
    };
    return typeMap[type] || type;
  };

  const getKnowledgeBaseName = (kbId) => {
    const kbMap = {
      'evaluation': '评价指标库',
      'decomposition': '方案拆解库',
      'simulation': '仿真知识库',
      'other': '其他知识库'
    };
    return kbMap[kbId] || kbId;
  };

  const getTagTypeOptions = () => [
    { value: 'solution', label: '方案' },
    { value: 'task', label: '任务' },
    { value: 'index', label: '指标' },
    { value: 'doc', label: '文档' }
  ];

  const publicObj = {
    safeJsonParse,
    safeLen,
    splitTags,
    formatFileSize,
    formatDateTime,
    toasts,
    showToast,
    removeToast,
    openFilePicker,
    handleDocumentSelect,
    handleDocumentDrop,
    apiFetch,
    getSolutionStatusName,
    getSolutionStatusClass,
    getSolutionPriorityName,
    getDocumentTypeName,
    getDocumentStatusName,
    getDocumentStatusClass,
    getSimulationTypeName,
    getIndexTypeName,
    getIndexLevelName,
    getPriorityName,
    getTaskTypeName,
    getKnowledgeBaseName,
    getTagTypeOptions
  };
  return publicObj;
})();