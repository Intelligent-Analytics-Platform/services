# 船舶能效数据分析 — 微服务架构

基于 uv workspace 的 monorepo，包含三个独立微服务 + 可观测性组件。

---

## 项目结构

```
services/
├── CLAUDE.md                   # AI 协作开发原则
├── Makefile                    # 常用命令入口
├── pyproject.toml              # uv workspace 根配置
├── libs/
│   └── common/                 # 公共库（跨服务复用）
│       └── common/
│           ├── auth.py         # JWT + 密码哈希
│           ├── database.py     # 引擎/会话工厂
│           ├── exceptions.py   # 异常体系 + FastAPI handlers
│           ├── logging.py      # 结构化 JSON 日志
│           ├── models.py       # SQLAlchemy Base + Mixin
│           ├── repository.py   # BaseRepository 通用 CRUD
│           └── schemas.py      # ResponseModel 统一响应
└── apps/
    ├── meta/                   # 元数据服务（port 8000）
    ├── identity/               # 身份认证服务（port 8001）
    └── vessel/                 # 船舶管理服务（port 8002）
```

---

## 服务一览

| 服务 | 端口 | 职责 | 文档 |
|------|------|------|------|
| meta | 8000 | 燃料/船型/时区等只读参考数据 | [apps/meta/README.md](apps/meta/README.md) |
| identity | 8001 | 公司管理 + 用户注册/登录/JWT | [apps/identity/README.md](apps/identity/README.md) |
| vessel | 8002 | 船舶信息 + 设备 + 功率曲线 | apps/vessel/README.md |

---

## 本地开发启动

> **日常开发推荐这种方式。** 直接用 uvicorn 进程，不依赖 Docker/k8s，热重载快。

```bash
# 安装依赖（首次或依赖变更后）
uv sync --all-packages

# 各服务分终端启动
make run-meta       # http://localhost:8000/docs
make run-identity   # http://localhost:8001/docs
make run-vessel     # http://localhost:8002/docs
```

首次启动会自动建表并执行 `seed.sql` 写入初始数据：
- meta：16 种燃料、13 种船型、25 个时区
- identity：测试公司 + 管理员账号（`admin` / `test1234`）

### 运行测试

```bash
make test           # 运行所有服务测试
make test-meta      # 单独运行 meta 测试
make test-identity  # 单独运行 identity 测试
make test-vessel    # 单独运行 vessel 测试
```

---

## k8s 部署（Kind 本地集群）

> **用于集成测试和可观测性验证。** 日常开发不需要。

### 首次搭建

```bash
make kind-pull-obs   # 预拉取 grafana/loki/promtail 镜像（防止 Kind 内拉取超时）
make kind-create     # 创建 Kind 集群（名称：iap）
make kind-load       # 构建三个服务镜像并加载到 Kind
make kind-apply      # 部署所有 k8s 资源
```

端口映射：

| 服务 | 宿主机端口 |
|------|-----------|
| meta | 8000 |
| identity | 8001 |
| vessel | 8002 |
| Grafana | 3000 |
| Loki | 3100 |

### ⚠️ Docker Desktop 重启后端口失效问题

**现象**：Docker Desktop 重启后，kubectl 报 `connection refused`，部分服务端口也无法访问。

**原因**：Kind 把端口绑定写在 Docker 容器的运行参数里。Docker Desktop 重启时容器也重启，但端口绑定会**随机丢失**——通常只有最后一个端口映射能保留（本项目是 Grafana 的 3000）。kubeconfig 里记录的 API server 端口也会失效。

**解决方案**：删除集群重建。

```bash
make kind-delete         # 删除旧集群
make kind-create         # 重建集群（端口重新绑定）
make kind-load           # 重新加载镜像（构建缓存不会重跑）
make kind-apply          # 重新部署
```

> 重建集群约需 1~2 分钟，镜像已缓存在本地所以 load 很快。

**不重建的临时方案**（只想用 kubectl）：

```bash
# 获取 Kind 节点容器 IP
NODE_IP=$(docker inspect iap-control-plane \
  --format '{{.NetworkSettings.Networks.kind.IPAddress}}')

# 临时更新 kubeconfig server 地址
kubectl config set-cluster kind-iap --server=https://$NODE_IP:6443

# 验证
kubectl get pods -n services
```

注意：此方案只修复 kubectl 连接，NodePort 端口（8000/8001/8002/3000/3100）在重建前仍无法从宿主机访问。

---

## 可观测性

Loki + Grafana + Promtail 采集所有服务的结构化 JSON 日志。

```bash
# 单独启动可观测性组件（不影响应用服务）
make up-obs
make down-obs
```

Grafana 访问：`http://localhost:3000`（默认无需登录）

在 Explore → Loki 中查询：
```
{service="meta"}
{service="identity"}
{service="vessel"}
```

---

## common 库说明

| 模块 | 用途 |
|------|------|
| `auth.py` | `get_password_hash` / `verify_password` / `create_access_token` / `decode_token` |
| `database.py` | `create_engine_from_url()` / `create_session_factory()` |
| `repository.py` | `BaseRepository[T]`：get_by_id / get_or_raise / list_all / create / update / delete |
| `schemas.py` | `ResponseModel[Data]` 统一 API 响应包装 |
| `models.py` | `Base` / `IntIDMixin`（自增主键）/ `TimestampMixin`（created_at/updated_at） |
| `exceptions.py` | `EntityNotFoundError` / `AuthenticationError` + `setup_exception_handlers()` |
| `logging.py` | `setup_logging(service, level)` 输出结构化 JSON 到 stdout |
