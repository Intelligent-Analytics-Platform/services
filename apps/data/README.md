# Data 数据服务

船舶能效分析平台的遥测数据微服务，负责 CSV 上传、数据清洗、存储和 CII 计算。

- **端口**：`8003`
- **OpenAPI 文档**：`http://localhost:8003/docs`

---

## 架构概览

### 双数据库设计

```
┌─────────────────────────────────────────────────────────┐
│  POST /upload/vessel/{id}/standard                       │
│  → 立即返回 202  →  BackgroundTask                       │
└──────────────────────────────┬──────────────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │         DataService              │
              │  1. read_csv  → DataFrame        │
              │  2. insert original data         │
              │  3. data_preparation (pipeline)  │
              │  4. insert standard data         │
              │  5. upsert per-day aggregates    │
              │  6. calculate CII_temp           │
              │  7. calculate CII (window fn)    │
              └────────┬───────────────┬─────────┘
                       │               │
         ┌─────────────▼──┐    ┌───────▼──────────────────┐
         │  SQLite         │    │  DuckDB                   │
         │  (SQLAlchemy)   │    │  (嵌入式列式 OLAP)        │
         │                 │    │                           │
         │ vessel_data_    │    │ vessel_original_data      │
         │   upload        │    │ vessel_standard_data      │
         │ (上传记录 CRUD) │    │ vessel_data_per_day       │
         └─────────────────┘    └───────────────────────────┘
```

### 关键设计决策

| 旧方案（backend）| 新方案（data service）| 原因 |
|---|---|---|
| `asyncio.wait_for(process, timeout=1800)` | `BackgroundTasks.add_task(...)` + 立即返回 202 | 避免请求阻塞 30 分钟 |
| `session.bulk_insert_mappings()` *(deprecated)* | `INSERT INTO table BY NAME SELECT * FROM df` | DuckDB 直接识别 pandas DataFrame，零行循环 |
| Python 循环计算 CII | SQL 窗口函数 `AVG(cii_temp) OVER (PARTITION BY vessel_id, YEAR(date) ORDER BY date ...)` | 逻辑更清晰，性能更好 |
| MySQL `INFORMATION_SCHEMA` 查询燃料列 | 约定式列名（`_act_cons` 后缀） | 去除 MySQL 特定代码，支持跨库 |

---

## 数据流

```
CSV 文件
  │
  ▼ pd.read_csv()
原始 DataFrame (60+ 列)
  │
  ├──► vessel_original_data (DuckDB) ← 保留完整原始数据
  │
  ▼ data_preparation(df, pitch)
      ├── normalize_columns()    # PascalCase → snake_case 列名映射
      ├── data_nulls()           # 删除含 null 行
      ├── 类型强制转换            # pd.to_numeric()
      ├── draft_calculation()    # 平均吃水 = (艉吃水 + 艏吃水) / 2
      ├── slip_ratio_calculation() # 滑失比 = (1 - 水速/(RPM×螺距×60)) × 100
      ├── ship_nmile_calculation() # 每海里油耗
      ├── data_abnormal_removal()  # 剔除传感器异常值
      └── data_filtering()         # 操作状态过滤 (RPM≥35, 水速≥3kn)
  │
  ├──► vessel_standard_data (DuckDB) ← 清洗后数据
  │
  ▼ groupby("date").mean()
日均聚合
  │
  ├──► vessel_data_per_day (DuckDB, upsert)
  │
  ▼ CII 计算 (若提供 vessel_capacity)
      ├── CII_temp = Σ (cons/speed_water) × (CF×1000/C)
      └── CII = 年内累积均值 (SQL窗口函数)
```

---

## 实体关系

