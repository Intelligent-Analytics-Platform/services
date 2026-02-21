# Meta 元数据微服务

船舶能效分析平台的基础元数据服务，提供燃料类型、船舶类型、时区等静态数据查询。

## 技术栈

- **Python** 3.12+
- **FastAPI** — Web 框架
- **SQLAlchemy** 2.0 — ORM（Mapped 声明式）
- **SQLite** — 数据库（零外部依赖）
- **Pydantic** v2 — 数据校验与序列化
- **common** — 内部公共库（ResponseModel、BaseRepository、异常处理）

## 项目结构

```
apps/meta/
├── meta/
│   ├── app.py           # FastAPI 应用入口，create_app() 工厂
│   ├── config.py        # Settings，从 .env 加载配置
│   ├── database.py      # SQLite 引擎、会话依赖
│   ├── models.py        # ORM 模型：FuelType, ShipType, TimeZone
│   ├── schemas.py       # Pydantic 响应 schema
│   ├── repository.py    # 数据访问层
│   ├── service.py       # 业务逻辑层
│   └── router.py        # API 路由定义
├── tests/
│   ├── conftest.py      # 测试 fixtures（内存数据库 + 种子数据）
│   └── test_api.py      # 14 个 API 测试用例
├── Dockerfile
├── .env.example
└── pyproject.toml
```

## 快速开始

```bash
cd apps/meta
cp .env.example .env
uv run uvicorn meta.app:app --reload
```

访问 http://localhost:8000/docs 查看 Swagger 文档。

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DATABASE_URL` | `sqlite:///meta.db` | 数据库连接地址 |
| `DEBUG` | `false` | 调试模式（开启 SQL 日志） |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |

## 数据模型

### FuelType（燃料类型）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name_cn` | str | 中文名称 |
| `name_en` | str | 英文名称 |
| `name_abbr` | str | 缩写 |
| `cf` | float | 碳排放因子 |

### ShipType（船舶类型）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name_cn` | str | 中文名称 |
| `name_en` | str | 英文名称 |
| `code` | str | 类型编码 |
| `cii_related_tone` | str | CII 相关吨位类型（DWT/GT） |

### TimeZone（时区）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name_cn` | str | 中文名称 |
| `name_en` | str | 英文名称 |
| `explaination` | str | 说明（如 UTC+8） |

## API 接口

所有接口返回统一格式：

```json
{
  "code": 200,
  "data": ...,
  "message": "..."
}
```

---

### GET /meta/fuel_type

获取所有燃料类型，用于"新增船舶"弹窗的燃料选择。

**请求示例**

```bash
curl http://localhost:8000/meta/fuel_type
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name_cn": "液化天然气",
      "name_en": "Liquefied Natural Gas",
      "name_abbr": "LNG",
      "cf": 2.75
    },
    {
      "id": 2,
      "name_cn": "重油",
      "name_en": "Heavy Fuel Oil",
      "name_abbr": "HFO",
      "cf": 3.114
    }
  ],
  "message": "获取燃料类型成功"
}
```

---

### GET /meta/ship_type

获取所有船舶类型，用于"新增船舶"弹窗的船型选择。

**请求示例**

```bash
curl http://localhost:8000/meta/ship_type
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name_cn": "集装箱船",
      "name_en": "Container Ship",
      "code": "I1004",
      "cii_related_tone": "DWT"
    },
    {
      "id": 2,
      "name_cn": "散货船",
      "name_en": "Bulk Carrier",
      "code": "I1001",
      "cii_related_tone": "DWT"
    }
  ],
  "message": "获取船舶类型成功"
}
```

---

### GET /meta/time_zone

获取所有船用时区，用于"新增船舶"弹窗的时区选择。

**请求示例**

```bash
curl http://localhost:8000/meta/time_zone
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name_cn": "中国标准时间",
      "name_en": "China Standard Time",
      "explaination": "UTC+8"
    }
  ],
  "message": "获取时区成功"
}
```

---

### GET /meta/attributes

获取数据分析属性列表，用于"数据分析与回放"页面的属性下拉框。

**请求示例**

