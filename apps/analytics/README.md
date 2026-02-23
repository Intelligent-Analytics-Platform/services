# Analytics 分析服务

船舶能效分析平台的统计分析与优化建议微服务，提供直方图/散点图/CII 数据查询和航速/吃水差 ML 优化建议。

- **端口**：`8004`
- **OpenAPI 文档**：`http://localhost:8004/docs`

---

## 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│  analytics 服务（只读，端口 8004）                             │
│                                                              │
│  ┌─────────────────┐   ┌──────────────────────────────────┐ │
│  │  statistic 路由  │   │  optimization 路由                │ │
│  │  /statistic/... │   │  /optimization/...               │ │
│  └────────┬────────┘   └──────────────┬───────────────────┘ │
│           │                           │                      │
│           └──────────┬────────────────┘                      │
│                      ▼                                       │
│           ┌──────────────────────┐                           │
│           │   StatisticService   │                           │
│           │  OptimizationService │                           │
│           └──────┬───────────────┘                           │
│                  │                                           │
│     ┌────────────┼────────────┐                             │
│     ▼            ▼            ▼                              │
│  DuckDB       vessel       meta                              │
│  (只读)       service      service                           │
└──────────────────────────────────────────────────────────────┘
```

### 设计原则

| 点 | 说明 |
|----|------|
| **只读 DuckDB** | 与 data 服务共享同一个 DuckDB 文件，以 `read_only=True` 打开，不阻塞写入方 |
| **跨服务查询** | vessel 服务提供 `dead_weight`/`gross_tone`/`ship_type`，meta 服务提供 `ship_type` → code 映射 |
| **列白名单** | `attribute_name` 参数经过白名单校验（`_PER_DAY_COLS` / `_STD_COLS`），防止 SQL 注入 |
| **IMO CII 计算** | 纯 Python，无 DB 依赖，支持 2023–2030 年减排因子 |
| **ML 优化（可选）** | XGBoost pkl 模型按需加载；未部署模型时端点返回 404，不影响其他功能 |

---

## 数据来源

```
data 服务写入 ──► data.duckdb ◄── analytics 服务读取（只读）
                     │
           ┌─────────┴─────────┐
           ▼                   ▼
  vessel_standard_data   vessel_data_per_day
  （清洗后逐条记录）       （日均聚合 + CII）
```

---

## 目录结构

```
apps/analytics/
├── analytics/
│   ├── app.py          # FastAPI 入口 + lifespan
│   ├── config.py       # Settings: duck_db_path, service URLs, models_dir
│   ├── database.py     # get_duck_conn()（只读 DuckDB 上下文管理器）
│   ├── cii_rating.py   # IMO CII 纯函数（get_cii_rating / get_cii_boundaries）
│   ├── schemas.py      # Pydantic 响应模型
│   ├── client.py       # HTTP 客户端（vessel / meta 服务）
│   ├── service.py      # StatisticService + OptimizationService
│   └── router.py       # 13 个端点
├── tests/
│   ├── conftest.py     # 临时 DuckDB fixture + TestClient
│   └── test_analytics_api.py  # 18 个测试
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## API 端点

### 统计分析（`/statistic`）

| 方法 | 路径 | 数据表 | 说明 |
|------|------|--------|------|
| GET | `/statistic/attribute-frequencies` | vessel_standard_data | 属性值频次（直方图） |
| GET | `/statistic/attribute-values` | vessel_data_per_day | 属性日均值（散点图） |
| GET | `/statistic/attribute-relation` | vessel_data_per_day | 双属性关系图 |
| GET | `/statistic/vessel/{vessel_id}/cii` | vessel_data_per_day | 年内每日 CII + 评级 |
| GET | `/statistic/vessel/{vessel_id}/completeness` | vessel_data_per_day | 近5年月度数据完整度 |
| GET | `/statistic/vessel/{vessel_id}/date-range` | vessel_standard_data | 时段明细（支持降采样） |
| GET | `/statistic/consumption/nmile` | vessel_data_per_day | 每海里油耗（me/dg/blr） |
| GET | `/statistic/consumption/total` | vessel_data_per_day | 总油耗（me/dg/blr） |