```
                         vessel 服务
                         ──────────
                         vessel.id ◄─────── vessel_id (跨服务引用，无 DB FK)
                                    │
              ┌────────────────────┼──────────────────────┐
              │                    │                      │
              ▼                    ▼                      ▼
  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────┐
  │ VesselDataUpload│  │vessel_original_   │  │vessel_data_per_day   │
  │ (SQLite)        │  │data (DuckDB)      │  │(DuckDB)              │
  │─────────────────│  │───────────────────│  │──────────────────────│
  │ id (PK)         │  │ id (PK, BIGINT)   │  │ vessel_id (PK)       │
  │ vessel_id       │  │ vessel_id         │  │ date      (PK)       │
  │ file_path       │  │ date              │  │ speed_ground/water   │
  │ date_start      │  │ speed_water       │  │ me_shaft_power       │
  │ date_end        │  │ me_rpm            │  │ me_rpm               │
  │ status          │  │ ... (60+ 列)      │  │ *_act_cons (各燃油)  │
  │ error_message   │  │ created_at        │  │ cii_temp             │
  │ completed_at    │  └───────────────────┘  │ cii                  │
  └─────────────────┘                         └──────────────────────┘
       status 枚举:                  同结构:
       pending → processing         vessel_standard_data (DuckDB)
       → done | failed
```

---

## 目录结构

```
apps/data/
├── data/
│   ├── app.py          # FastAPI 入口，lifespan 负责建表（SQLite + DuckDB）
│   ├── config.py       # Settings: database_url, duck_db_path, upload_dir 等
│   ├── database.py     # SQLite engine + DuckDB init + get_duck_conn()
│   ├── models.py       # SQLAlchemy ORM（仅 VesselDataUpload）
│   ├── pipeline.py     # 数据清洗函数（从 backend/core/data_utils.py 迁移）
│   ├── repository.py   # UploadRepository（CRUD + 分页）
│   ├── schemas.py      # Pydantic schema（UploadAccepted, UploadStatusSchema, DailyDataSchema）
│   ├── service.py      # DataService（上传入口 + 后台处理管道）
│   └── router.py       # 4 个端点
├── tests/
│   ├── conftest.py     # in-memory SQLite + temp DuckDB fixtures
│   └── test_data_api.py
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## API 端点

| 方法 | 路径 | 状态码 | 说明 |
|------|------|--------|------|
| POST | `/upload/vessel/{vessel_id}/standard` | 202 | 上传 CSV，立即返回，后台异步处理 |
| GET  | `/upload/vessel/{vessel_id}/history`  | 200 | 上传历史列表（支持分页） |
| GET  | `/upload/{upload_id}/status`          | 200 | 查询处理状态（轮询用） |
| GET  | `/daily/vessel/{vessel_id}`           | 200 | 日均数据（含 CII，支持分页） |

### 上传端点参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file` | UploadFile | 必填 | CSV 文件（最大 100 MB） |
| `pitch` | float | `6.058` | 螺旋桨螺距（用于滑失比计算） |
| `vessel_capacity` | float \| None | `None` | 船舶吨位（载重吨或总吨），不提供则跳过 CII 计算 |

### 上传状态流转

```
pending → processing → done
                    └→ failed  (error_message 字段记录原因)
```

---

## CSV 格式要求

### 支持的列名格式

`pipeline.normalize_columns()` 自动将数据采集系统输出的 **PascalCase 列名**映射为管道内部的 **snake_case 名**，两种格式均可上传：

| CSV 列名（PascalCase）| 内部字段名（snake_case）|
|---|---|
| `PCDate` | `date` |
| `PCTime` | `time` |
| `ShipSpdToWater` | `speed_water` |
| `ShipSpd` | `speed_ground` |
| `ShipDraughtBow` | `draught_bow` |
| `ShipDraughtAstern` | `draught_astern` |
| `ShipTrim` | `trim` |
| `MERpm` | `me_rpm` |
| `MEShaftPow` | `me_shaft_power` |
| `MESFOC_kw` | `me_fuel_consumption_kwh` |
| `MESFOC_nmile` | `me_fuel_consumption_nmile` |
| `MEActFOCons` | `me_hfo_act_cons` |
| `MEActMGOCons` | `me_mgo_act_cons` |
| `DGActFOCons` | `dg_hfo_act_cons` |
| `BlrActFOCons` | `blr_hfo_act_cons` |
| `BlrActMGOCons` | `blr_mgo_act_cons` |
| `WindSpd` | `wind_speed` |
| `WindDir` | `wind_direction` |
| `Latitude` / `Longitude` | `latitude` / `longitude` |

