# Simulation_Plantform


## 创建的文件
1. simulation_task.py - 仿真任务模块
2. config_sample.json - 示例配置文件
## 模块结构

### 核心类

| 类名 | 说明 |
|------|------|
| `SimulationConfig` | 仿真任务配置模型 (PyDantic) |
| `OrganizationConfig` | 组织配置模型 (PyDantic) |
| `WorkerConfig` | 员工配置模型 (PyDantic) |
| `SimulationEngine` | 仿真引擎，负责管理仿真生命周期 |
| `SimulationTaskModule` | 仿真任务模块，提供独立启动接口 |

### 主要功能

- **配置加载**: 支持从JSON/YAML文件或字典加载配置
- **初始化**: 根据配置创建Organization和AIWorker对象
- **启动**: AIWorker实例化后立即进入working状态
- **任务分配**: 支持按员工ID或角色分配任务
- **状态管理**: 提供仿真状态查询接口
- **信号处理**: 支持SIGINT/SIGTERM优雅关闭

### 使用示例

```python
from simulation_task import SimulationTaskModule

module = SimulationTaskModule()
module.run("config_sample.json")  # 完整运行

# 或分步操作
module.load_config("config.json")
module.initialize()
module.start()
```