### 优化建议（`/optimization`）

| 方法 | 路径 | 依赖 | 说明 |
|------|------|------|------|
| GET | `/optimization/vessel/{vessel_id}/values` | vessel/meta 服务 | 时段均速、CII 及评级 |
| GET | `/optimization/vessel/{vessel_id}/average` | — | 平均对水航速 + 每海里油耗 |
| GET | `/optimization/vessel/{vessel_id}/consumption-total` | — | 总油耗（同 statistic） |
| GET | `/optimization/trim-data/{vessel_id}` | vessel/meta 服务 | 逐日 trim + 均值 + CII |
| GET | `/optimization/optimize-speed/{vessel_id}` | vessel/meta + ML模型 | 航速优化建议（需 XGBoost 模型） |
| GET | `/optimization/optimize-trim/{vessel_id}` | vessel/meta + ML模型 | 吃水差优化建议（需 XGBoost 模型） |

---

## 通用查询参数

### attribute_name（属性名称）

`attribute-frequencies` / `attribute-values` / `attribute-relation` 端点接受以下属性名（经白名单校验）：

**vessel_standard_data 可用属性**

| 属性名 | 含义 |
|--------|------|
| `speed_ground` | 对地航速 |
| `speed_water` | 对水航速 |
| `draft` | 平均吃水 |
| `heel` | 横倾角 |
| `trim` | 吃水差 |
| `me_rpm` | 主机转速 |
| `me_shaft_power` | 主机轴功率 |
| `me_fuel_consumption_nmile` | 每海里油耗 |
| `slip_ratio` | 滑失比 |
| `wind_speed` | 风速 |
| ... | （共 22 个字段） |

**vessel_data_per_day 额外可用属性**

| 属性名 | 含义 |
|--------|------|
| `me_hfo_act_cons` | 主机 HFO 实际消耗 |
| `me_mgo_act_cons` | 主机 MGO 实际消耗 |
| `dg_hfo_act_cons` | 发电机 HFO 消耗 |
| `blr_hfo_act_cons` | 锅炉 HFO 消耗 |
| `cii_temp` | 当日 CII 分子 |
| `cii` | 累积 CII |
| ... | （共 26 个字段） |

> 传入白名单以外的值（如 `DROP TABLE`）将返回 **400**。

### fuel_type（燃料类型）

`consumption/nmile` 和 `consumption/total` 端点的 `fuel_type` 参数：`hfo` | `mgo` | `lfo` | `mdo`

---

## CII 评级（IMO 标准）

`cii_rating.py` 实现 IMO 2023 CII 计算，纯 Python，无外部依赖。

### 评级边界（2023 年减排因子）

```
A ──── superior ──── B ──── lower ──── C ──── upper ──── D ──── inferior ──── E
```

### 支持的船型代码

| 代码 | 船型 | 基准参数 |
|------|------|----------|
| `I001` | 散货船 (Bulk Carrier) | DWT（上限 279,000） |
| `I002` | 气体运输船 (Gas Carrier) | DWT |
| `I003` | 油轮 (Tanker) | DWT |
| `I004` | 集装箱船 (Container Ship) | DWT |
| `I005` | 杂货船 (General Cargo) | DWT |
| `I006` | 冷藏货船 (Refrigerated Cargo) | DWT |
| `I007` | 组合运输船 (Combination Carrier) | DWT |
| `I009` | LNG 运输船 | GT（上限 57,700） |
| `I010` | 滚装客轮 (Ro-Ro Passenger) | GT |
| `I011` | 滚装货船 (Ro-Ro Cargo) | GT |
| `I012` | 客轮 (Cruise Passenger) | GT |
| `B001`–`B010` | 散货细分类型 | DWT |
| `C001`–`C014` | 集装箱细分类型 | DWT |

