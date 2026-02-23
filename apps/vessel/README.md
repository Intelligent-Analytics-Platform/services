# Vessel 船舶管理服务

船舶能效分析平台的船舶信息微服务，管理船舶基本信息、设备配置和功率-航速曲线。

- **端口**：`8002`
- **OpenAPI 文档**：`http://localhost:8002/docs`

---

## 实体关系

```
  identity 服务              meta 服务
  ─────────────              ─────────
  company.id ◄───┐     ┌───► ship_type.id
                 │     │     ┌───► time_zone.id
                 │     │     │     ┌───► fuel_type.id
                 │     │     │     │
                 ▼     ▼     ▼     │  (跨服务引用：仅存 int，无 DB FK)
          ┌─────────────────────┐  │
          │       Vessel        │  │
          │─────────────────────│  │
          │ id (PK)             │  │
          │ name (unique)       │  │
          │ mmsi (unique)       │  │
          │ company_id ─────────┘  │
          │ ship_type ─────────────┘
          │ time_zone ─────────────┘
          │ build_date              │
          │ gross_tone              │
          │ dead_weight             │
          │ new_vessel (bool)       │
          │ pitch (螺距)            │
          │ hull_clean_date?        │
          │ engine_overhaul_date?   │
          │ newly_paint_date?       │
          │ propeller_polish_date?  │
          └──────────┬──────────┬──┘
                     │          │
         ┌───────────┘          └────────────────┐
         ▼                                        ▼
  ┌─────────────────┐                ┌────────────────────────┐
  │    Equipment    │                │    PowerSpeedCurve     │
  │─────────────────│                │────────────────────────│
  │ id (PK)         │                │ id (PK)                │
  │ name            │                │ curve_name             │
  │ type            │                │ draft_astern (艉吃水)  │
  │   me 主机       │                │ draft_bow    (艏吃水)  │
  │   dg 发电机     │                │ vessel_id (FK)         │
  │   blr 锅炉      │                └───────────┬────────────┘
  │ vessel_id (FK)  │                            │
  └────────┬────────┘                            ▼
           │                          ┌─────────────────────┐
           ▼                          │      CurveData      │
  ┌─────────────────────┐             │─────────────────────│
  │    EquipmentFuel    │             │ id (PK)             │
  │─────────────────────│             │ speed_water (kn)    │
  │ equipment_id (PK,FK)│             │ me_power (kW)       │
  │ fuel_type_id (PK)   │◄────────────│ power_speed_        │
  └─────────────────────┘    meta     │   curve_id (FK)     │
    复合主键，跨服务引用      服务       └─────────────────────┘
```

### 关键设计说明

| 设计点 | 说明 |
|--------|------|
| 跨服务引用 | `company_id`、`ship_type`、`time_zone`、`fuel_type_id` 仅存 int，无数据库 FK 约束，避免跨服务事务 |
| 级联删除 | 删除 Vessel → 自动删除 Equipment + EquipmentFuel + PowerSpeedCurve + CurveData |
| EquipmentFuel 复合主键 | `(equipment_id, fuel_type_id)` 保证同一设备不重复关联同一燃料 |
| CurveData 排序 | 查询时自动按 `speed_water` 升序排列，保证曲线点顺序正确 |
| 更新策略 | PUT /vessel/{id} 时，`equipments` 和 `curves` **全量替换**（先删后建），不支持局部更新 |

---

## 目录结构

```
apps/vessel/
├── vessel/
│   ├── app.py          # FastAPI 入口，lifespan 负责建表 + seed
│   ├── config.py       # 环境变量配置
│   ├── database.py     # SQLAlchemy engine + get_db 依赖
│   ├── models.py       # ORM 模型（5 张表）
│   ├── repository.py   # VesselRepository
│   ├── service.py      # VesselService（含嵌套结构组装）
│   ├── schemas.py      # Pydantic 请求/响应 schema（含 OpenAPI JSON examples）
│   ├── router.py       # 5 个端点
│   └── seed.sql        # 测试种子数据
├── tests/
│   ├── conftest.py
│   └── test_vessel_api.py
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/vessel` | 列表（name / company_id 过滤 + offset/limit 分页） |
| POST | `/vessel` | 创建船舶（含嵌套 equipment + curves，单事务） |
| GET | `/vessel/{id}` | 单船详情（含全部嵌套结构） |
| PUT | `/vessel/{id}` | 更新（equipment/curves 全量替换） |
| DELETE | `/vessel/{id}` | 删除（级联清除所有子表数据） |

