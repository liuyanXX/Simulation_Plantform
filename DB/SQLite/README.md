# SQLite数据库目录

本目录用于存放SQLite数据库文件。

## 数据库文件

- `simulation.db` - 仿真平台主数据库

## 使用说明

数据库文件会在首次运行时自动创建，无需手动创建。

## 初始化数据库

```python
from data_storage_services.SQLite.sqlite_operator import init_database

# 初始化数据库，创建所有表
operator = init_database()
```
