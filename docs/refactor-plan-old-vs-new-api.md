# API 重构落地方案（含接口与结果对比）

- 生成时间: 2026-03-08 20:25:37
- 输入依据:
  - `docs/api-compare-old-vs-refactor.json`（接口契约对比）
  - `docs/api-result-compare-old-vs-refactor.json`（运行结果对比）

## 1. 现状结论

- 接口维度: old=50 new=41 shared=36
- 差异分布: only_old=14 only_new=5 changed=21
- 结果兼容: 高=7 中=5 低=0（样本接口 12 个）

## 2. 重构目标

- 对前端/调用方保持平滑迁移：旧接口可映射、新接口可消费。
- 对关键业务（identity/vessel/meta/data）保证响应结构与语义稳定。
- 对遗留能力（reminder、route-optimization、calculate/cii）给出明确去留（迁移或下线）。

## 3. 分阶段实施计划

### 阶段A：契约收敛（1-2天）
- A1. 锁定 14 个 `only_old` 接口的处理策略：迁移/适配/废弃。
- A2. 对 21 个 `changed` 接口建立差异白名单（参数、状态码、summary、responses）。
- A3. 对 `POST /upload/vessel/{vessel_id}/standard` 明确 200->202 变更公告与客户端改造点。

### 阶段B：兼容层实现（2-4天）
- B1. 在网关或 BFF 增加旧路径到新路径映射（重点：`/optimization/{vessel_id}/*` -> `/optimization/vessel/{vessel_id}/*`）。
- B2. 对必须保留的旧返回结构做响应适配（字段重命名/包装一致化）。
- B3. 为 `only_old` 中确认保留接口提供临时代理实现，避免前端一次性改完。

### 阶段C：结果一致性治理（2-3天）
- C1. 将当前 12 个运行时对比用例固化为回归测试。
- C2. 扩充到所有共享 GET 接口，并补充至少 5 个 POST/PUT 场景。
- C3. 对低兼容样本逐项修复：优先状态码与 data 结构，再处理 message/summary。

### 阶段D：下线与收口（1天）
- D1. 对废弃接口发布 deprecation 清单与下线时间。
- D2. 在文档中标注替代接口与迁移示例。
- D3. 通过灰度验证后关闭兼容层。

## 4. 详细任务清单（按优先级）

### P0（必须先做）
- `POST /upload/vessel/{vessel_id}/standard`：统一状态码策略（建议保持 202）并更新调用方轮询逻辑。
- `/optimization/{vessel_id}/values|average|consumption-total`：补旧路径兼容映射。
- `GET /company` 与 meta 系列接口：确认是否保留 422 文档响应，避免 SDK 生成差异。

### P1（本周完成）
- reminder 4 个接口：确认是否迁移到 analytics 或彻底下线。
- route-optimization 4 个接口：拆分到新服务或提供独立服务说明。
- `POST /calculate/cii`：确认由 analytics 统计接口替代还是保留独立入口。

### P2（质量提升）
- summary/description 文案统一（中文规范化）。
- OpenAPI responses 统一补齐（特别是 422/400/404）。
- 生成 SDK 前做契约快照比对，防止回归。

## 5. 验收标准

- 标准1：`only_old` 接口全部有明确归属（迁移/代理/下线）。
- 标准2：共享接口运行时对比中，低兼容为 0。
- 标准3：关键链路（company/user/vessel/upload）前后端联调通过。
- 标准4：对外文档含迁移指引、状态码变化、替代路径示例。

## 6. 风险与回滚

- 风险1：调用方硬编码旧路径，切换后 404。
  - 缓解：保留兼容路由 1 个发布周期。
- 风险2：异步接口状态码变化（200->202）导致前端误判失败。
  - 缓解：前端增加任务状态查询与超时提示。
- 风险3：历史能力（reminder/route）未及时迁移。
  - 缓解：先代理转发，再逐步拆分。
- 回滚策略：网关层保留旧路由开关，可一键切回旧服务地址。

## 7. 接口去留建议（基于当前对比）

### 建议优先保留并兼容
- `GET /company/{company_id}/vessels`
- `GET /optimization/{vessel_id}/average`
- `GET /optimization/{vessel_id}/consumption-total`
- `GET /optimization/{vessel_id}/values`

### 建议评审后下线
- `GET /metrics`
- `GET /reminder/{vessel_id}/engine`
- `GET /reminder/{vessel_id}/graph`
- `GET /reminder/{vessel_id}/monthly-power-ranges-sfoc`
- `GET /reminder/{vessel_id}/values`
- `POST /calculate/cii`
- `POST /route-optimization/get-shortest-route`
- `POST /route-optimization/historical-routes`
- `POST /route-optimization/plan-all`
- `POST /route-optimization/ship-route-planner`

## 8. 下一步执行顺序（可直接开工）

1. 先在网关/BFF补3条 optimization 旧路径映射。
2. 补齐 upload 标准接口的调用链改造（202 + status查询）。
3. 输出 only_old 14条接口的最终决策表（负责人+截止时间）。
4. 把结果对比脚本接入 CI，每次发布前自动跑。