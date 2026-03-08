# 新老 API 返回结果对比报告

- 生成时间: 2026-03-08 20:25:06
- 说明: 本报告对可直接调用的核心接口进行运行时返回对比（状态码/顶层结构/data 结构）。

| 接口 | 老状态码 | 新状态码 | 顶层结构一致 | data类型一致 | data字段一致 | 兼容等级 |
|---|---:|---:|---|---|---|---|
| `GET /company` | 200 | 200 | 是 | 是 | 否 | 中 |
| `GET /company/1` | 200 | 200 | 是 | 是 | 否 | 中 |
| `GET /user?offset=0&limit=10` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /user/1` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /vessel?offset=0&limit=10` | 200 | 200 | 是 | 是 | 否 | 中 |
| `GET /vessel/1` | 200 | 200 | 是 | 是 | 否 | 中 |
| `GET /meta/fuel_type` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /meta/ship_type` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /meta/time_zone` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /meta/attributes` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /meta/attribute_mapping` | 200 | 200 | 是 | 是 | 是 | 高 |
| `GET /upload/vessel/1/history` | 200 | 200 | 是 | 是 | 否 | 中 |

## 详细差异

### `GET /company`
- 老URL: `http://localhost:8000/company`
- 新URL: `http://localhost:9001/company`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 1, 'item_keys': ['address', 'contact_email', 'contact_person', 'contact_phone', 'created_at', 'id', 'name']} new={'type': 'list', 'len': 1, 'item_keys': ['address', 'contact_email', 'contact_person', 'contact_phone', 'id', 'name']}
- 兼容等级: 中

### `GET /company/1`
- 老URL: `http://localhost:8000/company/1`
- 新URL: `http://localhost:9001/company/1`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'dict', 'keys': ['address', 'contact_email', 'contact_person', 'contact_phone', 'created_at', 'id', 'name']} new={'type': 'dict', 'keys': ['address', 'contact_email', 'contact_person', 'contact_phone', 'id', 'name']}
- 兼容等级: 中

### `GET /user?offset=0&limit=10`
- 老URL: `http://localhost:8000/user?offset=0&limit=10`
- 新URL: `http://localhost:9001/user?offset=0&limit=10`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 1, 'item_keys': ['company_id', 'disabled', 'id', 'is_admin', 'is_system_admin', 'phone', 'username']} new={'type': 'list', 'len': 1, 'item_keys': ['company_id', 'disabled', 'id', 'is_admin', 'is_system_admin', 'phone', 'username']}
- 兼容等级: 高

### `GET /user/1`
- 老URL: `http://localhost:8000/user/1`
- 新URL: `http://localhost:9001/user/1`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'dict', 'keys': ['company_id', 'disabled', 'id', 'is_admin', 'is_system_admin', 'phone', 'username']} new={'type': 'dict', 'keys': ['company_id', 'disabled', 'id', 'is_admin', 'is_system_admin', 'phone', 'username']}
- 兼容等级: 高

### `GET /vessel?offset=0&limit=10`
- 老URL: `http://localhost:8000/vessel?offset=0&limit=10`
- 新URL: `http://localhost:9002/vessel?offset=0&limit=10`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 4, 'item_keys': ['build_date', 'cii_rating', 'company_id', 'created_at', 'dead_weight', 'engine_overhaul_date', 'engine_state', 'equipment_fuel', 'gross_tone', 'hull_clean_date', 'hull_propeller_state', 'id', 'latest_cii', 'me_fuel_consumption_nmile', 'mmsi', 'name', 'new_vessel', 'newly_paint_date', 'pitch', 'power_speed_curve', 'propeller_polish_date', 'ship_type', 'speed_water', 'time_zone']} new={'type': 'list', 'len': 4, 'item_keys': ['build_date', 'company_id', 'created_at', 'curves', 'dead_weight', 'engine_overhaul_date', 'equipments', 'gross_tone', 'hull_clean_date', 'id', 'mmsi', 'name', 'new_vessel', 'newly_paint_date', 'pitch', 'propeller_polish_date', 'ship_type', 'time_zone']}
- 兼容等级: 中

### `GET /vessel/1`
- 老URL: `http://localhost:8000/vessel/1`
- 新URL: `http://localhost:9002/vessel/1`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'dict', 'keys': ['build_date', 'cii_rating', 'company_id', 'created_at', 'dead_weight', 'engine_overhaul_date', 'engine_state', 'equipment_fuel', 'gross_tone', 'hull_clean_date', 'hull_propeller_state', 'id', 'latest_cii', 'me_fuel_consumption_nmile', 'mmsi', 'name', 'new_vessel', 'newly_paint_date', 'pitch', 'power_speed_curve', 'propeller_polish_date', 'ship_type', 'speed_water', 'time_zone']} new={'type': 'dict', 'keys': ['build_date', 'company_id', 'created_at', 'curves', 'dead_weight', 'engine_overhaul_date', 'equipments', 'gross_tone', 'hull_clean_date', 'id', 'mmsi', 'name', 'new_vessel', 'newly_paint_date', 'pitch', 'propeller_polish_date', 'ship_type', 'time_zone']}
- 兼容等级: 中

### `GET /meta/fuel_type`
- 老URL: `http://localhost:8000/meta/fuel_type`
- 新URL: `http://localhost:9000/meta/fuel_type`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 16, 'item_keys': ['cf', 'id', 'name_abbr', 'name_cn', 'name_en']} new={'type': 'list', 'len': 16, 'item_keys': ['cf', 'id', 'name_abbr', 'name_cn', 'name_en']}
- 兼容等级: 高

### `GET /meta/ship_type`
- 老URL: `http://localhost:8000/meta/ship_type`
- 新URL: `http://localhost:9000/meta/ship_type`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 13, 'item_keys': ['cii_related_tone', 'code', 'id', 'name_cn', 'name_en']} new={'type': 'list', 'len': 13, 'item_keys': ['cii_related_tone', 'code', 'id', 'name_cn', 'name_en']}
- 兼容等级: 高

### `GET /meta/time_zone`
- 老URL: `http://localhost:8000/meta/time_zone`
- 新URL: `http://localhost:9000/meta/time_zone`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 25, 'item_keys': ['explaination', 'id', 'name_cn', 'name_en']} new={'type': 'list', 'len': 25, 'item_keys': ['explaination', 'id', 'name_cn', 'name_en']}
- 兼容等级: 高

### `GET /meta/attributes`
- 老URL: `http://localhost:8000/meta/attributes`
- 新URL: `http://localhost:9000/meta/attributes`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 11, 'item_keys': ['attribute', 'description']} new={'type': 'list', 'len': 11, 'item_keys': ['attribute', 'description']}
- 兼容等级: 高

### `GET /meta/attribute_mapping`
- 老URL: `http://localhost:8000/meta/attribute_mapping`
- 新URL: `http://localhost:9000/meta/attribute_mapping`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 5, 'item_keys': ['attribute_left', 'attribute_right']} new={'type': 'list', 'len': 5, 'item_keys': ['attribute_left', 'attribute_right']}
- 兼容等级: 高

### `GET /upload/vessel/1/history`
- 老URL: `http://localhost:8000/upload/vessel/1/history`
- 新URL: `http://localhost:9004/upload/vessel/1/history`
- 状态码: old=200 new=200
- 顶层keys: old=['code', 'data', 'message'] new=['code', 'data', 'message']
- data结构: old={'type': 'list', 'len': 10, 'item_keys': ['created_at', 'date_end', 'date_start', 'file_path', 'id', 'vessel_id']} new={'type': 'list', 'len': 0, 'item_keys': []}
- 兼容等级: 中
