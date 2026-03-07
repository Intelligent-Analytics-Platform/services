# Kind 集群部署指南

本文档描述如何在本地使用 Kind 创建 Kubernetes 集群，并通过 Ingress 部署服务。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kind Cluster (iap)                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    ingress-nginx                             │ │
│  │                      :80 :443                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    namespace: services                       │ │
│  │                                                              │ │
│  │  ┌─────────┐ ┌───────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐ │ │
│  │  │  meta   │ │ identity  │ │ vessel  │ │  data   │ │analyt│ │ │
│  │  │  :9000  │ │   :9001   │ │  :9002  │ │  :9003  │ │:9004 │ │ │
│  │  └─────────┘ └───────────┘ └─────────┘ └─────────┘ └──────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 端口映射

| 宿主机端口 | 集群端口 | 用途 |
|-----------|---------|------|
| 9000 | 30000 | meta 服务 |
| 9001 | 30001 | identity 服务 |
| 9002 | 30002 | vessel 服务 |
| 9003 | 30003 | 预留 |
| 9004 | 30004 | data 服务 |
| 9005 | 30005 | analytics 服务 |
| 9080 | 80 | Ingress HTTP |
| 9443 | 443 | Ingress HTTPS |
| 9100 | 30100 | Loki |

## 快速开始

### 前置条件

- Docker Desktop
- kubectl
- kind (`brew install kind`)

### 一键部署

```bash
# 1. 创建集群（首次需要拉取镜像，约 2 分钟）
make kind-create

# 2. 构建并加载镜像
make build-meta
kind load docker-image meta-service:latest --name iap

# 3. 安装 Ingress 控制器
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# 4. 部署服务
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/apps/meta.yml
kubectl apply -f k8s/ingress.yml

# 5. 验证
curl http://localhost:9000/
curl http://localhost:9080/meta/fuel_type
```

### 访问服务

**通过 NodePort（直连服务）：**
```bash
curl http://localhost:9000/           # meta
curl http://localhost:9001/           # identity
curl http://localhost:9002/           # vessel
curl http://localhost:9004/           # data
curl http://localhost:9005/           # analytics
```

**通过 Ingress（统一入口）：**
```bash
curl http://localhost:9080/meta/fuel_type
curl http://localhost:9080/identity/company
curl http://localhost:9080/vessel/
```

## 常用命令

```bash
# 查看集群状态
kubectl cluster-info --context kind-iap

# 查看所有服务
kubectl get all -n services

# 查看日志
kubectl logs -n services deployment/meta

# 进入 Pod
kubectl exec -it -n services deployment/meta -- /bin/bash

# 删除集群
kind delete cluster --name iap
```

## 部署所有服务

```bash
# 构建所有镜像
make build-meta build-identity build-vessel build-data build-analytics

# 加载镜像到 Kind
kind load docker-image meta-service:latest --name iap
kind load docker-image identity-service:latest --name iap
kind load docker-image vessel-service:latest --name iap
kind load docker-image data-service:latest --name iap
kind load docker-image analytics-service:latest --name iap

# 部署所有服务
kubectl apply -f k8s/apps/
```

## 故障排查

### 端口冲突

如果创建集群时端口冲突，修改 `k8s/kind-config.yml` 中的 `hostPort`。

### Pod 启动失败

```bash
kubectl describe pod -n services <pod-name>
kubectl logs -n services <pod-name>
```

### Ingress 不生效

```bash
kubectl get ingress -n services
kubectl describe ingress -n services
```

## 文件说明

```
k8s/
├── kind-config.yml     # Kind 集群配置
├── namespace.yml       # 命名空间定义
├── ingress.yml         # Ingress 路由规则
├── apps/
│   ├── meta.yml        # meta 服务部署
│   ├── identity.yml    # identity 服务部署
│   ├── vessel.yml      # vessel 服务部署
│   ├── data.yml        # data 服务部署
│   └── analytics.yml   # analytics 服务部署
└── observability/
    ├── loki.yml
    ├── promtail.yml
    └── grafana.yml
```