# AGENTS.md

> AI 助手开发指南。阅读此文件了解项目架构、规范和常用命令。

## 项目概览

船舶能效数据分析微服务平台，基于 uv workspace 的 monorepo 结构。

```
services/
├── libs/common/          # 公共库（认证、数据库、异常、仓储）
└── apps/
    ├── meta/             # 元数据服务 (port 8000)
    ├── identity/         # 身份认证服务 (port 8001)
    ├── vessel/           # 船舶管理服务 (port 8002)
    ├── data/             # 遥测数据服务 (port 8003)
    └── analytics/        # 分析服务 (port 8004)
```

## 技术栈

- **Python**: 3.12+
- **Web**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **校验**: Pydantic v2
- **测试**: pytest + TestClient
- **Linter**: ruff
- **包管理**: uv

## 开发规范

### 1. 分层架构

每个服务遵循 `Router → Service → Repository` 三层：

```
router.py   # 端点定义、参数校验、响应组装
service.py  # 业务逻辑、跨表操作、Schema 转换
repository.py  # 数据访问、单表 CRUD
```

### 2. 依赖注入

```python
# router.py
def get_vessel_service(session: Session = Depends(get_db)) -> VesselService:
    return VesselService(VesselRepository(session))

@router.get("/{id}")
def get_vessel(id: int, service: VesselService = Depends(get_vessel_service)):
    return ResponseModel(data=service.get_vessel_by_id(id))
```

### 3. Schema 规范

所有 Pydantic schema 必须包含 `json_schema_extra.examples`：

```python
class VesselCreate(BaseModel):
    name: str
    mmsi: str
    # ...

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "八打雁", "mmsi": "477401900", ...}]
        }
    }
```

响应使用统一的 `ResponseModel[T]`：

```python
return ResponseModel(data=vessel, message="获取成功")
```

### 4. 测试规范

- 使用内存 SQLite + StaticPool
- 每个服务有独立的 `tests/conftest.py`
- 测试类按功能分组（如 `TestGetVessels`, `TestCreateVessel`）

```python
@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
```

### 5. 代码风格

- 不写注释解释"是什么"，只写"为什么"
- 三行相似代码优于过早抽象
- 能用标准库就不引入第三方库

## 常用命令

```bash
# 安装依赖
make install

# Lint 检查和格式化
make lint
make format

# 运行测试
make test              # 所有服务
make test-vessel       # 单个服务

# 本地运行服务
make run-vessel        # http://localhost:8002/docs

# 生成 OpenAPI 文档
make gen-docs
```

## 添加新端点流程

1. 在 `models.py` 定义/修改模型
2. 在 `schemas.py` 定义请求/响应 Schema（含 examples）
3. 在 `repository.py` 添加数据访问方法
4. 在 `service.py` 实现业务逻辑
5. 在 `router.py` 定义端点（含 summary）
6. 在 `tests/test_xxx_api.py` 编写测试
7. 运行 `make lint && make test-xxx`

## 公共库模块

| 模块 | 用途 |
|------|------|
| `common.auth` | 密码哈希、JWT 创建/解码 |
| `common.database` | 引擎/会话工厂 |
| `common.repository` | `BaseRepository[T]` 泛型 CRUD |
| `common.schemas` | `ResponseModel[Data]` 统一响应 |
| `common.models` | `Base` / `IntIDMixin` / `TimestampMixin` |
| `common.exceptions` | `EntityNotFoundError` / `AuthenticationError` |
| `common.logging` | 结构化 JSON 日志配置 |

## 注意事项

- 新增代码前先阅读同类服务的实现作为参考
- 保持与现有代码风格一致
- 修改代码后确保测试通过
- 中文注释和文档，代码命名用英文

## 数据迁移（MySQL -> seed.sql）

当需要生成各服务 `seed.sql` 时，数据源来自本地 MySQL。

### 连接信息

- Host: `127.0.0.1`
- Port: `3306`
- User / Password: 使用本地私有配置文件（建议 `./.secrets/mysql.local.env`），不要写入仓库文档。

### 推荐流程

1. 先在 MySQL 中确认目标库和目标表（按服务划分：`meta` / `identity` / `vessel` / `data`）。
2. 使用 `mysqldump` 导出目标表结构和数据。
3. 将 MySQL 方言转换为 SQLite 兼容 SQL（去掉 ENGINE、CHARSET、AUTO_INCREMENT、反引号等）。
4. 按服务写入对应的 `seed.sql`：
    - `apps/meta/meta/seed.sql`
    - `apps/identity/identity/seed.sql`
    - `apps/vessel/vessel/seed.sql`
5. 在本地运行服务并验证启动时可正确执行 seed。

### mysqldump 示例

```bash
source ./.secrets/mysql.local.env
MYSQL_PWD="$MYSQL_PASSWORD" mysqldump -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" <database_name> <table_name> > /tmp/<table_name>.sql
```

### 验证建议

- 生成后执行对应服务测试：`make test-meta` / `make test-identity` / `make test-vessel`。
- 确保 `seed.sql` 可重复执行或在启动逻辑中具备幂等保护。