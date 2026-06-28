const { createApp, ref, computed, reactive, onMounted } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
  safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
  openFilePicker, showToast, toasts,
  getSolutionStatusName, getSolutionStatusClass, getSolutionPriorityName,
  getDocumentTypeName, getDocumentStatusName, getDocumentStatusClass
} = C;

createApp({
  setup() {
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
      solution_id: '', name: '', version: '1.0', status: 'draft', priority: 'medium',
      purpose: '', objectives: [], initiatives: [], working_mechanism: '',
      organization: [], personnel: [], roles: [], work_content: '',
      constraints: [], risks: [], issues: [], other_notes: '',
      tags: [], description: '', owner: '', created_by: '',
      effective_date: '', expiry_date: '', uploadedDocuments: []
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
        if (response.ok) { Object.assign(pendingDocDetail, item); }
        else { Object.assign(pendingDocDetail, item); }
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
        if (data.success) { Object.assign(understoodSolutionDetail, data.data); }
        else { Object.assign(understoodSolutionDetail, item); }
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
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ document_id: documentId })
        });
        const data = await response.json();
        if (data.success) {
          showToast('转换成功', `已成功理解方案: ${data.data.solution_name}`);
          loadPendingDocuments();
          loadUnderstoodSolutions();
        } else { showToast('转换失败', data.message, 'error'); }
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
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(understoodSolutionDetail)
        });
        const data = await response.json();
        if (data.success) {
          showToast('更新成功', `方案 [${understoodSolutionDetail.name}] 已更新`);
          showUnderstoodSolutionDetailModal.value = false;
          loadUnderstoodSolutions();
        } else { showToast('更新失败', data.message, 'error'); }
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
      if (idx >= 0) { selectedUnderstoodSolutionIds.value.splice(idx, 1); }
      else { selectedUnderstoodSolutionIds.value.push(solutionId); }
    };

    const batchDeleteUnderstoodSolutions = async () => {
      if (!confirm(`确定要删除选中的 ${selectedUnderstoodSolutionIds.value.length} 个方案吗？相关文档状态将回退到未理解状态。`)) return;
      try {
        const response = await fetch('/api/solution/batch_delete_with_rollback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ solution_ids: selectedUnderstoodSolutionIds.value })
        });
        const data = await response.json();
        if (data.success) {
          showToast('删除成功', data.message);
          selectedUnderstoodSolutionIds.value = [];
          loadUnderstoodSolutions();
          loadPendingDocuments();
        } else { showToast('删除失败', data.message, 'error'); }
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
              file_name: file.name, file_content: e.target.result,
              format: file.name.split('.').pop().toLowerCase(),
              size: file.size, version: '1.0',
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
              file_name: file.name, file_content: e.target.result,
              format: file.name.split('.').pop().toLowerCase(),
              size: file.size, version: '1.0',
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
        const response = await fetch('/api/solution/upload', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.success) {
          showToast('保存成功', `方案 [${structuredSolutionForm.name}] 已保存`);
          showStructuredSolutionModal.value = false;
          Object.assign(structuredSolutionForm, {
            solution_id: '', name: '', version: '1.0', status: 'draft', priority: 'medium',
            purpose: '', objectives: [], initiatives: [], working_mechanism: '',
            organization: [], personnel: [], roles: [], work_content: '',
            constraints: [], risks: [], issues: [], other_notes: '',
            tags: [], description: '', owner: '', created_by: '',
            effective_date: '', expiry_date: '', uploadedDocuments: []
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
        } else { showToast('保存失败', data.message, 'error'); }
      } catch (error) {
        console.error('保存方案失败:', error);
        showToast('保存失败', '网络请求失败', 'error');
      }
    };

    const runUnderstanding = startConversion;
    const showUnderstandingDetail = showPendingDocDetailModal;
    const currentUnderstanding = pendingDocDetail;
    const viewUnderstandingDetail = viewPendingDocDetail;
    const searchPendingDocs = () => { loadPendingDocuments(); };
    const prevPendingPage = () => { if (pendingDocsPage.value > 1) { pendingDocsPage.value--; loadPendingDocuments(); } };
    const nextPendingPage = () => {
      if (pendingDocsPage.value < Math.ceil(pendingDocsTotal.value / pendingDocsPageSize.value)) {
        pendingDocsPage.value++;
        loadPendingDocuments();
      }
    };

    let pendingPollTimer = null;

    onMounted(() => {
      loadPendingDocuments();
      loadUnderstoodSolutions();
      pendingPollTimer = setInterval(() => { loadPendingDocuments(); }, 15000);
    });

    return {
      toasts, showToast,
      safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
      getSolutionStatusName, getSolutionStatusClass, getSolutionPriorityName,
      getDocumentTypeName, getDocumentStatusName, getDocumentStatusClass,

      pendingDocuments: pendingDocs,
      pendingDocs, pendingDocsTotal, pendingDocsPage, pendingDocsPageSize,
      searchPendingDocs, prevPendingPage, nextPendingPage,
      loadPendingDocs: loadPendingDocuments, loadPendingDocuments,
      showUnderstandingDetail: showPendingDocDetailModal,
      showPendingDocDetailModal,
      currentUnderstanding: pendingDocDetail,
      pendingDocDetail,
      viewUnderstandingDetail: viewPendingDocDetail,
      viewPendingDocDetail,
      runUnderstanding: startConversion,
      runUnderstanding,
      startConversion, updateUnderstoodSolution,

      understoodSolutions, understoodSolutionsTotal,
      understoodSolutionsPage, understoodSolutionsPageSize,
      understoodSolutionsSearchQuery, selectedUnderstoodSolutionIds,
      searchUnderstoodSolutions, clearUnderstoodSolutionSearch,
      toggleSelectAllUnderstoodSolutions, toggleUnderstoodSolutionSelection,
      batchDeleteUnderstoodSolutions,
      viewUnderstoodSolutionDetail,
      showUnderstoodSolutionDetailModal,
      understoodSolutionDetail,
      showStructuredSolutionModal,
      structuredSolutionForm, handleStructuredDocumentSelect,
      handleStructuredDocumentDrop, saveStructuredSolution,
      newStructuredObjective, newStructuredInitiative, newStructuredOrg,
      newStructuredRole, newStructuredPersonnel, newStructuredRisk,
      newStructuredIssue, newStructuredConstraint, newStructuredTag,
      loadUnderstoodSolutions
    };
  }
}).mount('#app');
