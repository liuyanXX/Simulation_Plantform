import json
import threading
import time
from datetime import datetime
from simulation_process_engine import SimulationProcessEngine
from task import StartTask, Task

sample_manifest = {
    'org_id': 'ROOT',
    'name': '总公司',
    'workers': [],
    'children': [
        {
            'org_id': 'RD',
            'name': '研发部',
            'workers': [
                {
                    'employee_id': 'EMP001',
                    'name': '张三',
                    'department': '研发部',
                    'roles': ['DEV'],
                    'daily_work_hours': 8.0
                }
            ],
            'children': []
        }
    ]
}

manifest_file = 'test_start_task_manifest.json'
with open(manifest_file, 'w', encoding='utf-8') as f:
    json.dump(sample_manifest, f, ensure_ascii=False, indent=2)

engine = SimulationProcessEngine(manifest_file)

def run_engine():
    engine.run()

engine_thread = threading.Thread(target=run_engine, daemon=True)
engine_thread.start()

time.sleep(3)

now = datetime.now()
start_task = StartTask(
    task_id="START001",
    task_name="流程开始",
    expected_start_time=now,
    expected_end_time=now,
    content="流程开始节点",
    execute_role="SYSTEM",
    resource_consumption=0.0,
    priority="low",
    output_target_role="DEV",
    task_destinations=["T001"]
)

normal_task = Task(
    task_id="T001",
    task_name="开发模块",
    expected_start_time=now,
    expected_end_time=now,
    content="开发用户模块",
    execute_role="DEV",
    resource_consumption=0.5,
    priority="high"
)

engine.assign_initial_tasks([start_task, normal_task])

time.sleep(5)

start_worker = engine.get_worker("__START_WORKER__")
print(f"启动员工任务数量: {len(start_worker.task_list)}")
for t in start_worker.task_list:
    print(f"  - {t.task_id}: {t.task_name}")

dev_worker = engine.get_worker("EMP001")
print(f"\n张三任务数量: {len(dev_worker.task_list)}")
for t in dev_worker.task_list:
    print(f"  - {t.task_id}: {t.task_name}")

engine.stop()
time.sleep(2)