> 未知船型代码返回评级 `"N/A"`。

---

## ML 优化模型

### 航速优化（optimize-speed）

端点读取 `{MODELS_DIR}/{vessel_id}_XGBoost_v*_(all|less).pkl`，选择最高版本：

- `all` 模型：包含主机功率特征（RPM、轴功率、滑失比）
- `less` 模型：仅使用基础气象/航行特征

对当前平均航速 ±25%（步长 2.5%）共 20 个档位预测油耗和 CII，返回对比表。

### 吃水差优化（optimize-trim）

端点读取 `{MODELS_DIR}/{vessel_id}_trim_*.pkl`，对当前平均吃水差 -2.0 ～ +2.0（步长 0.5）共 9 个档位预测油耗和 CII。

**部署模型文件：**

```bash
# 将模型文件放到 MODELS_DIR 目录（默认 ./models）
ls models/
# 1_XGBoost_v2_all.pkl
# 1_XGBoost_v2_less.pkl
# 1_trim_v1.pkl
```

> 未找到模型文件时端点返回 **404**，不影响其他统计端点。

---

## 跨服务依赖

```
analytics ──GET /vessel/{id}──────► vessel 服务（端口 8002）
              返回: dead_weight, gross_tone, ship_type (int), pitch

analytics ──GET /meta/ship_type──► meta 服务（端口 8000）
              返回: [{id, code}]   # 如 {4: "I004"}，进程内缓存
```

两个服务均不可用时：
- vessel 不可用 → 返回 503（连接失败）或 502（服务端错误）
- meta 不可用 → 使用空映射（ship_type_code 退化为 `"I001"`）

---

## 本地运行

```bash
# 1. 先启动 data 服务（生成 DuckDB 文件）
cd apps/data && uv run uvicorn data.app:app --reload --port 8003

# 2. 配置 analytics 环境
cd apps/analytics
cp .env.example .env
# 编辑 .env 设置 DUCK_DB_PATH（指向 data 服务的 DuckDB 文件）

# 3. 启动 analytics 服务
uv run uvicorn analytics.app:app --reload --host 0.0.0.0 --port 8004
```

### 查询示例

```bash
# 属性频次（直方图数据）
curl "http://localhost:8004/statistic/attribute-frequencies?attribute_name=speed_water&vessel_id=1&start_date=2024-01-01&end_date=2024-03-31"

# 日均值散点图
curl "http://localhost:8004/statistic/attribute-values?attribute_name=me_shaft_power&vessel_id=1&start_date=2024-01-01&end_date=2024-03-31"

# CII 数据（近一年）
curl "http://localhost:8004/statistic/vessel/1/cii"

# 总油耗（HFO）
curl "http://localhost:8004/statistic/consumption/total?fuel_type=hfo&vessel_id=1&start_date=2024-01-01&end_date=2024-03-31"

# 航速优化建议
curl "http://localhost:8004/optimization/optimize-speed/1?start_date=2024-01-01&end_date=2024-03-31"
```

---

## 测试

```bash
uv run pytest -v
```

18 个测试覆盖：健康检查、CII 纯函数（4个）、统计端点（9个）、优化端点（4个）。

> **注意**：`test_optimize_speed_no_model` 和 `test_optimize_trim` 类测试在没有 ML 模型的环境中也能正常运行，分别验证 404 响应和 mock 路径。

---

## 配置（.env）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DUCK_DB_PATH` | `../data/data.duckdb` | data 服务的 DuckDB 文件路径（只读访问） |
| `VESSEL_SERVICE_URL` | `http://localhost:8002` | vessel 服务地址 |
| `META_SERVICE_URL` | `http://localhost:8000` | meta 服务地址 |
| `MODELS_DIR` | `./models` | XGBoost pkl 模型目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
