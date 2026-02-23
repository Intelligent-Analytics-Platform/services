.PHONY: install lint format test test-common test-meta test-identity test-vessel test-data \
       run-meta run-identity run-vessel run-data \
       build-meta build-identity build-vessel build-data \
       up-obs down-obs \
       kind-create kind-delete kind-load kind-apply kind-delete-apps \
       clean

# 安装所有依赖
install:
	uv sync --all-packages

# Lint 检查
lint:
	uv run ruff check .
	uv run ruff format --check .

# 自动格式化
format:
	uv run ruff check --fix .
	uv run ruff format .

# 运行所有测试
test: test-common test-meta test-identity test-vessel test-data

# common 单元测试
test-common:
	cd libs/common && uv run pytest -v

# meta API 测试
test-meta:
	cd apps/meta && uv run pytest -v

# identity API 测试
test-identity:
	cd apps/identity && uv run pytest -v

# vessel API 测试
test-vessel:
	cd apps/vessel && uv run pytest -v

# data API 测试
test-data:
	cd apps/data && uv run pytest -v

# 本地运行
run-meta:
	cd apps/meta && uv run uvicorn meta.app:app --reload --host 0.0.0.0 --port 8000

run-identity:
	cd apps/identity && uv run uvicorn identity.app:app --reload --host 0.0.0.0 --port 8001

run-vessel:
	cd apps/vessel && uv run uvicorn vessel.app:app --reload --host 0.0.0.0 --port 8002

run-data:
	cd apps/data && uv run uvicorn data.app:app --reload --host 0.0.0.0 --port 8003

# Docker 构建
build-meta:
	docker build -f apps/meta/Dockerfile -t meta-service .

build-identity:
	docker build -f apps/identity/Dockerfile -t identity-service .

build-vessel:
	docker build -f apps/vessel/Dockerfile -t vessel-service .

build-data:
	docker build -f apps/data/Dockerfile -t data-service .

# 可观测性（Loki + Grafana + Promtail）
up-obs:
	docker compose -f docker-compose.observability.yml up -d

down-obs:
	docker compose -f docker-compose.observability.yml down

# Kind 集群管理
kind-create:
	kind create cluster --config k8s/kind-config.yml

kind-delete:
	kind delete cluster --name iap

# 拉取可观测性镜像（首次）
kind-pull-obs:
	docker pull grafana/loki:3.0.0
	docker pull grafana/promtail:3.0.0
	docker pull grafana/grafana:latest

# 构建并加载所有镜像到 Kind
kind-load: build-meta build-identity build-vessel
	kind load docker-image meta-service:latest --name iap
	kind load docker-image identity-service:latest --name iap
	kind load docker-image vessel-service:latest --name iap
	kind load docker-image grafana/loki:3.0.0 --name iap
	kind load docker-image grafana/promtail:3.0.0 --name iap
	kind load docker-image grafana/grafana:latest --name iap

# 部署所有服务到 Kind
kind-apply:
	kubectl apply -f k8s/namespace.yml
	kubectl apply -f k8s/apps/
	kubectl apply -f k8s/observability/

# 删除所有应用（保留集群）
kind-delete-apps:
	kubectl delete -f k8s/observability/ --ignore-not-found
	kubectl delete -f k8s/apps/ --ignore-not-found
	kubectl delete -f k8s/namespace.yml --ignore-not-found

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f apps/meta/meta.db apps/identity/identity.db apps/vessel/vessel.db
	rm -f apps/data/data.db apps/data/data.duckdb
