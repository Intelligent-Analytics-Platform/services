.PHONY: install lint format test test-common test-meta test-identity \
       run-meta run-identity build-meta build-identity clean

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
test: test-common test-meta test-identity

# common 单元测试
test-common:
	cd libs/common && uv run pytest -v

# meta API 测试
test-meta:
	cd apps/meta && uv run pytest -v

# identity API 测试
test-identity:
	cd apps/identity && uv run pytest -v

# 本地运行
run-meta:
	cd apps/meta && uv run uvicorn meta.app:app --reload --host 0.0.0.0 --port 8000

run-identity:
	cd apps/identity && uv run uvicorn identity.app:app --reload --host 0.0.0.0 --port 8001

# Docker 构建
build-meta:
	docker build -f apps/meta/Dockerfile -t meta-service .

build-identity:
	docker build -f apps/identity/Dockerfile -t identity-service .

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f apps/meta/meta.db apps/identity/identity.db
