# 船舶能效数据分析 - 微服务架构

基于 uv workspace 的 monorepo，将原单体 FastAPI 后端逐步拆分为独立微服务。

## 项目结构

```
services/
├── pyproject.toml              # uv workspace 根配置
├── libs/
│   └── common/                 # 公共库（跨服务复用）
│       ├── common/
│       │   ├── database.py     # 引擎/会话工厂
│       │   ├── repository.py   # BaseRepository 通用 CRUD
│       │   ├── schemas.py      # ResponseModel 统一响应
│       │   ├── models.py       # SQLAlchemy Base + Mixin
│       │   └── exceptions.py   # 异常体系 + FastAPI handlers
│       └── tests/
└── apps/
    └── meta/                   # 元数据微服务
        ├── meta/
        │   ├── app.py          # FastAPI 入口
        │   ├── config.py       # 配置
        │   ├── database.py     # SQLite 数据库
        │   ├── models.py       # ORM 模型
        │   ├── schemas.py      # Pydantic schema
        │   ├── repository.py   # 数据访问层
        │   ├── service.py      # 业务逻辑层
        │   └── router.py       # API 路由
        ├── tests/
        ├── Dockerfile
        └── .env.example
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite（meta 服务） |
| 包管理 | uv workspace |
| 测试 | pytest + httpx |
| 容器 | Docker |

## 快速开始

### 环境准备

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 进入项目目录
cd services

# 安装所有依赖
uv sync
```

### 运行 meta 服务

```bash
cd apps/meta
cp .env.example .env        # 按需修改配置
uv run uvicorn meta.app:app --reload
```

访问 http://localhost:8000/docs 查看 Swagger 文档。

### 运行测试

```bash
# common 单元测试
cd libs/common
uv run pytest

# meta API 测试
cd apps/meta
uv run pytest
```

## Docker 部署

从 monorepo 根目录构建：

```bash
cd services
docker build -f apps/meta/Dockerfile -t meta-service .
docker run -p 8000:8000 meta-service
```

## API 端点（meta 服务）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 健康检查 |
| GET | `/meta/fuel_type` | 获取燃料类型列表 |
| GET | `/meta/ship_type` | 获取船舶类型列表 |
| GET | `/meta/time_zone` | 获取时区列表 |
| GET | `/meta/attributes` | 获取属性列表（数据分析用） |
| GET | `/meta/attribute_mapping` | 获取属性组合（多维展示用） |
| GET | `/meta/fuel_type_category` | 获取燃料类型分类（能耗统计用） |

## 添加新服务

1. 在 `apps/` 下创建新目录，参考 `meta/` 结构
2. `pyproject.toml` 中添加 `common` 作为 workspace 依赖：
   ```toml
   [tool.uv.sources]
   common = { workspace = true }
   ```
3. 创建 `Dockerfile`，从 monorepo 根目录构建
4. 编写 `tests/` 下的 API 测试

## common 库说明

| 模块 | 用途 |
|------|------|
| `database.py` | `create_engine_from_url()` 引擎工厂、`create_session_factory()` 会话工厂 |
| `repository.py` | `BaseRepository[T]` 泛型 CRUD（get_by_id, list_all, create, update, delete） |
| `schemas.py` | `ResponseModel[Data]` 统一 API 响应包装 |
| `models.py` | `Base` 声明基类、`IntIDMixin` 自增主键、`TimestampMixin` 时间戳 |
| `exceptions.py` | `AppError` 异常体系 + `setup_exception_handlers()` FastAPI 注册 |
