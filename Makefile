.PHONY: install lint format test test-common test-meta run-meta build-meta docker-run-meta clean

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
test: test-common test-meta

# common 单元测试
test-common:
	cd libs/common && uv run pytest -v

# meta API 测试
test-meta:
	cd apps/meta && uv run pytest -v

# 本地运行 meta 服务
run-meta:
	cd apps/meta && uv run uvicorn meta.app:app --reload --host 0.0.0.0 --port 8000

# 构建 meta Docker 镜像
build-meta:
	docker build -f apps/meta/Dockerfile -t meta-service .

# Docker 运行 meta 服务
docker-run-meta:
	docker run --rm -p 8000:8000 meta-service

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f apps/meta/meta.db
