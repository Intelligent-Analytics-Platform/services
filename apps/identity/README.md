# Identity 身份认证服务

船舶能效分析平台的用户与公司管理微服务，负责公司注册、用户认证和 JWT token 签发。

- **端口**：`8001`
- **OpenAPI 文档**：`http://localhost:8001/docs`

---

## 目录结构

```
apps/identity/
├── identity/
│   ├── app.py          # FastAPI 入口，lifespan 负责建表
│   ├── config.py       # 环境变量配置（JWT 参数、database_url）
│   ├── database.py     # SQLAlchemy engine + get_db 依赖
│   ├── models.py       # ORM 模型：Company / User
│   ├── repository.py   # CompanyRepository / UserRepository
│   ├── service.py      # CompanyService / UserService（含认证逻辑）
│   ├── schemas.py      # Pydantic 请求/响应 schema（含 OpenAPI examples）
│   ├── router.py       # 11 个端点（公司 5 个 + 用户 6 个）
│   └── deps.py         # JWT 认证依赖（get_current_user）
├── tests/
│   ├── conftest.py     # in-memory SQLite + seed（2 公司 + 3 用户）
│   ├── test_company_api.py
│   └── test_user_api.py
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## API 端点

所有响应格式统一：`{ "code": 200, "data": ..., "message": "..." }`

### 公司管理 `/company`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/company` | 获取所有公司 |
| POST | `/company` | 创建公司（名称唯一） |
| GET | `/company/{id}` | 获取公司详情 |
| PUT | `/company/{id}` | 部分更新公司信息 |
| DELETE | `/company/{id}` | 硬删除公司 |

### 用户管理 `/user`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/user` | 用户列表（按名称/公司过滤，支持分页） |
| POST | `/user/register` | 注册用户（密码加密存储） |
| POST | `/user/login` | 登录，返回 JWT token |
| GET | `/user/{id}` | 获取用户信息（禁用用户返回 404） |
| PUT | `/user/{id}` | 更新用户信息（当前仅手机号） |
| DELETE | `/user/{id}` | 软删除（disabled=true，数据保留） |

---

## 数据模型

### Company（公司）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键，自增 |
| `name` | str | 公司名称（唯一） |
| `address` | str | 地址 |
| `contact_person` | str | 联系人 |
| `contact_phone` | str | 联系电话 |
| `contact_email` | str | 联系邮箱 |
| `created_at` / `updated_at` | datetime | 时间戳（自动维护） |

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键，自增 |
| `username` | str | 用户名 |
| `hashed_password` | str | 加密密码（不出现在响应中） |
| `phone` | str | 手机号 |
| `company_id` | int | 所属公司 ID（FK → company.id） |
| `is_admin` | bool | 公司管理员 |
| `is_system_admin` | bool | 系统管理员 |
| `disabled` | bool | 是否禁用（软删除标记） |

---

## 认证机制

登录成功后返回 JWT token，后续请求可通过以下方式传递：

```
Authorization: Bearer <token>
# 或
Token: <token>
```

token 由 `deps.py` 中的 `get_current_user` 依赖解析，跨服务调用时使用 `Token` 自定义头。

---

## 架构

```
POST /user/login
  └─▶ router.py        解析请求体
  └─▶ UserService      authenticate_user() → create_access_token()
  └─▶ UserRepository   find_by_username()
  └─▶ SQLite

GET /user?name=zhang&company_id=1
  └─▶ router.py        Query 参数解析
  └─▶ UserService      get_user_list() → 返回 list[User]
  └─▶ UserRepository   list_users() 含过滤 + 分页
  └─▶ SQLite
```

- **软删除**：`DELETE /user/{id}` 不删除记录，将 `disabled` 置为 `true`，后续 GET 返回 404。
- **Repository 继承 BaseRepository**：Company 和 User 都有 CRUD 需求，因此合理继承 `BaseRepository[T]`，在此基础上扩展自定义查询。

---

## 本地运行

```bash
cp .env.example .env
uv run uvicorn identity.app:app --reload --port 8001
```

**环境变量**（`.env`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///identity.db` | 数据库连接串 |
| `JWT_SECRET_KEY` | `change-me-in-production` | **生产环境必须修改** |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `JWT_EXPIRE_MINUTES` | `30` | token 有效期（分钟） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

---

## 测试

```bash
uv run pytest -v
# 指定文件
uv run pytest tests/test_user_api.py -v
```

测试使用 in-memory SQLite，预置 2 个公司和 3 个用户（含 1 个 disabled 用户），覆盖：

- 公司 CRUD（含 404 处理）
- 用户列表过滤 / 分页
- 注册、登录（成功 / 密码错误 / 用户不存在）
- 软删除（delete 后 GET 返回 404）
- 密码字段不出现在响应中

---

## Docker 部署

```bash
docker build -f apps/identity/Dockerfile -t identity-service .
docker run -p 8001:8001 \
  -e JWT_SECRET_KEY=your-secret \
  identity-service
```
