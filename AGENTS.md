# AGENTS.md

> AI 助手开发指南（统一版）。阅读此文件了解项目架构、开发原则、规范和常用命令。

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

## 开发原则

> 回复请用中文。

### 1. 追求可测试

- 每个模块必须有对应的单元测试，逻辑写在可被独立测试的函数/类中
- 依赖通过参数注入（Repository、Session），不在业务代码内直接创建
- 测试使用内存 SQLite + StaticPool，不依赖真实数据库或外部服务
- 新增端点前先写测试，确保测试覆盖正常路径和错误路径

### 2. 文档即记忆，是团队的共享工具

- OpenAPI 文档是对外契约：每个 schema 必须有 `json_schema_extra.examples`，端点必须有 `summary`
- 代码注释只写“为什么”，不写“是什么”
- 本文档是 AI 和人类协作的唯一上下文入口，保持简洁、随代码演进更新

### 3. 代码精简，less is more

- 不为假设的未来需求写代码，只解决当下实际问题
- 三行相似代码优于一个过早的抽象
- 删除比添加更需要勇气：无用代码及时删除
- 依赖选择：能用标准库解决的不引入第三方

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
- 敏感信息（账号、密码、Token）只放本地私有文件（如 `./.secrets/*.env`），禁止写入仓库文档

## 数据文件统一目录

- 所有本地数据库文件统一放在：`/Users/lee/services/data`
- 当前默认路径约定：
    - `meta`: `data/meta.db`
    - `identity`: `data/identity.db`
    - `vessel`: `data/vessel.db`
    - `data`: `data/data.db` + `data/data.duckdb`
    - `analytics`: 只读 `data/data.duckdb`，不单独持有 `analytics.db`

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

### SQLite 兼容口径（重要）

- 生成 `seed.sql` 时，字段必须与当前 SQLAlchemy 模型一致
- 若 MySQL 存在模型未定义字段（如历史 `created_at`），导出时需剔除
- 若源数据不满足当前约束（如外键为空但模型要求非空），必须在迁移说明中明确过滤策略
- 导入顺序固定为：`vessel -> equipment -> equipment_fuel -> power_speed_curve -> curve_data`

### mysqldump 示例

```bash
source ./.secrets/mysql.local.env
MYSQL_PWD="$MYSQL_PASSWORD" mysqldump -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" <database_name> <table_name> > /tmp/<table_name>.sql
```

### 验证建议

- 生成后执行对应服务测试：`make test-meta` / `make test-identity` / `make test-vessel`。
- 确保 `seed.sql` 可重复执行或在启动逻辑中具备幂等保护。

### 运行态复核（本地 + K8s）

- 本地复核：直接查询 SQLite 行数与主键样本
- K8s 复核：
    1. 确认 Deployment 的 `DATABASE_URL`
    2. 必要时删除 PVC 内旧库后再同步新库
    3. `kubectl rollout restart deploy/<service> -n services`
    4. 通过 API 复核数据是否与源一致
- 对账建议至少包含：`count(*)`、主键列表、关键业务字段（如 `name` / `mmsi`）