所有响应格式统一：`{ "code": 200, "data": ..., "message": "..." }`

### 请求示例（POST /vessel）

```json
{
  "name": "八打雁",
  "mmsi": "477401900",
  "ship_type": 4,
  "build_date": "2019-11-01",
  "gross_tone": 26771.0,
  "dead_weight": 35337.0,
  "new_vessel": false,
  "pitch": 6.058,
  "hull_clean_date": "2023-06-15",
  "time_zone": 1,
  "company_id": 1,
  "equipments": [
    {"name": "主机", "type": "me", "fuel_type_ids": [1]},
    {"name": "副机", "type": "dg", "fuel_type_ids": [1, 7]},
    {"name": "锅炉", "type": "blr", "fuel_type_ids": [1, 7]}
  ],
  "curves": [
    {
      "curve_name": "满载",
      "draft_astern": 10.5,
      "draft_bow": 9.8,
      "curve_data": [
        {"speed_water": 10.0, "me_power": 2800.0},
        {"speed_water": 12.0, "me_power": 4500.0},
        {"speed_water": 14.0, "me_power": 7200.0},
        {"speed_water": 15.5, "me_power": 9800.0}
      ]
    }
  ]
}
```

---

## 数据模型

### Vessel

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键，自增 |
| `name` | str | 船名（唯一） |
| `mmsi` | str | MMSI 号（唯一） |
| `ship_type` | int | 船型 ID（跨服务引用 meta） |
| `build_date` | date | 建造日期 |
| `gross_tone` | float | 总吨（GT） |
| `dead_weight` | float | 载重吨（DWT） |
| `new_vessel` | bool | 是否新船 |
| `pitch` | float | 螺旋桨螺距（默认 6.058，用于滑失比计算） |
| `hull_clean_date` | date? | 最近船底清洁日期 |
| `engine_overhaul_date` | date? | 最近主机大修日期 |
| `newly_paint_date` | date? | 最近重新涂装日期 |
| `propeller_polish_date` | date? | 最近螺旋桨抛光日期 |
| `time_zone` | int | 时区 ID（跨服务引用 meta） |
| `company_id` | int | 所属公司 ID（跨服务引用 identity） |

### Equipment

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 设备名称（如"主机"） |
| `type` | str | `me`（主机）/ `dg`（发电机）/ `blr`（锅炉） |
| `fuel_type_ids` | list[int] | 关联燃料 ID 列表（跨服务引用 meta） |

### PowerSpeedCurve + CurveData

| 字段 | 类型 | 说明 |
|------|------|------|
| `curve_name` | str | 曲线名称（如"满载"、"压载"） |
| `draft_astern` | float | 艉吃水（m） |
| `draft_bow` | float | 艏吃水（m） |
| `speed_water` | float | 对水速度（kn） |
| `me_power` | float | 主机功率（kW） |

---

## 本地运行

```bash
cp .env.example .env
uv run uvicorn vessel.app:app --reload --port 8002
```

首次启动自动建表并执行 `seed.sql`，写入 1 艘测试船舶（集装箱轮）。

**环境变量**（`.env`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///vessel.db` | 数据库连接串 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

---

## 测试

```bash
uv run pytest -v
```

19 个测试覆盖：CRUD 完整流程、嵌套结构创建、级联删除、列表过滤与分页、404 处理。

---

## Docker 部署

从 monorepo 根目录构建：

```bash
docker build -f apps/vessel/Dockerfile -t vessel-service .
docker run -p 8002:8002 vessel-service
```
