-- 从本地 MySQL 同步的种子数据（company + user）
-- 注意：密码字段为哈希值，明文密码未知。

INSERT INTO company (id, name, address, contact_person, contact_phone, contact_email, created_at, updated_at) VALUES
    (1, 'Company Test', 'Shanghai', 'John Doe', '12345678', 'test@163.com', '2025-04-17 19:11:46', NULL);

INSERT INTO user (id, username, hashed_password, phone, is_admin, is_system_admin, disabled, company_id, created_at, updated_at) VALUES
    (1, 'user', '$2b$12$Dr2YLnyK4c9IkYptSKyw3OmQ5dHoLmpJ1YGTrs5.QJwbpl9LP0ZOm', '12345678', 0, 0, 0,
        (SELECT id FROM company WHERE name = 'Company Test'),
        '2025-04-17 12:35:56', NULL);
