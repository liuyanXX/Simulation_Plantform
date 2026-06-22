import json
import threading
import time
from simulation_process_engine import SimulationProcessEngine

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

manifest_file = 'test_start_worker_manifest.json'
with open(manifest_file, 'w', encoding='utf-8') as f:
    json.dump(sample_manifest, f, ensure_ascii=False, indent=2)

engine = SimulationProcessEngine(manifest_file)

def run_engine():
    engine.run()

engine_thread = threading.Thread(target=run_engine, daemon=True)
engine_thread.start()

time.sleep(3)

status = engine.get_simulation_status()
print('员工列表:')
for worker in status['workers']:
    print(f"  - {worker['name']} (ID: {worker['employee_id']}, 角色: {worker['roles']})")

role_keys = list(engine.get_role_registry().keys())
print(f"\n角色注册表: {role_keys}")

engine.stop()
time.sleep(2)