```bash
curl http://localhost:8000/meta/attributes
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    { "attribute": "speed_ground", "description": "对地航速" },
    { "attribute": "speed_water", "description": "对水航速" },
    { "attribute": "draft", "description": "船艏船尾平均吃水" },
    { "attribute": "trim", "description": "船舶纵倾" },
    { "attribute": "me_rpm", "description": "主机转速" },
    { "attribute": "wind_speed", "description": "风速" },
    { "attribute": "wind_direction", "description": "风向" },
    { "attribute": "slip_ratio", "description": "滑失比" },
    { "attribute": "me_fuel_consumption_nmile", "description": "主机每海里油耗" },
    { "attribute": "me_fuel_consumption_kwh", "description": "主机每千瓦时油耗（g/kWh）" },
    { "attribute": "me_shaft_power", "description": "主机功率" }
  ],
  "message": "获取属性成功"
}
```

---

### GET /meta/attribute_mapping

获取属性组合列表，用于"多角度展示"页面的图表坐标轴配置。

**请求示例**

```bash
curl http://localhost:8000/meta/attribute_mapping
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    {
      "attribute_left": { "attribute": "speed_water", "description": "对水航速" },
      "attribute_right": { "attribute": "me_shaft_power", "description": "主机功率" }
    },
    {
      "attribute_left": { "attribute": "speed_water", "description": "对水航速" },
      "attribute_right": { "attribute": "me_fuel_consumption_nmile", "description": "主机每海里油耗（Kg/NM）" }
    },
    {
      "attribute_left": { "attribute": "me_rpm", "description": "主机转速" },
      "attribute_right": { "attribute": "me_shaft_power", "description": "主机功率" }
    },
    {
      "attribute_left": { "attribute": "me_rpm", "description": "主机转速" },
      "attribute_right": { "attribute": "me_fuel_consumption_kwh", "description": "主机功率油耗（g/kWh）" }
    },
    {
      "attribute_left": { "attribute": "me_shaft_power", "description": "主机功率" },
      "attribute_right": { "attribute": "me_fuel_consumption_kwh", "description": "主机功率油耗（g/kWh）" }
    }
  ],
  "message": "获取属性组合成功"
}
```

---

### GET /meta/fuel_type_category

获取燃料类型分类，用于"能耗统计"页面的燃料筛选。

**请求示例**

```bash
curl http://localhost:8000/meta/fuel_type_category
```

**响应示例**

```json
{
  "code": 200,
  "data": [
    { "label": "重油", "value": "hfo" },
    { "label": "轻油", "value": "lfo" },
    { "label": "船舶柴油", "value": "mgo" },
    { "label": "内河船用燃料油", "value": "mdo" },
    { "label": "液化天然气", "value": "lng" },
    { "label": "液化石油气(丙烷)", "value": "lpg_p" },
    { "label": "液化石油气(丁烷)", "value": "lpg_b" },
    { "label": "甲醇", "value": "methanol" },
    { "label": "乙醇", "value": "ethanol" },
    { "label": "乙烷", "value": "ethane" },
    { "label": "氨", "value": "ammonia" },
    { "label": "氢", "value": "hydrogen" }
  ],
  "message": "获取燃料类型成功"
}
```

## 测试

```bash
# 运行全部测试
uv run pytest -v

# 运行指定测试类
uv run pytest -v -k TestFuelType
```

测试使用 SQLite 内存数据库 + StaticPool，无需外部依赖，测试间完全隔离。

## Docker 部署

从 monorepo 根目录构建：

```bash
cd services
docker build -f apps/meta/Dockerfile -t meta-service .
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///meta.db meta-service
```

## 架构说明

```
请求 → router.py → service.py → repository.py → SQLAlchemy → SQLite
                        ↓
                  硬编码数据直接返回
                  (attributes, fuel_type_category)
```

- **router** — 路由定义 + 依赖注入，负责 HTTP 层
- **service** — 业务逻辑，数据库查询委托给 repository，静态数据直接返回
- **repository** — 继承 `common.BaseRepository`，封装 SQL 查询
- **models** — SQLAlchemy ORM 模型，映射数据库表
- **schemas** — Pydantic 模型，定义 API 响应结构（与 ORM 模型解耦）
