# Meta 元数据服务

船舶能效分析平台的基础数据微服务，提供燃料类型、船舶类型、时区等只读参考数据。

- **端口**：`8000`
- **OpenAPI 文档**：`http://localhost:8000/docs`

---

## 目录结构

```
apps/meta/
├── meta/
│   ├── app.py          # FastAPI 入口，lifespan 负责建表 + seed
│   ├── config.py       # 环境变量配置（database_url / log_level）
│   ├── database.py     # SQLAlchemy engine + get_db 依赖
│   ├── models.py       # ORM 模型：FuelType / ShipType / TimeZone
│   ├── repository.py   # MetaRepository：封装 3 个 SELECT 查询
│   ├── service.py      # MetaService：DB 数据 + 静态配置数据
│   ├── schemas.py      # Pydantic 响应 schema（含 OpenAPI examples）
│   ├── router.py       # 6 个只读 GET 端点
│   └── seed.sql        # 种子数据（数据与代码分离）
├── tests/
│   ├── conftest.py     # in-memory SQLite + 执行 seed.sql
│   └── test_api.py     # 19 个 API 测试
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## API 端点

所有响应格式统一：

```json
{ "code": 200, "data": [...], "message": "..." }
```

| 方法 | 路径 | 数据来源 | 说明 |
|------|------|----------|------|
| GET | `/` | — | 健康检查 |
| GET | `/meta/fuel_type` | 数据库 | 16 种燃料，含碳排放因子（CF） |
| GET | `/meta/ship_type` | 数据库 | 13 种 IMO CII 船型，含 DWT/GT 基准 |
| GET | `/meta/time_zone` | 数据库 | 25 个标准时区（UTC-12 至 UTC+12） |
| GET | `/meta/attributes` | 静态 | 11 个性能分析属性（航速、功率、油耗等） |
| GET | `/meta/attribute_mapping` | 静态 | 5 组散点图 X/Y 轴属性对 |
| GET | `/meta/fuel_type_category` | 静态 | 12 个燃料大类，用于前端筛选 |

---

## 数据模型

### FuelType（燃料类型）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name_abbr` | str | 缩写，如 `LNG` |
| `name_cn` | str | 中文名称 |
| `name_en` | str | 英文名称 |
| `cf` | float | CO₂ 排放因子（t-CO₂/t-fuel） |

### ShipType（船舶类型）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `code` | str | IMO 类型编码，如 `I004` |
| `name_cn` / `name_en` | str | 中英文名称 |
| `cii_related_tone` | str | CII 计算基准：`dwt` 或 `gt` |

### TimeZone（时区）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name_cn` | str | 中文名，如 `东八区` |
| `name_en` | str | UTC 偏移，如 `UTC+8` |
| `explaination` | str | 经度范围说明 |

---

## 架构

```
GET /meta/fuel_type
  └─▶ router.py      依赖注入 get_meta_service()
  └─▶ service.py     调用 repository
  └─▶ repository.py  SELECT * FROM fuel_type
  └─▶ SQLite (meta.db)

GET /meta/attributes
  └─▶ router.py
  └─▶ service.py     直接返回静态列表（无 DB 查询）
```

- **MetaRepository** 不继承 `BaseRepository`，因为只有 3 个只读查询，不需要通用 CRUD。
- **静态数据**（attributes / attribute_mapping / fuel_type_category）在 `service.py` 中直接定义，不入库——这类数据与业务逻辑紧密绑定，SQL 存储反而增加维护成本。

---

## 种子数据

启动时自动执行 `seed.sql`（幂等：检测到已有数据则跳过）。

```
seed.sql  ──▶  fuel_type（16 条）
          ──▶  ship_type（13 条）
          ──▶  time_zone（25 条）
```

数据需要变更时只需修改 `seed.sql`，无需动 Python 代码。

---

## 本地运行

```bash
cp .env.example .env
uv run uvicorn meta.app:app --reload --port 8000
```

**环境变量**（`.env`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///meta.db` | 数据库连接串 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

---

## 测试

```bash
uv run pytest -v
# 指定类
uv run pytest -v -k TestFuelType
```

测试使用 in-memory SQLite + StaticPool，执行同一份 `seed.sql`，与生产 seed 完全一致，无需外部依赖。

---

## Docker 部署

从 monorepo 根目录构建：

```bash
docker build -f apps/meta/Dockerfile -t meta-service .
docker run -p 8000:8000 meta-service
```
