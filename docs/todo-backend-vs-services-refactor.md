# backend -> services 重构 Todo

更新时间：2026-03-14

## P0 文档与契约收敛

- [ ] 维护一份旧接口去向清单，覆盖 `兼容保留`、`路径迁移`、`独立服务迁移`、`确认下线` 四类。
- [ ] 修正 docs 中已过期的接口结论，特别是 `GET /company/{company_id}/vessels` 和 optimization 三个路径重构接口。
- [ ] 补一份面对前端的迁移说明，明确 `POST /upload/vessel/{vessel_id}/standard` 已改为 `202 + status 查询`。
- [ ] 确认 `GET /vessel` 和 `GET /vessel/{id}` 是否需要通过 BFF 恢复旧聚合字段。

## P1 兼容层

- [x] 为 `/optimization/{vessel_id}/values` 提供兼容映射到 `/optimization/vessel/{vessel_id}/values`。
- [x] 为 `/optimization/{vessel_id}/average` 提供兼容映射到 `/optimization/vessel/{vessel_id}/average`。
- [x] 为 `/optimization/{vessel_id}/consumption-total` 提供兼容映射到 `/optimization/vessel/{vessel_id}/consumption-total`。
- [ ] 统一各服务 OpenAPI 中常见错误响应的文档声明，至少覆盖 `400`、`404`、`422`。

## P2 历史能力决策

- [ ] 确认 `reminder` 四个接口是否迁入 `analytics`。
- [ ] 确认 `route_optimization` 是否拆为独立服务，而不是继续并入现有 analytics。
- [ ] 确认 `POST /calculate/cii` 的保留价值；需要保留则补纯计算端点，不需要则发布下线说明。
- [ ] 确认 `GET /metrics` 是否需要统一外部访问入口或只保留内部观测用途。

## P3 验证与回归

- [ ] 把接口契约对比脚本纳入发布前检查。
- [ ] 把运行结果对比扩展到 `company`、`user`、`vessel`、`upload`、`optimization` 关键链路。
- [ ] 为已声明“兼容保留”的接口补测试，避免文档与代码再次偏离。
- [ ] 在最终决策后更新对外迁移文档，删除 `待迁移/已废弃` 这类未决措辞。