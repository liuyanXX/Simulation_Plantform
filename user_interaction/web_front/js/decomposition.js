const { createApp, ref, computed, reactive, onMounted } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
  safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
  showToast, toasts,
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

    const decompositionForm = reactive({ solution_id: '', strategy: 'auto' });
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

    const solutions = solutionList;
    const pagedSolutions = computed(() => {
      const ps = solutionPageSize.value;
      const p = solutionPage.value;
      return (solutionList.value || []).slice((p - 1) * ps, p * ps);
    });
    const decompositionCurrentPage = ref(1);
    const decompositionPageSize = ref(10);
    const decompositionTotalPages = computed(() => {
      return Math.max(1, Math.ceil((decompositionForm.solution_id ? 1 : 0) / Math.max(1, decompositionPageSize.value)));
    });
    const decompositionSolutionId = ref('');
    const decompositionStrategy = ref('auto');
    const lastDecompositionBehavior = ref(null);
    const decompositionModalTitle = ref('方案拆分详情');
    const decompositionModalTab = ref('overview');
    const decompositionBehavior = decompositionResult;
    const showDecompositionModal = ref(false);
    const showDecompositionBehavior = ref(false);
    const showDecompositionResult = ref(false);
    const runDecomposition = splitSolution;
    const viewSolutionBehavior = ref(false);
    const viewSolutionResult = ref(false);

    onMounted(() => {
      loadSolutionList();
    });

    return {
      toasts, showToast,
      safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
      getSolutionStatusName, getSolutionStatusClass, getSolutionPriorityName,
      getDocumentTypeName, getDocumentStatusName, getDocumentStatusClass,

      solutionList, solutionTotal, solutionPage, solutionPageSize, solutionSearchQuery,
      loadSolutionList,

      solutions, pagedSolutions,
      decompositionForm, decompositionResult,
      splitSolution, runDecomposition,

      decompositionBehavior,
      showDecompositionModal, showDecompositionBehavior, showDecompositionResult,
      viewSolutionBehavior, viewSolutionResult,

      decompositionCurrentPage, decompositionPageSize, decompositionTotalPages,
      decompositionSolutionId, decompositionStrategy,
      lastDecompositionBehavior,
      decompositionModalTitle, decompositionModalTab
    };
  }
}).mount('#app');
