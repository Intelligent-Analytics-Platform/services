-- 测试种子数据（仅用于开发环境）
-- 依赖：
--   company_id=1  来自 identity/seed.sql（测试航运有限公司）
--   ship_type=4   来自 meta/seed.sql（集装箱船 I004）
--   time_zone=9   来自 meta/seed.sql（东八区 UTC+8）
--   fuel_type_id  来自 meta/seed.sql（1=HFO-HS, 7=MDO/MGO, 11=LNG）

-- 测试船舶：集装箱轮
INSERT INTO vessel (
    name, mmsi, build_date, gross_tone, dead_weight,
    new_vessel, pitch,
    hull_clean_date, engine_overhaul_date, newly_paint_date, propeller_polish_date,
    company_id, ship_type, time_zone,
    created_at, updated_at
) VALUES (
    '测试集装箱轮', '413123456', '2018-03-15', 50000.0, 65000.0,
    0, 6.058,
    '2024-06-01', '2023-12-01', '2024-06-01', NULL,
    1, 4, 9,
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);

-- 设备：主机（me）
INSERT INTO equipment (name, type, vessel_id) VALUES
    ('主机', 'me', (SELECT id FROM vessel WHERE mmsi = '413123456'));

-- 主机燃料：LNG + HFO-HS（双燃料）
INSERT INTO equipment_fuel (equipment_id, fuel_type_id) VALUES
    ((SELECT id FROM equipment WHERE name = '主机' AND vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456')), 11),
    ((SELECT id FROM equipment WHERE name = '主机' AND vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456')), 1);

-- 设备：发电机（dg）
INSERT INTO equipment (name, type, vessel_id) VALUES
    ('辅机', 'dg', (SELECT id FROM vessel WHERE mmsi = '413123456'));

-- 辅机燃料：MDO/MGO
INSERT INTO equipment_fuel (equipment_id, fuel_type_id) VALUES
    ((SELECT id FROM equipment WHERE name = '辅机' AND vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456')), 7);

-- 功率-航速曲线（正常压载吃水）
INSERT INTO power_speed_curve (curve_name, draft_astern, draft_bow, vessel_id) VALUES
    ('设计曲线（压载）', 8.5, 7.2, (SELECT id FROM vessel WHERE mmsi = '413123456'));

-- 曲线数据点（速度 kn → 主机功率 kW）
INSERT INTO curve_data (speed_water, me_power, power_speed_curve_id) VALUES
    (10.0,  8200.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456'))),
    (12.0, 14100.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456'))),
    (14.0, 22500.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456'))),
    (16.0, 34800.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456'))),
    (18.0, 51200.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456'))),
    (20.0, 72000.0,  (SELECT id FROM power_speed_curve WHERE vessel_id = (SELECT id FROM vessel WHERE mmsi = '413123456')));
