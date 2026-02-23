-- 测试种子数据（仅用于开发环境）
-- 测试用户密码：test1234

INSERT INTO company (name, address, contact_person, contact_phone, contact_email, created_at, updated_at) VALUES
    ('测试航运有限公司', '上海市浦东新区张江高科技园区88号', '张三', '13800000001', 'admin@test-shipping.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT INTO user (username, hashed_password, phone, is_admin, is_system_admin, disabled, company_id, created_at, updated_at) VALUES
    ('admin', '$2b$12$/GOtP3wHTASyRSGo/LtKuuAIn7KO64zx0WHtiTLxIAeSldXu1kHxi', '13900000001', 1, 1, 0,
        (SELECT id FROM company WHERE name = '测试航运有限公司'),
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
