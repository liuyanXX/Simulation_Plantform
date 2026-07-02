"""数据存储服务组合调用测试

测试多个服务之间的组合调用操作。
"""

import unittest
import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_storage_services.sql_db_services.solution_service import SolutionService
from data_storage_services.sql_db_services.task_service import TaskService
from data_storage_services.sql_db_services.task_manifest_service import TaskManifestService
from data_storage_services.sql_db_services.task_flow_group_service import TaskFlowGroupService
from data_storage_services.sql_db_services.tasks_graph_service import TasksGraphService
from data_storage_services.sql_db_services.worker_service import WorkerService
from data_storage_services.sql_db_services.organization_service import OrganizationService
from bo.solution import Solution, SolutionStatus, SolutionPriority
from bo.task import Task, StartTask, EndTask, Priority, TaskType
from bo.task_manifest import TaskManifest
from bo.task_flow_group import TaskFlowGroup
from bo.tasks_graph import TasksGraph
from bo.ssys.aiworker import AIWorker
from bo.organization import Organization


class TestDataStorageIntegration(unittest.TestCase):
    """数据存储服务组合调用测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'test_integration.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        cls.logger = logging.getLogger(__name__)
        cls.logger.info("=" * 60)
        cls.logger.info("开始数据存储服务组合调用测试")
        cls.logger.info("=" * 60)

        test_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        os.makedirs(test_db_path, exist_ok=True)

        from . import ensure_tables_exist
        ensure_tables_exist(test_db_path, "test_integration.db")

        cls.solution_service = SolutionService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.task_service = TaskService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.manifest_service = TaskManifestService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.flow_group_service = TaskFlowGroupService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.graph_service = TasksGraphService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.worker_service = WorkerService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )
        cls.org_service = OrganizationService(
            db_type="sqlite",
            db_config={"db_path": test_db_path, "db_name": "test_integration.db"}
        )

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.solution_service.disconnect()
        cls.task_service.disconnect()
        cls.manifest_service.disconnect()
        cls.flow_group_service.disconnect()
        cls.graph_service.disconnect()
        cls.worker_service.disconnect()
        cls.org_service.disconnect()
        cls.logger.info("数据存储服务组合调用测试完成")

    def setUp(self):
        """每个测试前的准备"""
        self.logger.info("\n" + "-" * 60)

    def test_01_solution_manifest_tasks_integration(self):
        """测试01: 方案-清单-任务完整流程"""
        self.logger.info("测试01: 方案-清单-任务完整流程")

        solution = Solution(
            solution_id="SOL_INT_001",
            name="集成测试方案",
            version="1.0",
            status=SolutionStatus.DRAFT,
            priority=SolutionPriority.HIGH,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.solution_service.create(solution)
        self.logger.info(f"创建方案: {solution.solution_id}")

        manifest = TaskManifest(
            manifest_id="MANIFEST_INT_001",
            manifest_name="集成测试清单",
            description="测试清单",
            solution_id=solution.solution_id,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.manifest_service.create(manifest)
        self.logger.info(f"创建清单: {manifest.manifest_id}")

        flow_group = TaskFlowGroup(
            flow_id="FLOW_INT_001",
            flow_name="集成测试流组",
            description="测试流组",
            manifest_id=manifest.manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.flow_group_service.create(flow_group)
        self.logger.info(f"创建流组: {flow_group.flow_id}")

        graph = TasksGraph(
            graph_id="GRAPH_INT_001",
            graph_name="集成测试图谱",
            description="测试图谱",
            manifest_id=manifest.manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.graph_service.create(graph)
        self.logger.info(f"创建图谱: {graph.graph_id}")

        now = datetime.now()
        start_task = StartTask(
            task_id="TASK_START_INT_001",
            task_name="开始任务",
            expected_start_time=now,
            expected_end_time=now + timedelta(hours=1),
            content="开始节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority=Priority.LOW,
            output_target_role="DEV",
            task_destinations=["TASK_INT_001"],
            task_type=TaskType.START
        )
        start_task._flow_group_id = flow_group.flow_id
        start_task._graph_id = graph.graph_id
        start_task._manifest_id = manifest.manifest_id
        self.task_service.create(start_task)
        self.logger.info(f"创建开始任务: {start_task.task_id}")

        normal_task = Task(
            task_id="TASK_INT_001",
            task_name="普通任务",
            expected_start_time=now + timedelta(hours=1),
            expected_end_time=now + timedelta(hours=9),
            content="开发任务",
            execute_role="DEV",
            resource_consumption=8.0,
            priority=Priority.HIGH,
            output_target_role="TEST",
            task_source="TASK_START_INT_001",
            task_destinations=["TASK_END_INT_001"],
            task_type=TaskType.NORMAL
        )
        normal_task._flow_group_id = flow_group.flow_id
        normal_task._graph_id = graph.graph_id
        normal_task._manifest_id = manifest.manifest_id
        self.task_service.create(normal_task)
        self.logger.info(f"创建普通任务: {normal_task.task_id}")

        end_task = EndTask(
            task_id="TASK_END_INT_001",
            task_name="结束任务",
            expected_start_time=now + timedelta(hours=9),
            expected_end_time=now + timedelta(hours=10),
            content="结束节点",
            execute_role="SYSTEM",
            resource_consumption=0.0,
            priority=Priority.LOW,
            output_target_role="",
            task_source="TASK_INT_001",
            task_destinations=[],
            task_type=TaskType.END
        )
        end_task._flow_group_id = flow_group.flow_id
        end_task._graph_id = graph.graph_id
        end_task._manifest_id = manifest.manifest_id
        self.task_service.create(end_task)
        self.logger.info(f"创建结束任务: {end_task.task_id}")

        read_manifest = self.manifest_service.read("MANIFEST_INT_001")
        self.assertIsNotNone(read_manifest)
        self.assertEqual(read_manifest.solution_id, solution.solution_id)

        tasks = self.task_service.get_by_manifest(manifest.manifest_id)
        self.assertEqual(len(tasks), 3)
        self.logger.info(f"清单中任务数量: {len(tasks)}")

        self.logger.info("方案-清单-任务完整流程测试通过")

    def test_02_org_worker_assignment_integration(self):
        """测试02: 组织-员工-任务分配流程"""
        self.logger.info("测试02: 组织-员工-任务分配流程")

        org = Organization(
            org_id="ORG_INT_001",
            name="集成测试组织",
            parent=None,
            children=[],
            workers=[]
        )
        self.org_service.create(org)
        self.logger.info(f"创建组织: {org.org_id}")

        worker = AIWorker(
            employee_id="EMP_INT_001",
            name="集成测试员工",
            department="测试部",
            roles=["DEV", "TEST"],
            daily_work_hours=8.0,
            task_list=[]
        )
        worker._org_id = org.org_id
        self.worker_service.create(worker)
        self.logger.info(f"创建员工: {worker.employee_id}")

        now = datetime.now()
        task = Task(
            task_id="TASK_INT_002",
            task_name="分配测试任务",
            expected_start_time=now,
            expected_end_time=now + timedelta(hours=8),
            content="测试任务内容",
            execute_role="DEV",
            resource_consumption=8.0,
            priority=Priority.MEDIUM,
            output_target_role="TEST",
            task_type=TaskType.NORMAL
        )
        self.task_service.create(task)
        self.logger.info(f"创建任务: {task.task_id}")

        self.worker_service.assign_task(worker.employee_id, task.task_id)
        self.logger.info(f"分配任务给员工")

        workers_in_org = self.worker_service.get_by_org(org.org_id)
        self.assertEqual(len(workers_in_org), 1)
        self.logger.info(f"组织中员工数量: {len(workers_in_org)}")

        self.logger.info("组织-员工-任务分配流程测试通过")

    def test_03_workflow_query_integration(self):
        """测试03: 工作流查询组合"""
        self.logger.info("测试03: 工作流查询组合")

        manifest = TaskManifest(
            manifest_id="MANIFEST_INT_003",
            manifest_name="查询测试清单",
            description="测试清单",
            solution_id="SOL_QUERY",
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.manifest_service.create(manifest)

        flow_group = TaskFlowGroup(
            flow_id="FLOW_INT_003",
            flow_name="查询测试流组",
            description="测试流组",
            manifest_id=manifest.manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.flow_group_service.create(flow_group)

        graph = TasksGraph(
            graph_id="GRAPH_INT_003",
            graph_name="查询测试图谱",
            description="测试图谱",
            manifest_id=manifest.manifest_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.graph_service.create(graph)

        now = datetime.now()
        tasks = []
        for i in range(5):
            task = Task(
                task_id=f"TASK_INT_003_{i}",
                task_name=f"查询测试任务{i}",
                expected_start_time=now,
                expected_end_time=now + timedelta(hours=8),
                content=f"任务内容{i}",
                execute_role="DEV",
                resource_consumption=8.0,
                priority=Priority.MEDIUM,
                output_target_role="TEST",
                task_type=TaskType.NORMAL
            )
            task._flow_group_id = flow_group.flow_id
            task._graph_id = graph.graph_id
            task._manifest_id = manifest.manifest_id
            self.task_service.create(task)
            tasks.append(task)

        manifest_tasks = self.task_service.get_by_manifest(manifest.manifest_id)
        self.assertEqual(len(manifest_tasks), 5)

        flow_tasks = self.task_service.get_by_flow_group(flow_group.flow_id)
        self.assertEqual(len(flow_tasks), 5)

        graph_tasks = self.task_service.get_by_graph(graph.graph_id)
        self.assertEqual(len(graph_tasks), 5)

        self.logger.info(f"清单任务数: {len(manifest_tasks)}")
        self.logger.info(f"流组任务数: {len(flow_tasks)}")
        self.logger.info(f"图谱任务数: {len(graph_tasks)}")

        self.logger.info("工作流查询组合测试通过")

    def test_04_batch_crud_integration(self):
        """测试04: 批量CRUD组合操作"""
        self.logger.info("测试04: 批量CRUD组合操作")

        solutions = [
            Solution(
                solution_id=f"SOL_BATCH_{i}",
                name=f"批量方案{i}",
                version="1.0",
                status=SolutionStatus.DRAFT,
                priority=SolutionPriority.MEDIUM,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(5)
        ]
        count = self.solution_service.create_many(solutions)
        self.assertEqual(count, 5)
        self.logger.info(f"批量创建方案: {count}")

        all_solutions = self.solution_service.read_all()
        self.assertGreaterEqual(len(all_solutions), 5)

        for sol in all_solutions[:3]:
            sol.status = SolutionStatus.ACTIVE
            self.solution_service.update(sol)
        self.logger.info("批量更新方案状态")

        active_count = len(self.solution_service.get_by_status(SolutionStatus.ACTIVE))
        self.logger.info(f"活跃方案数量: {active_count}")

        for sol in all_solutions[:3]:
            self.solution_service.delete(sol.solution_id)
        self.logger.info("批量删除方案")

        remaining_count = self.solution_service.count()
        self.logger.info(f"剩余方案数量: {remaining_count}")

        self.logger.info("批量CRUD组合操作测试通过")

    def test_05_cross_service_query_integration(self):
        """测试05: 跨服务关联查询"""
        self.logger.info("测试05: 跨服务关联查询")

        org = Organization(
            org_id="ORG_INT_005",
            name="跨服务测试组织",
            parent=None,
            children=[],
            workers=[]
        )
        self.org_service.create(org)

        workers = [
            AIWorker(
                employee_id=f"EMP_INT_005_{i}",
                name=f"员工{i}",
                department="研发部",
                roles=["DEV"],
                daily_work_hours=8.0,
                task_list=[]
            )
            for i in range(3)
        ]
        for w in workers:
            w._org_id = org.org_id
        self.worker_service.create_many(workers)
        self.logger.info(f"创建员工数量: {len(workers)}")

        dev_workers = self.worker_service.get_by_role("DEV")
        self.assertGreaterEqual(len(dev_workers), 3)

        org_workers = self.worker_service.get_by_org(org.org_id)
        self.assertEqual(len(org_workers), 3)
        self.logger.info(f"组织内员工数量: {len(org_workers)}")

        self.logger.info("跨服务关联查询测试通过")


if __name__ == '__main__':
    unittest.main()