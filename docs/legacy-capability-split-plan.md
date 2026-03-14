# reminder / route_optimization / calculate 拆分方案

更新时间：2026-03-14

## 结论摘要

| 能力 | 建议归宿 | 原因 | 优先级 |
|---|---|---|---|
| `reminder` | 并入 `analytics` | 只读分析类接口，依赖船舶维护日期与标准数据，天然属于分析域 | P1 |
| `route_optimization` | 拆成独立服务 | 依赖栈极重，运行时资源模型和 analytics 完全不同 | P2 |
| `calculate/cii` | 先补到 `analytics`，算法继续沉到公共模块 | 纯计算、无数据库依赖，适合作为轻量兼容端点恢复 | P1 |

## 1. reminder

### 当前依赖

- 读取 `Vessel` 维护日期：`hull_clean_date`、`newly_paint_date`、`propeller_polish_date`、`engine_overhaul_date`
- 读取 `VesselStandardData`、`VesselDataPerDay`
- 读取 `PowerSpeedCurve`、`CurveData`
- 主要是 pandas/numpy 计算与图表数据组装，没有外部天气、图搜索、异步任务依赖

### 为什么适合并入 analytics

- reminder 本质是状态评估和分析结果展示，不是主数据写入。
- 它需要的数据已经分散在 `vessel` 主数据和 `data` 采集数据之间，由 analytics 做只读聚合最自然。
- 当前 analytics 已具备 DuckDB 只读分析、跨服务查询和纯计算模式，迁入后边界一致。

### 推荐拆法

1. 在 `analytics` 新增 `reminder_router`，路径保持 `/reminder/*` 兼容旧前端。
2. 将旧服务中基于 `VesselStandardData` / `VesselDataPerDay` 的查询改写为从 DuckDB 读取。
3. 对维护日期、试航曲线等主数据，通过 `vessel` 服务查询，而不是直接连 vessel 库。
4. 把通用计算逻辑拆成纯函数，方便单元测试和后续复用。

### 风险点

- 旧实现直接 join 了 vessel 模型与曲线表，迁移后会涉及跨服务数据拼装。
- 试航曲线数据如果当前 `vessel` 服务 API 没有暴露，需要先补只读接口。
- 图表返回结构历史包袱较重，建议优先保留旧响应，内部再慢慢整理。

### 最小可执行计划

- 第一步恢复 `/reminder/{vessel_id}/values`
- 第二步恢复 `/reminder/{vessel_id}/graph`
- 第三步恢复 `/reminder/{vessel_id}/engine` 和 `/monthly-power-ranges-sfoc`
- 第四步补 4 组兼容测试，并和旧返回结构做样本比对

## 2. route_optimization

### 当前依赖

- 算法层依赖：`geopandas`、`shapely`、`networkx`、`xarray`、`scipy`、`numba`、`joblib`
- 运行时依赖：海图/水深数据、天气数据抓取、历史航次数据、图缓存与模型文件
- 内存与启动成本高：存在大体积图缓存、长时间预热、线程锁、天气缓存等机制

### 为什么不适合直接并入 analytics

- analytics 当前是“只读 DuckDB + 轻量 HTTP 调用 + ML 模型按需加载”的分析服务；route optimization 是高计算、高内存、高外部依赖的规划服务。
- 二者的伸缩策略不同：analytics 更像查询服务，route optimization 更像任务型计算服务。
- 强行并入会把 analytics 镜像、启动时长、依赖复杂度显著抬高，拖慢已有稳定能力。

### 推荐拆法

1. 新建独立 `route` 或 `routing` 服务。
2. 先原样迁移旧接口：`/route-optimization/plan-all`、`/get-shortest-route`、`/ship-route-planner`、`/historical-routes`。
3. 先保持输入输出兼容，不在第一阶段重写算法。
4. 把天气抓取、图缓存、历史航次查询拆成内部模块，逐步替换旧单体直接访问模型的方式。

### 前置条件

- 盘点模型文件、GEBCO 数据、天气缓存目录、历史航次表结构。
- 明确部署资源：CPU、内存、磁盘缓存位置。
- 评估哪些流程应该改成异步任务，而不是同步 HTTP 长请求。

### 最小可执行计划

- 第一步只恢复 `get-shortest-route`
- 第二步恢复 `ship-route-planner` 与 `plan-all`
- 第三步迁移 `historical-routes` 与航次对账逻辑
- 第四步补超时、缓存和资源限制策略

## 3. calculate/cii

### 当前依赖

- `CalculateService` 只调用纯算法 `calculate_cii_full`
- 无数据库依赖
- 输入是 `year`、`ship_type`、`dwt/gt`、`sailing_distance`、`fuel_list`

### 推荐归宿

- 对外接口先补在 `analytics`，因为它已经承载 CII 相关查询和评级逻辑。
- 算法本身建议沉到 `libs/common` 或 analytics 内的纯函数模块，不和 HTTP 层耦合。

### 推荐拆法

1. 在 `analytics` 新增 `/calculate/cii` 兼容端点。
2. 复用已有 CII 纯函数，不新增数据库访问。
3. 增加独立单元测试，确保与旧单体输出一致。

### 决策建议

- 如果前端仍有独立 CII 计算器页面，应尽快恢复该端点。
- 如果没有真实调用方，可仅保留内部函数，不暴露 HTTP 端点。

## 4. 建议实施顺序

1. 先补 `calculate/cii`，投入最小、收益直接。
2. 再把 `reminder` 并入 `analytics`，优先恢复读取型接口。
3. 最后独立拆 `route_optimization`，单独规划资源和部署。