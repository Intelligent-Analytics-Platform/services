# 老服务与重构后 API 对比报告

- 生成时间: 2026-03-08 20:21:40
- 老服务 OpenAPI: `http://localhost:8000/openapi.json`
- 新服务 OpenAPI:
  - `meta`: `http://localhost:9000/openapi.json`
  - `identity`: `http://localhost:9001/openapi.json`
  - `vessel`: `http://localhost:9002/openapi.json`
  - `data`: `http://localhost:9004/openapi.json`
  - `analytics`: `http://localhost:9005/openapi.json`

## 总览

- 老服务接口数(method+path): **50**
- 重构后接口数(method+path): **41**
- 完全匹配接口数: **36**
- 仅老服务存在: **14**
- 仅重构后存在: **5**
- 匹配但签名有差异: **21**

## 代码审阅修正（2026-03-14）

- 本文顶部统计来自 2026-03-08 的自动对比快照，不等同于当前代码现状。
- `GET /company/{company_id}/vessels` 已在 `identity` 服务补齐兼容端点，旧报告中标记为 `仅老服务` 已过期。
- `GET /optimization/{vessel_id}/values|average|consumption-total` 不是能力缺失，而是路径规范化到了 `analytics` 服务的 `/optimization/vessel/{vessel_id}/*`。
- `2026-03-14` 已在 `analytics` 服务补充旧 optimization 路径兼容入口，因此这 3 个接口现在既有新路径，也保留旧路径访问能力。
- 因此阅读本报告时，需要把“严格 path+method 对比”和“能力是否已迁移”分开判断。

## 一一对比（按老服务接口）

| 老接口 | 重构后状态 | 归属服务 | 备注 |
|---|---|---|---|
| `DELETE /company/{company_id}` | 一致 | `identity` |  |
| `DELETE /user/{user_id}` | 一致 | `identity` |  |
| `DELETE /vessel/{vessel_id}` | 一致 | `vessel` |  |
| `GET /` | 有差异 | `analytics` | summary |
| `GET /company` | 有差异 | `identity` | responses |
| `GET /company/{company_id}` | 一致 | `identity` |  |
| `GET /company/{company_id}/vessels` | 一致 | `identity` | 已在 identity 保留兼容端点 |
| `GET /meta/attribute_mapping` | 有差异 | `meta` | responses |
| `GET /meta/attributes` | 有差异 | `meta` | responses |
| `GET /meta/fuel_type` | 有差异 | `meta` | responses |
| `GET /meta/fuel_type_category` | 有差异 | `meta` | responses |
| `GET /meta/ship_type` | 有差异 | `meta` | responses |
| `GET /meta/time_zone` | 有差异 | `meta` | responses |
| `GET /metrics` | 仅老服务 | - | 待迁移/已废弃 |
| `GET /optimization/optimize-speed/{vessel_id}` | 有差异 | `analytics` | summary |
| `GET /optimization/optimize-trim/{vessel_id}` | 有差异 | `analytics` | summary |
| `GET /optimization/trim-data/{vessel_id}` | 有差异 | `analytics` | summary |
| `GET /optimization/{vessel_id}/average` | 一致 | `analytics` | 已兼容旧路径；规范路径为 `GET /optimization/vessel/{vessel_id}/average` |
| `GET /optimization/{vessel_id}/consumption-total` | 一致 | `analytics` | 已兼容旧路径；规范路径为 `GET /optimization/vessel/{vessel_id}/consumption-total` |
| `GET /optimization/{vessel_id}/values` | 一致 | `analytics` | 已兼容旧路径；规范路径为 `GET /optimization/vessel/{vessel_id}/values` |
| `GET /reminder/{vessel_id}/engine` | 仅老服务 | - | 待迁移/已废弃 |
| `GET /reminder/{vessel_id}/graph` | 仅老服务 | - | 待迁移/已废弃 |
| `GET /reminder/{vessel_id}/monthly-power-ranges-sfoc` | 仅老服务 | - | 待迁移/已废弃 |
| `GET /reminder/{vessel_id}/values` | 仅老服务 | - | 待迁移/已废弃 |
| `GET /statistic/attribute-frequencies` | 有差异 | `analytics` | parameters, summary |
| `GET /statistic/attribute-relation` | 有差异 | `analytics` | parameters, summary |
| `GET /statistic/attribute-values` | 有差异 | `analytics` | parameters, summary |
| `GET /statistic/consumption/nmile` | 有差异 | `analytics` | summary |
| `GET /statistic/consumption/total` | 有差异 | `analytics` | summary |
| `GET /statistic/vessel/{vessel_id}/cii` | 有差异 | `analytics` | summary |
| `GET /statistic/vessel/{vessel_id}/completeness` | 一致 | `analytics` |  |
| `GET /statistic/vessel/{vessel_id}/date-range` | 有差异 | `analytics` | summary |
| `GET /upload/vessel/{vessel_id}/history` | 有差异 | `data` | summary |
| `GET /user` | 一致 | `identity` |  |
| `GET /user/{user_id}` | 一致 | `identity` |  |
| `GET /vessel` | 一致 | `vessel` |  |
| `GET /vessel/{vessel_id}` | 有差异 | `vessel` | summary |
| `POST /calculate/cii` | 仅老服务 | - | 待迁移/已废弃 |
| `POST /company` | 一致 | `identity` |  |
| `POST /route-optimization/get-shortest-route` | 仅老服务 | - | 待迁移/已废弃 |
| `POST /route-optimization/historical-routes` | 仅老服务 | - | 待迁移/已废弃 |
| `POST /route-optimization/plan-all` | 仅老服务 | - | 待迁移/已废弃 |
| `POST /route-optimization/ship-route-planner` | 仅老服务 | - | 待迁移/已废弃 |
| `POST /upload/vessel/{vessel_id}/standard` | 有差异 | `data` | parameters, responses, summary |
| `POST /user/login` | 一致 | `identity` |  |
| `POST /user/register` | 一致 | `identity` |  |
| `POST /vessel` | 一致 | `vessel` |  |
| `PUT /company/{company_id}` | 一致 | `identity` |  |
| `PUT /user/{user_id}` | 一致 | `identity` |  |
| `PUT /vessel/{vessel_id}` | 一致 | `vessel` |  |

