"""任务图谱解析和生成脚本

从任务清单文件解析生成任务图谱，并导出任务流组文件。
"""
import os
from tasks_graph import TasksGraph
from task_flow_group import TaskFlowGroup

def main():
    # 1. 解析任务清单文件生成任务图谱
    manifest_file = 'task_manifest_example.json'
    print(f"正在从 {manifest_file} 解析任务清单...")
    
    try:
        graph = TasksGraph.from_task_manifest_file(manifest_file)
        print(f"任务图谱解析成功！")
        print(f"  图谱ID: {graph.graph_id}")
        print(f"  图谱名称: {graph.graph_name}")
        print(f"  任务数量: {len(graph.tasks)}")
        print(f"  开始任务数量: {len(graph.get_start_tasks())}")
        print(f"  终点任务数量: {len(graph.get_end_tasks())}")
        print(f"  路径数量: {len(graph.extract_all_paths())}")
        print(f"  是否连通: {graph.is_connected()}")
    except Exception as e:
        print(f"解析失败: {e}")
        return
    
    # 2. 生成任务图谱示例文件
    graph_output_file = 'tasks_graph_example.json'
    print(f"\n正在生成任务图谱文件 {graph_output_file}...")
    try:
        graph.save_to_file(graph_output_file)
        print(f"任务图谱文件生成成功！")
    except Exception as e:
        print(f"生成失败: {e}")
        return
    
    # 3. 根据任务图谱生成任务流组
    print(f"\n正在从任务图谱生成任务流组...")
    flow_groups = graph.split_into_flow_groups()
    print(f"生成了 {len(flow_groups)} 个任务流组")
    
    # 4. 创建输出目录
    output_dir = 'flow_groups_output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 5. 每个任务流组写入一个JSON文件
    for i, flow_group in enumerate(flow_groups):
        flow_file_name = f"{output_dir}/flow_group_{flow_group.flow_id}.json"
        print(f"正在写入任务流组文件: {flow_file_name}")
        
        try:
            with open(flow_file_name, 'w', encoding='utf-8') as f:
                f.write(flow_group.to_json())
            print(f"  写入成功，任务数: {len(flow_group.tasks)}")
        except Exception as e:
            print(f"  写入失败: {e}")
    
    print("\n=== 操作完成 ===")
    print(f"任务图谱文件: {graph_output_file}")
    print(f"任务流组输出目录: {output_dir}")
    print(f"生成的任务流组数量: {len(flow_groups)}")

if __name__ == '__main__':
    main()