# Kubernetes 部署指南

本文档描述如何使用 [Kind](https://kind.sigs.k8s.io/) 在本地搭建完整的船舶能效分析平台 Kubernetes 集群。

---

## 前置要求

| 工具 | 最低版本 | 说明 |
|------|----------|------|
| Docker | 20.x+ | 镜像构建与 Kind 依赖 |
| Kind | 0.20+ | 本地 Kubernetes 集群 |
| kubectl | 1.27+ | 集群管理 |
| make | — | Makefile 任务编排 |

```bash
# macOS 安装
brew install kind kubectl
```

---

## 集群架构

```
                           本机（localhost）
┌──────────────────────────────────────────────────────────────────┐
│  :8000  :8001  :8002  :8003  :8004  :3000  :3100                 │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────────┘
     │      │      │      │      │      │      │   Kind 端口映射
┌────▼──────▼──────▼──────▼──────▼──────▼──────▼───────────────────┐
│                      Kind 集群（iap）                              │
│                                                                   │
│  ┌──────────────────── services 命名空间 ─────────────────────┐   │
│  │                                                            │   │
│  │  meta       identity     vessel     data      analytics    │   │
│  │  :8000      :8001        :8002      :8003     :8004        │   │
│  │   │            │           │          │          │         │   │
│  │   │            │           │          │          │ (只读)  │   │
│  │  SQLite      SQLite       SQLite  SQLite ──► DuckDB ◄──────┘   │
│  │  (meta.db) (identity.db)(vessel.db)(data.db)(data.duckdb)  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────── observability 命名空间 ──────────────────────┐     │
│  │  Promtail（DaemonSet）→ Loki :3100 → Grafana :3000       │     │
│  └──────────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────┘
```

### 端口映射总表

| 服务 | 容器端口 | NodePort | 本机端口 | URL |
|------|----------|----------|----------|-----|
| meta | 8000 | 30000 | 8000 | http://localhost:8000/docs |
| identity | 8001 | 30001 | 8001 | http://localhost:8001/docs |
| vessel | 8002 | 30002 | 8002 | http://localhost:8002/docs |
| data | 8003 | 30004 | 8003 | http://localhost:8003/docs |
| analytics | 8004 | 30005 | 8004 | http://localhost:8004/docs |
| Grafana | 3000 | 30003 | 3000 | http://localhost:3000 |
| Loki | 3100 | 30100 | 3100 | — |

### 服务内部 DNS

集群内各服务通过 Kubernetes DNS 互相调用：

```
http://{service}.services.svc.cluster.local:{port}
```

| 调用方 | 被调用方 | 内部地址 |
|--------|----------|----------|
| analytics | vessel | `http://vessel.services.svc.cluster.local:8002` |
| analytics | meta | `http://meta.services.svc.cluster.local:8000` |
| identity | meta | `http://meta.services.svc.cluster.local:8000` |

---

## 存储卷

| PVC 名称 | 大小 | 访问模式 | 用途 |
|----------|------|----------|------|
| `meta-db` | 1 Gi | ReadWriteOnce | meta SQLite |
| `identity-db` | 1 Gi | ReadWriteOnce | identity SQLite |
| `vessel-db` | 1 Gi | ReadWriteOnce | vessel SQLite |
| `data-storage` | 20 Gi | ReadWriteOnce | data SQLite + **DuckDB**（data.duckdb） |
| `data-uploads` | 10 Gi | ReadWriteOnce | 上传 CSV 临时存储 |
| `analytics-models` | 5 Gi | ReadWriteOnce | XGBoost pkl 模型文件 |
| `loki-data` | 5 Gi | ReadWriteOnce | Loki 日志数据 |

> **DuckDB 共享**：`data-storage` PVC 由 data 服务以读写方式挂载，analytics 服务以只读方式挂载同一个 PVC（`readOnly: true`）。Kind 为单节点集群，两个 Pod 必然调度在同一节点，ReadWriteOnce 约束天然满足。
>
> **生产环境**：多节点集群需将 `data-storage` 改为 ReadWriteMany（NFS / 云厂商 CSI 插件），或将 DuckDB 文件迁移到对象存储（S3）。

---

## 快速部署（首次）

### 第一步：创建 Kind 集群

```bash
make kind-create
```

> 此命令使用 `k8s/kind-config.yml` 创建名为 `iap` 的单节点集群，并配置所有 NodePort 端口映射。
>
> ⚠️ **如果集群已存在且端口映射不包含 8003/8004**，需先删除重建：
> ```bash
> make kind-delete
> make kind-create
> ```

验证集群：

```bash
kubectl cluster-info --context kind-iap
kubectl get nodes
```

### 第二步：拉取可观测性基础镜像

首次部署需提前拉取 Grafana / Loki / Promtail 镜像（国内网络建议配置镜像加速）：

```bash
make kind-pull-obs
```

### 第三步：构建应用镜像并加载到集群

```bash
make kind-load
```

此命令依次执行：
1. `docker build` 构建所有 5 个服务镜像
2. `kind load docker-image` 将镜像导入 Kind 集群（避免从 Registry 拉取）
3. 加载 Loki / Promtail / Grafana 镜像

> 每次修改代码后重新部署，重复此步骤，然后执行 `kubectl rollout restart deployment/<name> -n services`。

### 第四步：部署应用

```bash
make kind-apply
```

执行顺序：
1. 创建命名空间（`services` / `observability`）
2. 部署所有应用服务（`k8s/apps/`）
3. 部署可观测性栈（`k8s/observability/`）

### 第五步：验证部署

```bash
# 等待所有 Pod 就绪（约 30-60 秒）
kubectl get pods -n services -w
kubectl get pods -n observability -w

# 检查所有服务
kubectl get svc -n services
kubectl get svc -n observability
```

所有 Pod 的 `READY` 列应显示 `1/1`，`STATUS` 为 `Running`。

### 第六步：冒烟测试

```bash
# 健康检查
curl http://localhost:8000/   # meta
curl http://localhost:8001/   # identity
curl http://localhost:8002/   # vessel
curl http://localhost:8003/   # data
curl http://localhost:8004/   # analytics

# OpenAPI 文档
open http://localhost:8003/docs   # data 服务
open http://localhost:8004/docs   # analytics 服务

# Grafana 日志看板
open http://localhost:3000
```

---

## 日常操作

### 更新单个服务

```bash
# 重新构建并加载镜像（以 analytics 为例）
docker build -f apps/analytics/Dockerfile -t analytics-service .
kind load docker-image analytics-service:latest --name iap

# 触发滚动重启
kubectl rollout restart deployment/analytics -n services

# 查看滚动状态
kubectl rollout status deployment/analytics -n services
```

### 查看日志

```bash
# 实时日志
kubectl logs -f deployment/data -n services
kubectl logs -f deployment/analytics -n services

# 历史日志（含已重启 Pod）
kubectl logs deployment/analytics -n services --previous
```

### 查看配置和环境变量

```bash
kubectl describe deployment/analytics -n services
kubectl exec -it deployment/analytics -n services -- env | grep -E "DUCK|VESSEL|META|MODELS"
```

### 手动上传 XGBoost 模型（analytics 服务）

```bash
# 获取 analytics pod 名称
POD=$(kubectl get pod -n services -l app=analytics -o jsonpath='{.items[0].metadata.name}')

# 复制模型文件到 /models 目录
kubectl cp ./models/1_XGBoost_v2_all.pkl services/$POD:/models/
kubectl cp ./models/1_XGBoost_v2_less.pkl services/$POD:/models/
kubectl cp ./models/1_trim_v1.pkl         services/$POD:/models/

# 验证
kubectl exec -n services $POD -- ls /models/
```

### 端口转发（调试用）

```bash
# 直接转发单个服务（不经 NodePort）
kubectl port-forward svc/analytics 8004:8004 -n services
kubectl port-forward svc/loki 3100:3100 -n observability
```

---

## identity 服务 JWT Secret

部署前替换默认的 JWT 密钥（尤其是生产环境）：

```bash
# 方式一：直接编辑 YAML 再 apply
vim k8s/apps/identity.yml   # 修改 JWT_SECRET_KEY 值

# 方式二：kubectl patch（不修改文件）
kubectl create secret generic identity-secret \
  --from-literal=JWT_SECRET_KEY="your-strong-secret-key" \
  --namespace=services \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/identity -n services
```

---

## 清理与重建

```bash
# 删除所有应用（保留集群和 PVC）
make kind-delete-apps

# 重新部署应用
make kind-apply

# 完全删除集群（含所有数据）
make kind-delete

# 重建整个环境
make kind-create kind-load kind-apply
```

---

## 可观测性

### Grafana 访问

打开 http://localhost:3000（匿名管理员，无需登录）。

**浏览日志步骤：**
1. 左侧菜单 → **Explore**
2. 数据源选择 **Loki**
3. 按 Label 过滤：`service=data`、`service=analytics`、`level=ERROR` 等
4. 运行查询查看结构化 JSON 日志

### 常用 Loki 查询

```logql
# analytics 服务所有日志
{service="analytics"}

# 所有 ERROR 级别日志
{level="error"}

# data 服务上传相关日志
{service="data"} |= "upload"

# 过去1小时内所有错误
{namespace="services"} |= "ERROR" | json | line_format "{{.message}}"
```

---

## 常见问题

### Pod 处于 Pending 状态

```bash
kubectl describe pod <pod-name> -n services
```

常见原因：
- PVC 未绑定：Kind 使用本地存储，通常自动绑定；检查 `kubectl get pvc -n services`
- 镜像未加载：确认 `kind load docker-image` 已执行

### analytics Pod CrashLoopBackOff

检查 DuckDB 路径：

```bash
kubectl exec -n services deployment/data -- ls -la /data/
# 应存在 data.duckdb 文件（由 data 服务首次启动时创建）
```

若 `data.duckdb` 不存在，需先触发 data 服务初始化（发送任意 HTTP 请求即可）：

```bash
curl http://localhost:8003/
```

### analytics 无法访问 DuckDB（只读挂载）

analytics 和 data 两个 Pod 必须调度到同一节点（`data-storage` PVC 为 ReadWriteOnce）。
analytics 的 Deployment 已配置 `podAffinity` 约束，在单节点 Kind 集群中自动满足。

如果出现 `Multi-Attach error for volume`，说明 analytics Pod 被调度到不同节点：

```bash
# 查看两个 Pod 所在节点
kubectl get pod -n services -o wide | grep -E "data|analytics"
```

### 端口映射不生效（8003 / 8004 无法访问）

Kind 的端口映射在**集群创建时**固定。若集群是在添加 data/analytics 端口之前创建的，需重建：

```bash
make kind-delete
make kind-create
# 然后重新加载镜像和部署
make kind-load kind-apply
```

---

## 目录结构

```
services/
├── k8s/
│   ├── kind-config.yml          # Kind 集群配置（端口映射）
│   ├── namespace.yml            # services + observability 命名空间
│   ├── apps/
│   │   ├── meta.yml             # meta 服务（:8000, NodePort 30000）
│   │   ├── identity.yml         # identity 服务（:8001, NodePort 30001）
│   │   ├── vessel.yml           # vessel 服务（:8002, NodePort 30002）
│   │   ├── data.yml             # data 服务（:8003, NodePort 30004）
│   │   └── analytics.yml        # analytics 服务（:8004, NodePort 30005）
│   └── observability/
│       ├── loki.yml             # Loki 日志聚合（:3100, NodePort 30100）
│       ├── grafana.yml          # Grafana 看板（:3000, NodePort 30003）
│       └── promtail.yml         # Promtail DaemonSet（日志采集）
├── Makefile                     # 所有运维命令入口
└── DEPLOYMENT.md                # 本文档
```
