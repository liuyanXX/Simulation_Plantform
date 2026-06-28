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
        const response = await fetch(`/api/solution/delete_document?document_id=${documentId}`, { method: 'DELETE' });
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
          headers: { 'Content-Type': 'application/json' },
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

    const openFilePickerLocal = openFilePicker;

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
        const response = await fetch('/api/solution/upload_document', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.success) {
          showToast('上传成功', `文档 [${solutionUploadForm.document_id}] 已上传`);
          showUploadModal.value = false;
          Object.assign(solutionUploadForm, {
            document_id: '', version: '1.0', document_type: 'main',
            description: '', created_by: '', uploadedFiles: []
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

    const uploadInProgress = ref(false);

    const solutionDocuments = solutionList;
    const pagedSolutionDocuments = computed(() => {
      const ps = solutionPageSize.value;
      const p = solutionPage.value;
      return (solutionList.value || []).slice((p - 1) * ps, p * ps);
    });
    const solutionCurrentPage = solutionPage;
    const solutionTotalPages = computed(() => {
      return Math.max(1, Math.ceil((solutionTotal.value || 0) / Math.max(1, solutionPageSize.value)));
    });
    const showDocumentDetail = showSolutionDetailModal;
    const currentDocument = solutionDetail;
    const uploadDocument = uploadSolution;
    const downloadSingleFile = downloadSolutionDocument;
    const canUploadDocument = canUploadSolution;

    onMounted(() => {
      loadSolutionList();
    });

    return {
      toasts, showToast,
      safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
      getSolutionStatusName, getSolutionStatusClass, getSolutionPriorityName,
      getDocumentTypeName, getDocumentStatusName, getDocumentStatusClass,

      solutionList, solutionTotal, solutionPage, solutionPageSize,
      solutionSearchQuery, selectedSolutionIds,
      showSolutionDetailModal, showUploadModal, solutionDetail,
      solutionUploadForm, canUploadSolution,
      loadSolutionList, searchSolutions, clearSolutionSearch,
      prevSolutionPage, nextSolutionPage,
      toggleSelectAllSolutions, toggleSolutionSelection,
      viewSolutionDetail, deleteSolution, batchDeleteSolutions,
      handleDocumentSelect, handleDocumentDrop,
      openFilePicker: openFilePickerLocal,
      uploadSolution, downloadSolutionDocument,
      uploadInProgress,

      solutionDocuments, pagedSolutionDocuments, solutionCurrentPage,
      solutionTotalPages, showDocumentDetail, currentDocument,
      uploadDocument, downloadSingleFile, canUploadDocument, newUploadTag: ref('')
    };
  }
}).mount('#app');