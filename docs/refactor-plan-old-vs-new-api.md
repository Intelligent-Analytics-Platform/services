# backend -> services 重构分析与落地计划

- 更新时间: 2026-03-14
- 分析依据:
  - `docs/api-compare-old-vs-refactor.md`
  - `docs/api-result-compare-old-vs-refactor.md`
  - `/Users/lee/backend/app/main.py`
  - `/Users/lee/backend/app/modules/*/router.py`
  - `apps/*/*/router.py`
  - `apps/*/tests/*.py`

## 1. 项目形态判断

- `/Users/lee/backend` 是单体 FastAPI 应用，主入口统一挂载 `meta/company/user/vessel/upload/statistic/optimization/reminder/calculate/route_optimization` 模块。
- `/Users/lee/services` 是基于 uv workspace 的微服务 monorepo，把原单体拆成 `meta`、`identity`、`vessel`、`data`、`analytics` 五个服务，并将通用能力下沉到 `libs/common`。
- 这次重构不是简单目录搬迁，而是一次职责重划分：身份、元数据、船舶主数据、上传流水、分析计算已经解耦，部分旧接口通过兼容端点保留，部分接口通过路径规范化迁移，部分能力尚未落地。

## 2. 模块映射结论

| backend 模块 | services 归属 | 当前状态 | 说明 |
|---|---|---|---|
| `meta` | `apps/meta` | 已迁移 | 元数据查询已完成，接口语义基本稳定。 |
| `company` + `user` | `apps/identity` | 已迁移 | 公司、用户、登录、JWT 已拆出；`GET /company/{company_id}/vessels` 已做兼容端点。 |
| `vessel` | `apps/vessel` | 已迁移但响应有变化 | 新服务聚焦主数据，旧系统里拼装的 CII/状态字段不再直接内嵌。 |
| `upload` | `apps/data` | 已迁移且语义变化 | 上传由同步处理改为 `202 + 后台异步 + status 查询`。 |
| `statistic` | `apps/analytics` | 已迁移 | 统计类接口基本齐全，部分查询参数默认值和文案发生变化。 |
| `optimization` | `apps/analytics` | 已迁移但路径重构 | `/{vessel_id}/values|average|consumption-total` 规范化为 `/vessel/{vessel_id}/*`。 |
| `calculate` | 无 | 未迁移 | `POST /calculate/cii` 仍缺失。 |
| `reminder` | 无 | 未迁移 | 4 个提醒接口未在微服务侧落地。 |
| `route_optimization` | 无 | 未迁移 | 航线优化仍停留在旧单体。 |
| 通用认证/异常/仓储/日志 | `libs/common` | 已抽离 | 这是重构的核心收益，降低了各服务重复代码。 |

## 3. 当前最重要的差异

### 已经完成但文档容易误判的项

- `GET /company/{company_id}/vessels` 已在 `identity` 保留，不应继续当作缺口。
- `GET /optimization/{vessel_id}/values|average|consumption-total` 是路径规范化，不是能力缺失。

### 真实缺口

- `reminder` 四个接口尚未决定去向。
- `route_optimization` 四个接口尚未拆分到新服务。
- `POST /calculate/cii` 尚无替代入口。
- 聚合指标接口 `GET /metrics` 未提供统一外部契约。

### 兼容性风险

- `POST /upload/vessel/{vessel_id}/standard` 从同步 `200` 变为异步 `202`，调用方必须接受任务化处理。
- `GET /vessel` / `GET /vessel/{id}` 不再内联旧单体中的 `latest_cii`、`cii_rating`、`engine_state`、`hull_propeller_state` 等聚合字段。
- 运行结果对比文档中部分数据差异来自旧快照或部署状态，不能直接作为当前代码事实。

## 4. 落地策略

### P0：先收敛契约，再决定补功能还是下线

- 统一一份“旧接口去向表”，逐条标记为 `兼容保留`、`路径迁移`、`新建服务`、`确认下线`。
- 对前端仍在使用的旧路径，优先在网关/BFF 或兼容路由层兜底，不反向污染内部服务边界。
- 明确 `upload` 的异步契约，把 `202 + /upload/{upload_id}/status` 作为标准流程写入文档。

### P1：补最影响上线的兼容层

- 为 `/optimization/{vessel_id}/values|average|consumption-total` 增加兼容入口或映射。
- 为 `vessel` 视图准备聚合层方案：若前端仍依赖旧字段，应由 BFF/analytics 聚合而不是回填进 vessel 基础服务。
- 统一 OpenAPI 中 `422/400/404` 的文档响应，避免 SDK 生成抖动。

### P2：处理遗留能力去留

- `reminder`：判断是否并入 `analytics`，还是单独保留为后续服务。
- `route_optimization`：单独评估依赖（天气、图算法、模型文件、历史航次数据），更适合拆成独立服务，而不是塞回 analytics。
- `calculate/cii`：如果只是纯算法入口，可作为 analytics 的纯计算端点补回；如果没有实际调用方，可直接下线。

### P3：把对比变成持续验证

- 将现有接口对比与结果对比脚本纳入 CI 或发布前检查。
- 补足兼容性回归测试，覆盖 `company/user/vessel/upload/statistic/optimization` 主链路。
- 对所有“文档写了已迁移”的接口至少保留一条自动化测试，避免再次出现文档领先或落后于代码。

## 5. 验收标准

- 所有旧接口都有明确去向，不再出现“待迁移/已废弃”这种未决描述。
- 前端主链路在不修改或只做最小修改的前提下可完成登录、公司、船舶、上传、分析页面联调。
- `upload`、`optimization`、`vessel` 的关键兼容差异在文档和测试中均被显式覆盖。
- reminder、route optimization、calculate 三块历史能力有最终结论：迁移方案、独立服务方案或下线方案。

## 6. 建议执行顺序

1. 修正文档中的过期结论，先让团队对当前状态达成一致。
2. 输出旧接口去向表，并确认哪些路径必须兼容一个发布周期。
3. 优先补 optimization 旧路径兼容和 upload 异步迁移说明。
4. 再决定 reminder / route optimization / calculate 的最终归宿。