# 创建方案拆解服务
service = SolutionDecompositionService()

# 拆解方案
result = service.decompose_solution(solution)

# 保存拆解结果到数据库
if result.success:
    service.save_decomposition_result(result)
    print("拆解结果已保存到数据库")

# 从数据库加载拆解结果
loaded_result = service.load_decomposition_from_db(manifest_id="MANIFEST_SOL001")

# 单独保存操作
service.save_task(task)
service.save_flow_group(flow_group, manifest_id="MANIFEST_SOL001")
service.save_task_manifest(manifest, solution_id="SOL001")
service.save_tasks_graph_to_db(graph)

# 删除操作
service.delete_task_from_db("TASK001")
service.delete_flow_group_from_db("FLOW001")
service.delete_task_manifest_from_db("MANIFEST_SOL001")
service.delete_tasks_graph_from_db("GRAPH_SOL001")

# 查询操作
task = service.get_task_from_db("TASK001")
flow_group = service.get_flow_group_from_db("FLOW001")
manifest = service.get_task_manifest_from_db("MANIFEST_SOL001")
graph = service.get_tasks_graph_from_db("GRAPH_SOL001")

# 列表查询
all_flow_groups = service.list_flow_groups_from_db()
all_manifests = service.list_task_manifests_from_db()
all_graphs = service.list_tasks_graphs_from_db()