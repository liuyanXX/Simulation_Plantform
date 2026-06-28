const { createApp, ref, computed, reactive, onMounted } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
  safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
  showToast, toasts,
  getSimulationTypeName, getSolutionStatusName, getSolutionStatusClass,
  getSolutionPriorityName, getDocumentTypeName
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

    const structuredSolutions = computed(() => (solutionList.value || []).map(s => ({
      solution_id: s.solution_id || s.document_id,
      name: s.name || s.document_name || s.solution_id || s.document_id
    })));

    const simulations = ref([]);
    const simulationCurrentPage = ref(1);
    const simulationPageSize = ref(10);
    const simulationTotalPages = computed(() => {
      const ps = simulationPageSize.value || 10;
      return Math.max(1, Math.ceil((simulations.value || []).length / ps));
    });
    const pagedSimulations = computed(() => {
      const ps = simulationPageSize.value || 10;
      const p = simulationCurrentPage.value;
      return (simulations.value || []).slice((p - 1) * ps, p * ps);
    });

    const showCreateSimulationModal = ref(false);
    const showSimulationDetail = ref(false);
    const newSimulation = reactive({
      name: '', type: 'mission_rehearsal', solution_id: '', description: ''
    });
    const currentSimulation = reactive({});

    const simulationForm = reactive({ solution_id: '', manifest_id: '' });
    const isSimulating = ref(false);
    const simulationStatus = ref(null);
    const simulationLogs = ref([]);
    let simulationTimer = null;
    const simulationRunning = isSimulating;

    const viewSimulationDetail = (id) => {
      const sim = (simulations.value || []).find(s => String(s.sim_id) === String(id));
      Object.assign(currentSimulation, sim || {});
      showSimulationDetail.value = true;
    };

    const createSimulation = async () => {
      if (!newSimulation.solution_id) {
        showToast('提示', '请先选择方案', 'warning');
        return;
      }
      const sim = {
        sim_id: 'SIM_' + Date.now(),
        name: newSimulation.name || '未命名仿真',
        type: newSimulation.type,
        solution_id: newSimulation.solution_id,
        description: newSimulation.description || '',
        status: 'pending',
        progress: 0,
        created_at: new Date().toISOString()
      };
      simulations.value = simulations.value || [];
      simulations.value.unshift(sim);
      showCreateSimulationModal.value = false;
      Object.assign(newSimulation, {
        name: '', type: 'mission_rehearsal', solution_id: '', description: ''
      });
      showToast('仿真创建', '仿真已创建，可开始运行', 'success');
    };

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
              level: 'info', message: '仿真完成！'
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
      if (simulationTimer) { clearInterval(simulationTimer); }
      isSimulating.value = false;
      if (simulationStatus.value) { simulationStatus.value.status = 'stopped'; }
      simulationLogs.value.push({
        time: new Date().toLocaleTimeString(), level: 'warn',
        message: '仿真已手动停止'
      });
      showToast('仿真停止', '仿真已停止', 'warning');
    };

    onMounted(() => { loadSolutionList(); });

    return {
      toasts, showToast,
      safeJsonParse, safeLen, splitTags, formatDateTime, formatFileSize,
      getSimulationTypeName, getSolutionStatusName, getSolutionStatusClass,
      getSolutionPriorityName, getDocumentTypeName,

      solutionList, structuredSolutions, loadSolutionList,

      simulations, pagedSimulations, simulationCurrentPage, simulationPageSize, simulationTotalPages,

      simulationForm, simulationStatus, simulationLogs,
      isSimulating, simulationRunning, simulationTimer: { value: null },

      showCreateSimulationModal, showSimulationDetail,
      newSimulation, currentSimulation,
      createSimulation, startSimulation, stopSimulation,
      viewSimulationDetail
    };
  }
}).mount('#app');
