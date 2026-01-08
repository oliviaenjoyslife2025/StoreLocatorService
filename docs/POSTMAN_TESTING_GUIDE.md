# Postman测试指南 - 所有端点详细配置

本指南提供所有API端点的Postman测试配置（除了 `/api/stores/search`）。

## 📋 目录

1. [准备工作](#准备工作)
2. [健康检查端点](#健康检查端点)
3. [认证端点](#认证端点)
4. [商店管理端点](#商店管理端点)
5. [用户管理端点](#用户管理端点)

---

## 🔧 准备工作

### 1. 设置基础URL

在Postman中创建环境变量：
- **变量名**: `base_url`
- **初始值**: `http://localhost:8000`

或者直接在URL中使用：`http://localhost:8000`

### 2. 测试账号

- **Admin**: `admin@test.com` / `TestPassword123!`
- **Marketer**: `marketer@test.com` / `TestPassword123!`
- **Viewer**: `viewer@test.com` / `TestPassword123!`

### 3. 保存Token

登录后会获得 `access_token`，保存到环境变量 `access_token` 以便后续使用。

---

## 1️⃣ 健康检查端点

### GET /

**用途**: 健康检查

**Method**: `GET`

**URL**: `http://localhost:8000/`

**Headers**: 无需

**Body**: 无需

**预期响应**:
```json
{
  "message": "Welcome to the Store Locator Service!"
}
```

---

## 2️⃣ 认证端点

### POST /api/auth/login

**用途**: 登录获取访问令牌

**Method**: `POST`

**URL**: `http://localhost:8000/api/auth/login`

**Headers**:
```
Content-Type: application/json
```

**Body** (raw JSON):
```json
{
  "email": "admin@test.com",
  "password": "TestPassword123!"
}
```

**预期响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "abc123def456...",
  "token_type": "bearer"
}
```

**重要**: 复制 `access_token` 的值，用于后续请求的Authorization header。

---

### POST /api/auth/refresh

**用途**: 使用刷新令牌获取新的访问令牌

**Method**: `POST`

**URL**: `http://localhost:8000/api/auth/refresh`

**Headers**:
```
Content-Type: application/json
```

**Body** (raw JSON):
```json
{
  "refresh_token": "从login响应中复制的refresh_token值"
}
```

**预期响应**:
```json
{
  "access_token": "新的access_token",
  "token_type": "bearer"
}
```

---

### POST /api/auth/logout

**用途**: 注销，撤销刷新令牌

**Method**: `POST`

**URL**: `http://localhost:8000/api/auth/logout`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Body** (raw JSON):
```json
{
  "refresh_token": "要撤销的refresh_token"
}
```

**预期响应**: `200 OK` (无响应体)

---

## 3️⃣ 商店管理端点

### POST /api/admin/stores

**用途**: 创建新商店（需要Admin或Marketer权限）

**Method**: `POST`

**URL**: `http://localhost:8000/api/admin/stores`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Body** (raw JSON):
```json
{
  "store_id": "S0001",
  "name": "Boston Downtown Store",
  "store_type": "regular",
  "status": "active",
  "latitude": 42.3601,
  "longitude": -71.0589,
  "address_street": "123 Main Street",
  "address_city": "Boston",
  "address_state": "MA",
  "address_postal_code": "02101",
  "address_country": "USA",
  "phone": "617-555-0100",
  "services": ["pharmacy", "grocery"],
  "hours_mon": "08:00-22:00",
  "hours_tue": "08:00-22:00",
  "hours_wed": "08:00-22:00",
  "hours_thu": "08:00-22:00",
  "hours_fri": "08:00-22:00",
  "hours_sat": "09:00-21:00",
  "hours_sun": "10:00-20:00"
}
```

**注意**:
- `store_id` 必须唯一
- 如果不提供 `latitude` 和 `longitude`，需要提供完整的地址信息（会自动地理编码）
- `store_type` 可选值: `flagship`, `regular`, `outlet`, `express`
- `status` 可选值: `active`, `inactive`, `temporarily_closed`

**预期响应**: 返回创建的商店信息

---

### GET /api/admin/stores

**用途**: 列出所有商店（分页，需要认证）

**Method**: `GET`

**URL**: `http://localhost:8000/api/admin/stores?page=1&page_size=10`

**Query Parameters**:
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认10

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 无需

**预期响应**:
```json
{
  "data": [
    {
      "store_id": "S0001",
      "name": "Boston Downtown Store",
      ...
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

---

### GET /api/admin/stores/{store_id}

**用途**: 获取特定商店的详细信息（需要认证）

**Method**: `GET`

**URL**: `http://localhost:8000/api/admin/stores/S0001`

**路径参数**:
- `store_id`: 商店ID（在URL中）

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 无需

**预期响应**: 返回商店详细信息

**错误响应**: 如果商店不存在，返回 `404 Not Found`

---

### PATCH /api/admin/stores/{store_id}

**用途**: 部分更新商店信息（需要Admin或Marketer权限）

**Method**: `PATCH`

**URL**: `http://localhost:8000/api/admin/stores/S0001`

**路径参数**:
- `store_id`: 商店ID（在URL中）

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Body** (raw JSON，只包含要更新的字段):
```json
{
  "name": "Updated Store Name",
  "phone": "617-555-9999",
  "services": ["pharmacy", "grocery", "bakery"],
  "status": "active",
  "hours_mon": "09:00-21:00",
  "hours_tue": "09:00-21:00",
  "hours_wed": "09:00-21:00",
  "hours_thu": "09:00-21:00",
  "hours_fri": "09:00-21:00",
  "hours_sat": "10:00-20:00",
  "hours_sun": "11:00-19:00"
}
```

**注意**:
- 只能更新: `name`, `phone`, `services`, `status`, `hours_*`
- **不能更新**: `store_id`, `latitude`, `longitude`, `address_*` 字段

**预期响应**: 返回更新后的商店信息

---

### DELETE /api/admin/stores/{store_id}

**用途**: 删除（停用）商店（需要Admin或Marketer权限）

**Method**: `DELETE`

**URL**: `http://localhost:8000/api/admin/stores/S0001`

**路径参数**:
- `store_id`: 商店ID（在URL中）

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 无需

**预期响应**: `200 OK` (无响应体)

**注意**: 这是软删除，商店状态会被设置为 `inactive`

---

### POST /api/admin/stores/import

**用途**: 批量导入商店（CSV文件，需要Admin或Marketer权限）

**Method**: `POST`

**URL**: `http://localhost:8000/api/admin/stores/import`

**Headers**:
```
Authorization: Bearer {access_token}
```
**注意**: 不要设置 `Content-Type` header，Postman会自动设置 `multipart/form-data`

**Body设置**:
1. 在Postman中，选择 **Body** 标签
2. 选择 **form-data**（不是raw或x-www-form-urlencoded）
3. 添加一个字段：
   - **Key**: `file`（必须）
   - **Type**: 点击Key旁边的下拉菜单，选择 **File**（不是Text）
   - **Value**: 点击 **Select Files** 按钮，选择你的CSV文件

**重要说明**:
- ❌ **不能使用JSON格式** - 这个端点只接受文件上传
- ✅ **必须使用form-data格式**
- ✅ **Key必须是 `file`**
- ✅ **Type必须是File类型**

**CSV文件格式示例**:

**CSV文件格式示例**:
```csv
store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S0001,Store 1,regular,active,42.3601,-71.0589,123 Main St,Boston,MA,02101,USA,617-555-0100,"pharmacy,grocery",08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00
```

**预期响应**:
```json
{
  "total_rows": 10,
  "created": 8,
  "updated": 2,
  "failed": 0,
  "results": [
    {
      "row_number": 1,
      "store_id": "S0001",
      "status": "created",
      "error": null
    }
  ]
}
```

---

## 4️⃣ 用户管理端点（仅Admin）

### POST /api/admin/users

**用途**: 创建新用户（仅Admin权限）

**Method**: `POST`

**URL**: `http://localhost:8000/api/admin/users`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Body** (raw JSON):
```json
{
  "user_id": "user001",
  "email": "newuser@test.com",
  "password": "SecurePassword123!",
  "role": "viewer"
}
```

**注意**:
- `role` 可选值: `admin`, `marketer`, `viewer`
- 必须使用Admin账号的token

**预期响应**: 返回创建的用户信息（不包含密码）

---

### GET /api/admin/users

**用途**: 列出所有用户（仅Admin权限）

**Method**: `GET`

**URL**: `http://localhost:8000/api/admin/users`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 无需

**预期响应**:
```json
{
  "data": [
    {
      "user_id": "user001",
      "email": "admin@test.com",
      "role": "admin",
      "status": "active",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 3
}
```

---

### PUT /api/admin/users/{user_id}

**用途**: 更新用户信息（仅Admin权限）

**Method**: `PUT`

**URL**: `http://localhost:8000/api/admin/users/user001`

**路径参数**:
- `user_id`: 用户ID（在URL中）

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Body** (raw JSON):
```json
{
  "role": "marketer",
  "status": "active"
}
```

**注意**:
- 可以更新 `role` 和 `status`
- `role` 可选值: `admin`, `marketer`, `viewer`
- `status` 可选值: `active`, `inactive`

**预期响应**: 返回更新后的用户信息

---

### DELETE /api/admin/users/{user_id}

**用途**: 删除（停用）用户（仅Admin权限）

**Method**: `DELETE`

**URL**: `http://localhost:8000/api/admin/users/user001`

**路径参数**:
- `user_id`: 用户ID（在URL中）

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 无需

**预期响应**: `200 OK` (无响应体)

**注意**: 这是软删除，用户状态会被设置为 `inactive`

---

## 📝 Postman使用技巧

### 1. 设置环境变量

在Postman中：
1. 点击右上角的眼睛图标
2. 点击 "Add" 创建新环境
3. 添加变量：
   - `base_url`: `http://localhost:8000`
   - `access_token`: (登录后自动填充)

### 2. 自动保存Token

在登录请求的Tests标签页中添加：
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
    pm.environment.set("refresh_token", jsonData.refresh_token);
}
```

### 3. 使用环境变量

在URL中使用: `{{base_url}}/api/admin/stores`

在Header中使用: `Bearer {{access_token}}`

### 4. 创建请求集合

建议按功能分组：
- 认证 (Authentication)
- 商店管理 (Store Management)
- 用户管理 (User Management)

---

## 🔐 权限说明

### Admin权限
- ✅ 所有商店管理操作
- ✅ 所有用户管理操作
- ✅ CSV导入

### Marketer权限
- ✅ 创建/更新/删除商店
- ✅ CSV导入
- ✅ 查看商店列表
- ❌ 用户管理

### Viewer权限
- ✅ 查看商店列表
- ✅ 查看商店详情
- ❌ 创建/更新/删除商店
- ❌ 用户管理

---

## ⚠️ 常见错误

### 401 Unauthorized
- 检查 `Authorization` header是否正确
- 检查token是否过期（15分钟）
- 重新登录获取新token

### 403 Forbidden
- 检查用户角色是否有权限
- Viewer无法创建/更新商店
- 只有Admin可以管理用户

### 404 Not Found
- 检查URL是否正确
- 检查资源ID是否存在

### 422 Validation Error
- 检查请求体格式
- 检查必填字段是否提供
- 检查字段类型是否正确

---

## 📚 相关文档

- [API文档](http://localhost:8000/docs) - Swagger UI
- [ReDoc](http://localhost:8000/redoc) - 交互式API文档

