# 旧接口去向表

更新时间：2026-03-14

说明：本表以 `/Users/lee/backend` 的旧接口为基准，标识它们在 `/Users/lee/services` 中的当前去向。状态定义如下：

- `已迁移`：新项目已有对应接口，路径和用途基本一致
- `已兼容`：新项目保留了旧路径，或已有兼容入口
- `路径重构`：能力已存在，但推荐调用新路径
- `未迁移`：当前 services 侧没有对等能力
- `待决策`：是否保留仍需业务确认

| 旧接口 | backend 模块 | 当前归属 | 状态 | 建议动作 | 备注 |
|---|---|---|---|---|---|
| `GET /` | root | `analytics` | 已迁移 | 保持 | 新项目健康检查拆到各服务；聚合入口是否保留待定 |
| `GET /company` | company | `identity` | 已迁移 | 保持 | 文档 422 响应可继续补齐 |
| `POST /company` | company | `identity` | 已迁移 | 保持 |  |
| `GET /company/{company_id}` | company | `identity` | 已迁移 | 保持 |  |
| `PUT /company/{company_id}` | company | `identity` | 已迁移 | 保持 |  |
| `DELETE /company/{company_id}` | company | `identity` | 已迁移 | 保持 |  |
| `GET /company/{company_id}/vessels` | company | `identity` | 已兼容 | 保留一个发布周期 | 已有兼容端点 |
| `GET /user` | user | `identity` | 已迁移 | 保持 |  |
| `POST /user/register` | user | `identity` | 已迁移 | 保持 |  |
| `POST /user/login` | user | `identity` | 已迁移 | 保持 |  |
| `GET /user/{user_id}` | user | `identity` | 已迁移 | 保持 |  |
| `PUT /user/{user_id}` | user | `identity` | 已迁移 | 保持 |  |
| `DELETE /user/{user_id}` | user | `identity` | 已迁移 | 保持 |  |
| `GET /vessel` | vessel | `vessel` | 已迁移 | 增加聚合说明 | 旧聚合字段未内联返回 |
| `POST /vessel` | vessel | `vessel` | 已迁移 | 保持 |  |
| `GET /vessel/{vessel_id}` | vessel | `vessel` | 已迁移 | 增加聚合说明 | 旧聚合字段未内联返回 |
| `PUT /vessel/{vessel_id}` | vessel | `vessel` | 已迁移 | 保持 |  |
| `DELETE /vessel/{vessel_id}` | vessel | `vessel` | 已迁移 | 保持 |  |
| `GET /meta/fuel_type` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /meta/ship_type` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /meta/time_zone` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /meta/attributes` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /meta/attribute_mapping` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /meta/fuel_type_category` | meta | `meta` | 已迁移 | 保持 |  |
| `GET /upload/vessel/{vessel_id}/history` | upload | `data` | 已迁移 | 保持 |  |
| `POST /upload/vessel/{vessel_id}/standard` | upload | `data` | 已迁移 | 更新调用方 | 已变为 `202 + status 查询` |
| `GET /statistic/attribute-frequencies` | statistic | `analytics` | 已迁移 | 保持 | 默认参数语义有细微变化 |
| `GET /statistic/attribute-values` | statistic | `analytics` | 已迁移 | 保持 | 默认参数语义有细微变化 |
| `GET /statistic/attribute-relation` | statistic | `analytics` | 已迁移 | 保持 | 默认参数语义有细微变化 |
| `GET /statistic/consumption/nmile` | statistic | `analytics` | 已迁移 | 保持 |  |
| `GET /statistic/consumption/total` | statistic | `analytics` | 已迁移 | 保持 |  |
| `GET /statistic/vessel/{vessel_id}/cii` | statistic | `analytics` | 已迁移 | 保持 |  |
| `GET /statistic/vessel/{vessel_id}/completeness` | statistic | `analytics` | 已迁移 | 保持 |  |
| `GET /statistic/vessel/{vessel_id}/date-range` | statistic | `analytics` | 已迁移 | 保持 |  |
| `GET /optimization/optimize-speed/{vessel_id}` | optimization | `analytics` | 已迁移 | 保持 |  |
| `GET /optimization/optimize-trim/{vessel_id}` | optimization | `analytics` | 已迁移 | 保持 |  |
| `GET /optimization/trim-data/{vessel_id}` | optimization | `analytics` | 已迁移 | 保持 |  |
| `GET /optimization/{vessel_id}/values` | optimization | `analytics` | 已兼容 | 对外公告规范路径 | 规范路径为 `/optimization/vessel/{vessel_id}/values` |
| `GET /optimization/{vessel_id}/average` | optimization | `analytics` | 已兼容 | 对外公告规范路径 | 规范路径为 `/optimization/vessel/{vessel_id}/average` |
| `GET /optimization/{vessel_id}/consumption-total` | optimization | `analytics` | 已兼容 | 对外公告规范路径 | 规范路径为 `/optimization/vessel/{vessel_id}/consumption-total` |
| `GET /reminder/{vessel_id}/values` | reminder | 无 | 未迁移 | 并入 analytics | 建议优先恢复 |
| `GET /reminder/{vessel_id}/graph` | reminder | 无 | 未迁移 | 并入 analytics | 依赖试航曲线和日均数据 |
| `GET /reminder/{vessel_id}/engine` | reminder | 无 | 未迁移 | 并入 analytics | 读取型分析接口 |
| `GET /reminder/{vessel_id}/monthly-power-ranges-sfoc` | reminder | 无 | 未迁移 | 并入 analytics | 读取型分析接口 |
| `POST /calculate/cii` | calculate | 无 | 未迁移 | 补到 analytics | 纯计算接口 |
| `POST /route-optimization/get-shortest-route` | route_optimization | 无 | 未迁移 | 拆独立服务 | 高计算、高依赖 |
| `POST /route-optimization/historical-routes` | route_optimization | 无 | 未迁移 | 拆独立服务 | 依赖历史航次识别 |
| `POST /route-optimization/plan-all` | route_optimization | 无 | 未迁移 | 拆独立服务 | 复合规划入口 |
| `POST /route-optimization/ship-route-planner` | route_optimization | 无 | 未迁移 | 拆独立服务 | 复合规划入口 |
| `GET /metrics` | root | 无 | 待决策 | 明确是否对外暴露 | 当前更像内部观测能力 |