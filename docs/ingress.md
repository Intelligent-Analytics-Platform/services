# Ingress 访问指南

## 请求链路

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              外部请求                                        │
│                         http://localhost:9080                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Kind Cluster                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Node (iap-control-plane)                      │    │
│  │                                                                      │    │
│  │   ┌──────────────────────────────────────────────────────────┐     │    │
│  │   │                    Port Mappings                          │     │    │
│  │   │   9080 → 80 (HTTP)                                        │     │    │
│  │   │   9443 → 443 (HTTPS)                                      │     │    │
│  │   │   9000/9001/9002/9004/9005 → 30000/1/2/4/5 (应用)         │     │    │
│  │   │   3000 → 30003 (Grafana)                                  │     │    │
│  │   └──────────────────────────────────────────────────────────┘     │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌──────────────────────────────────────────────────────────┐     │    │
│  │   │              Ingress-Nginx Controller                     │     │    │
│  │   │                    (namespace: ingress-nginx)             │     │    │
│  │   │                                                           │     │    │
│  │   │   规则:                                                   │     │    │
│  │   │   /meta/*     → meta:9000                                │     │    │
│  │   │   /company/*  → identity:9001                            │     │    │
│  │   │   /user/*     → identity:9001                            │     │    │
│  │   │   /vessel/*   → vessel:9002                              │     │    │
│  │   │   /upload/*   → data:9003                                │     │    │
│  │   │   /daily/*    → data:9003                                │     │    │
│  │   │   /analytics/*→ analytics:9004                           │     │    │
│  │   └──────────────────────────────────────────────────────────┘     │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌──────────────────────────────────────────────────────────┐     │    │
│  │   │                  Services (namespace: services)           │     │    │
│  │   │                                                           │     │    │
│  │   │   meta:9000      identity:9001    vessel:9002             │     │    │
│  │   │   data:9003      analytics:9004                          │     │    │
│  │   └──────────────────────────────────────────────────────────┘     │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌──────────────────────────────────────────────────────────┐     │    │
│  │   │                      Pods                                 │     │    │
│  │   │                                                           │     │    │
│  │   │   meta-xxx       identity-xxx     vessel-xxx              │     │    │
│  │   │   data-xxx       analytics-xxx                            │     │    │
│  │   │                                                           │     │    │
│  │   │   ┌─────────────────────────────────────────────────┐    │     │    │
│  │   │   │  Container (FastAPI + Uvicorn)                   │    │     │    │
│  │   │   │  /data/*.db  ← PVC (PersistentVolumeClaim)       │    │     │    │
│  │   │   └─────────────────────────────────────────────────┘    │     │    │
│  │   └──────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          可观测性 (Observability)                            │
│                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│   │  Promtail   │───▶│    Loki     │◀───│   Grafana   │                    │
│   │ (日志采集)   │    │  (日志存储)  │    │  (可视化)    │                    │
│   └─────────────┘    └─────────────┘    └─────────────┘                    │
│         │                   ▲                                                │
│         │                   │                                                │
│         └───────────────────┘                                                │
│              采集 Pod 日志                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 请求流程详解

### 示例：访问 meta 服务

```
请求: curl http://localhost:9080/meta/fuel_type

1. 宿主机端口 (localhost:9080)
   │
   ├─▶ Kind Port Mapping: 9080 → 容器内 80
   │
2. Ingress-Nginx Controller (容器内 :80)
   │
   ├─▶ 匹配 Ingress 规则: /meta/* → service:meta, port:9000
   │
3. Service (meta:9000)
   │
   ├─▶ 选择器: app=meta
   │
4. Pod (meta-xxx)
   │
   ├─▶ 容器端口: 9000
   │
5. FastAPI 应用
   │
   ├─▶ 路由: /meta/fuel_type
   │
   └─▶ 返回燃料类型数据
```

### 示例：通过 NodePort 直接访问

```
请求: curl http://localhost:9000/meta/fuel_type

1. 宿主机端口 (localhost:9000)
   │
   ├─▶ Kind Port Mapping: 9000 → NodePort 30000
   │
2. Service (meta:9000, NodePort: 30000)
   │
   ├─▶ 选择器: app=meta
   │
3. Pod → FastAPI → 返回数据
```

## 服务端点

| 服务 | NodePort | Ingress 路径 | 说明 |
|------|----------|-------------|------|
| meta | 9000 | /meta | 元数据服务 |
| identity | 9001 | /company, /user | 身份认证服务 |
| vessel | 9002 | /vessel | 船舶管理服务 |
| data | 9004 | /upload, /daily | 遥测数据服务 |
| analytics | 9005 | /analytics | 分析服务 |
| Grafana | 3000 | - | 日志可视化 |

## 访问方式

### 1. NodePort 直连

```bash
# meta 服务
curl http://localhost:9000/
curl http://localhost:9000/meta/fuel_type
curl http://localhost:9000/docs

# identity 服务
curl http://localhost:9001/
curl http://localhost:9001/company

# vessel 服务
curl http://localhost:9002/
curl http://localhost:9002/vessel
```

### 2. Ingress 统一入口

```bash
# HTTP (端口 9080)
curl http://localhost:9080/meta/fuel_type
curl http://localhost:9080/company
curl http://localhost:9080/vessel

# HTTPS (端口 9443，需配置证书)
curl -k https://localhost:9443/meta/
```

### 3. 浏览器访问 Swagger UI

| 服务 | URL |
|------|-----|
| meta | http://localhost:9000/docs |
| identity | http://localhost:9001/docs |
| vessel | http://localhost:9002/docs |
| data | http://localhost:9004/docs |
| analytics | http://localhost:9005/docs |

### 4. 可观测性入口

| 组件 | URL | 说明 |
|------|-----|------|
| Grafana | http://localhost:3000 | 默认入口，已预置 `Meta Service Overview` 看板 |
| Loki Readiness | http://localhost:9100/ready | Loki 健康检查 |

> 说明：`9003` 已预留给业务应用，不再用于 Grafana。

## 数据库访问

### SQLite 文件路径

| 服务 | 容器内路径 | 本地路径 |
|------|-----------|---------|
| meta | /data/meta.db | ./data/meta.db |
| identity | /data/identity.db | ./data/identity.db |
| vessel | /data/vessel.db | ./data/vessel.db |
| data | /data/data.db | ./data/data.db |

### 复制数据库到本地

```bash
# meta
kubectl cp services/$(kubectl get pod -n services -l app=meta -o jsonpath='{.items[0].metadata.name}'):/data/meta.db ./data/meta.db

# identity
kubectl cp services/$(kubectl get pod -n services -l app=identity -o jsonpath='{.items[0].metadata.name}'):/data/identity.db ./data/identity.db

# vessel
kubectl cp services/$(kubectl get pod -n services -l app=vessel -o jsonpath='{.items[0].metadata.name}'):/data/vessel.db ./data/vessel.db
```

### DBeaver 连接

1. 新建连接 → SQLite
2. 路径设置：
   - meta: `/Users/lee/services/data/meta.db`
   - identity: `/Users/lee/services/data/identity.db`
   - vessel: `/Users/lee/services/data/vessel.db`

## 端口映射表

| 宿主机端口 | 集群端口 | 用途 |
|-----------|---------|------|
| 9000 | 30000 | meta NodePort |
| 9001 | 30001 | identity NodePort |
| 9002 | 30002 | vessel NodePort |
| 3000 | 30003 | Grafana NodePort |
| 9004 | 30004 | data NodePort |
| 9005 | 30005 | analytics NodePort |
| 9080 | 80 | Ingress HTTP |
| 9443 | 443 | Ingress HTTPS |
| 9100 | 30100 | Loki |

## 故障排查

### Ingress 404

检查 ingress 配置：
```bash
kubectl get ingress -n services
kubectl describe ingress -n services
```

### 服务无法访问

检查 pod 状态：
```bash
kubectl get pods -n services
kubectl logs -n services deployment/meta
```

### 数据库文件不存在

```bash
# 检查容器内文件
kubectl exec -n services deployment/meta -- ls -la /data/

# 检查 PVC
kubectl get pvc -n services
```

## 常用命令

```bash
# 查看所有服务
kubectl get all -n services

# 查看 ingress
kubectl get ingress -n services

# 查看日志
kubectl logs -n services deployment/meta -f

# 进入容器
kubectl exec -it -n services deployment/meta -- /bin/bash

# 端口转发
kubectl port-forward -n services svc/meta 8080:9000

# 查看集群信息
kubectl cluster-info
```