const { createApp, ref, computed, reactive, onMounted } = Vue;
const C = (typeof window !== 'undefined' && window.SP_Common) || {};
const {
  safeJsonParse, safeLen, splitTags, formatDateTime, showToast, toasts
} = C;

createApp({
  setup() {
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

    const index_scores = computed(() => evaluationResult.index_scores);

    const toggleIndex = (indexId) => {
      const idx = evaluationForm.selected_indices.indexOf(indexId);
      if (idx >= 0) { evaluationForm.selected_indices.splice(idx, 1); }
      else { evaluationForm.selected_indices.push(indexId); }
    };

    const isAgentSelected = (agentId) => {
      return evaluationForm.selected_agents.some(a => a.agent_id === agentId);
    };

    const toggleAgent = (agent) => {
      const idx = evaluationForm.selected_agents.findIndex(a => a.agent_id === agent.agent_id);
      if (idx >= 0) { evaluationForm.selected_agents.splice(idx, 1); }
      else {
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
      if (evaluationTimer) { clearTimeout(evaluationTimer); }
      evaluationResult.status = 'aborted';
      evaluationResult.end_time = new Date();
      showToast('评估中止', '评估已中止', 'warning');
    };

    return {
      toasts, showToast,
      safeJsonParse, safeLen, splitTags, formatDateTime,

      evaluationStep, evaluationForm,
      availableIndices, availableAgents, index_scores,
      toggleIndex, isAgentSelected, toggleAgent,
      canStartEvaluation, startEvaluation, abortEvaluation
    };
  }
}).mount('#app');