> **注意**：未在映射表中的列（如 `ShipSlip`、`ShipDraft`、`windPower`）会在写入 DuckDB 时自动跳过（`PRAGMA table_info` 列名白名单过滤）。

### CII 计算前提

CII 依赖燃油实际消耗列（`me_hfo_act_cons`、`dg_hfo_act_cons` 等）。
若上传的 CSV 不含这些列（如预处理后的汇总文件），则 `cii_temp` 和 `cii` 字段将保持 `0.0`，查询时返回 `null`。

---

## 数据清洗规则（pipeline.py）

### 异常值过滤（data_abnormal_removal）

| 字段 | 规则 |
|------|------|
| `me_fuel_consumption_nmile` | 0 < 值 < 250 |
| `me_shaft_power` | 0 < 值 < 8000 kW |
| `me_rpm` | 值 < 2000 且 ≠ 0 |
| `draft` | 值 > 0 |
| `speed_ground` | 值 ≥ 3 且 ≠ 88888（无效标记） |
| `wind_speed` | 值 < 60 m/s |
| `me_fuel_consumption_kwh` | 值 ≥ 0 |

### 操作状态过滤（data_filtering）

| 字段 | 规则 | 含义 |
|------|------|------|
| `me_rpm` | ≥ 35 | 主机运行中 |
| `speed_water` | ≥ 3 kn | 实际航行 |
| `slip_ratio` | -20% ~ 100% | 正常滑失范围 |

### CO2 排放因子（get_cf）

| 燃油 | CF (t CO2 / t fuel) |
|------|---------------------|
| HFO  | 3.114 |
| LFO  | 3.151 |
| MGO/MDO | 3.206 |
| LNG  | 2.75 |
| LPG-P | 3.0 |
| LPG-B | 3.03 |
| 甲醇 | 1.375 |
| 乙醇 | 1.913 |
| 乙烷 | 2.927 |

---

## 本地运行

```bash
cp .env.example .env
uv run uvicorn data.app:app --reload --port 8003
```

首次启动自动建表（SQLite + DuckDB），无 seed 数据。

### 上传示例

```bash
# 上传 CSV
curl -F "file=@vessel_data.csv" \
     "http://localhost:8003/upload/vessel/1/standard?pitch=6.058&vessel_capacity=50000"
# → 202 {"data": {"upload_id": 1}, "message": "上传成功，后台处理中"}

# 轮询状态（直到 done）
curl "http://localhost:8003/upload/1/status"
# → {"data": {"status": "done", "date_start": "2024-01-15", ...}}

# 查询日均数据
curl "http://localhost:8003/daily/vessel/1?limit=30"
```

---

## 测试

```bash
uv run pytest -v
```

15 个测试覆盖：健康检查、上传 202、空文件/非 CSV 400、历史分页、状态 404、日均数据、pipeline 单元测试。

### 端到端测试（真实 CSV）

```bash
# 使用真实数据抽样（前 200 行）进行端到端验证
head -201 /path/to/b2022_cleaned.csv > /tmp/test_sample.csv

curl -F "file=@/tmp/test_sample.csv" \
     "http://localhost:8003/upload/vessel/1/standard?pitch=6.058"
# → 202 {"data": {"upload_id": 1}, "message": "上传成功，后台处理中"}

# 轮询直到 done
curl "http://localhost:8003/upload/1/status"
# → {"status": "done", "date_start": "2022-01-01", "date_end": "2022-01-08"}

curl "http://localhost:8003/daily/vessel/1?limit=5"
# → 返回日均数据，缺失燃油列的字段显示 null（不影响其他字段）
```

---

## 配置（.env）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./data.db` | SQLite 连接串（上传记录） |
| `DUCK_DB_PATH` | `./data.duckdb` | DuckDB 文件路径（遥测数据） |
| `UPLOAD_DIR` | `uploads` | CSV 文件存储目录 |
| `MAX_FILE_SIZE` | `104857600` | 最大上传文件大小（字节，默认 100MB） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
