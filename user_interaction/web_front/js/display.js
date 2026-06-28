const { createApp, ref, computed, reactive, onMounted } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
  safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
  showToast, toasts, apiFetch
} = C;

createApp({
  setup() {
    const solutionList = ref([]);
    const solutionTotal = ref(0);
    const knowledgeList = ref([]);
    const knowledgeTotal = ref(0);
    const decompositionResult = ref(null);
    const simulations = ref([]);

    const stats = reactive({
      solutionCount: 0,
      documentCount: 0,
      decompositionCount: 0,
      simulationCount: 0,
      knowledgeCount: 0
    });

    const loadSolutionList = async () => {
      try {
        const response = await fetch('/api/solution/list?page=1&page_size=1');
        const data = await response.json();
        if (data.success) {
          solutionTotal.value = data.data.total || 0;
        }
      } catch (e) {}
    };

    const loadStats = async () => {
      try {
        const response = await fetch('/api/stats');
        if (response && response.ok) {
          const data = await response.json();
          if (data && data.success && data.data) {
            Object.assign(stats, data.data);
            return;
          }
        }
      } catch (_) {}
      await loadSolutionList();
      stats.solutionCount = solutionTotal.value || 0;
      stats.documentCount = solutionTotal.value || 0;
      stats.decompositionCount = decompositionResult.value ? 1 : 0;
      stats.simulationCount = (simulations.value || []).length;
      stats.knowledgeCount = knowledgeTotal.value || 0;
    };

    onMounted(() => {
      loadStats().catch(() => {});
    });

    return {
      toasts, showToast, apiFetch,
      safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
      stats, loadStats
    };
  }
}).mount('#app');