## 签名差异详情（共享 path+method）

### `GET /`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `Root`
- 新 summary: `Health Check`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200']`
- 新 responses: `['200']`

### `GET /company`
- 新服务归属: `identity`
- 差异项: responses
- 老 summary: `获取所有公司`
- 新 summary: `获取所有公司`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/attribute_mapping`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `属性组合`
- 新 summary: `属性组合`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/attributes`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `属性`
- 新 summary: `属性`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/fuel_type`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `获取燃料类型`
- 新 summary: `获取燃料类型`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/fuel_type_category`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `燃料类型分类`
- 新 summary: `燃料类型分类`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/ship_type`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `获取船舶类型`
- 新 summary: `获取船舶类型`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /meta/time_zone`
- 新服务归属: `meta`
- 差异项: responses
- 老 summary: `获取时区`
- 新 summary: `获取时区`
- 老 parameters: `[]`
- 新 parameters: `[]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200']`

### `GET /optimization/optimize-speed/{vessel_id}`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `Get speed optimization suggestions`
- 新 summary: `获取航速优化建议（需ML模型）`
- 老 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /optimization/optimize-trim/{vessel_id}`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `Get trim optimization suggestions`
- 新 summary: `获取吃水差优化建议（需ML模型）`
- 老 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /optimization/trim-data/{vessel_id}`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `Get vessel trim data`
- 新 summary: `获取船舶吃水差数据`
- 老 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'start_date', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/attribute-frequencies`
- 新服务归属: `analytics`
- 差异项: parameters, summary
- 老 summary: `获取属性频次分布`
- 新 summary: `获取直方图属性值频次`
- 老 parameters: `[('query', 'attribute_name', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', True), ('query', 'min_slip_ratio', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 新 parameters: `[('query', 'attribute_name', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', False), ('query', 'min_slip_ratio', False), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/attribute-relation`
- 新服务归属: `analytics`
- 差异项: parameters, summary
- 老 summary: `获取属性关系`
- 新 summary: `获取属性关系图数据（双属性散点图）`
- 老 parameters: `[('query', 'attribute_name1', True), ('query', 'attribute_name2', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', True), ('query', 'min_slip_ratio', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 新 parameters: `[('query', 'attribute_name1', True), ('query', 'attribute_name2', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', False), ('query', 'min_slip_ratio', False), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/attribute-values`
- 新服务归属: `analytics`
- 差异项: parameters, summary
- 老 summary: `获取属性值随日期变化`
- 新 summary: `获取散点图属性值（日期维度）`
- 老 parameters: `[('query', 'attribute_name', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', True), ('query', 'min_slip_ratio', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 新 parameters: `[('query', 'attribute_name', True), ('query', 'end_date', True), ('query', 'max_slip_ratio', False), ('query', 'min_slip_ratio', False), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/consumption/nmile`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `获取每海里油耗统计`
- 新 summary: `获取每海里燃油消耗统计`
- 老 parameters: `[('query', 'end_date', True), ('query', 'fuel_type', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 新 parameters: `[('query', 'end_date', True), ('query', 'fuel_type', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/consumption/total`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `获取总油耗统计`
- 新 summary: `获取总燃油消耗统计`
- 老 parameters: `[('query', 'end_date', True), ('query', 'fuel_type', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 新 parameters: `[('query', 'end_date', True), ('query', 'fuel_type', True), ('query', 'start_date', True), ('query', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/vessel/{vessel_id}/cii`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `获取船舶CII数据`
- 新 summary: `获取船舶CII数据（含评级）`
- 老 parameters: `[('path', 'vessel_id', True)]`
- 新 parameters: `[('path', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /statistic/vessel/{vessel_id}/date-range`
- 新服务归属: `analytics`
- 差异项: summary
- 老 summary: `获取时间范围内船舶数据`
- 新 summary: `获取时间范围内船舶标准数据`
- 老 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'sample_interval', False), ('query', 'start_date', True)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'end_date', True), ('query', 'sample_interval', False), ('query', 'start_date', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /upload/vessel/{vessel_id}/history`
- 新服务归属: `data`
- 差异项: summary
- 老 summary: `获取船舶数据上传历史`
- 新 summary: `获取船舶上传历史`
- 老 parameters: `[('path', 'vessel_id', True), ('query', 'limit', False), ('query', 'offset', False)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'limit', False), ('query', 'offset', False)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `GET /vessel/{vessel_id}`
- 新服务归属: `vessel`
- 差异项: summary
- 老 summary: `获取单个船舶`
- 新 summary: `获取船舶详情`
- 老 parameters: `[('path', 'vessel_id', True)]`
- 新 parameters: `[('path', 'vessel_id', True)]`
- 老 requestBody: `required=False, content=[]`
- 新 requestBody: `required=False, content=[]`
- 老 responses: `['200', '422']`
- 新 responses: `['200', '422']`

### `POST /upload/vessel/{vessel_id}/standard`
- 新服务归属: `data`
- 差异项: parameters, responses, summary
- 老 summary: `上传标准数据`
- 新 summary: `上传标准 CSV 数据`
- 老 parameters: `[('path', 'vessel_id', True)]`
- 新 parameters: `[('path', 'vessel_id', True), ('query', 'pitch', False), ('query', 'vessel_capacity', False)]`
- 老 requestBody: `required=True, content=['multipart/form-data']`
- 新 requestBody: `required=True, content=['multipart/form-data']`
- 老 responses: `['200', '422']`
- 新 responses: `['202', '422']`

## 旧路径仍待处理（含未迁移与已迁移但路径变化）

- `GET /metrics`：当前 services 未提供对应聚合指标接口。
- `GET /reminder/{vessel_id}/engine`：当前未迁移。
- `GET /reminder/{vessel_id}/graph`：当前未迁移。
- `GET /reminder/{vessel_id}/monthly-power-ranges-sfoc`：当前未迁移。
- `GET /reminder/{vessel_id}/values`：当前未迁移。
- `POST /calculate/cii`：当前未迁移。
- `POST /route-optimization/get-shortest-route`：当前未迁移。
- `POST /route-optimization/historical-routes`：当前未迁移。
- `POST /route-optimization/plan-all`：当前未迁移。
- `POST /route-optimization/ship-route-planner`：当前未迁移。

## 仅重构后存在（新增）

- `GET /daily/vessel/{vessel_id}` (data)
- `GET /optimization/vessel/{vessel_id}/average` (analytics)
- `GET /optimization/vessel/{vessel_id}/consumption-total` (analytics)
- `GET /optimization/vessel/{vessel_id}/values` (analytics)
- `GET /upload/{upload_id}/status` (data)
