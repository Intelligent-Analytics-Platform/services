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
│   ├── schemas.py      # Pydantic 请求/响应 schema
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

---

## 本地运行

```bash
cp .env.example .env
uv run uvicorn vessel.app:app --reload --port 8002
```

首次启动自动建表并执行 `seed.sql`，写入 1 艘测试船舶（集装箱轮）。

---

## 测试

```bash
uv run pytest -v
```
