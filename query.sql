

-- Chèn dữ liệu mẫu cho bảng thoi_gian_cho
INSERT INTO thoi_gian_cho (id, loai_cho, mo_ta) VALUES
(1, 'Bỏ chờ toàn bộ', 'Không áp dụng thời gian chờ cho bất kỳ quyền lợi nào'),
(2, 'Chờ bệnh thông thường', 'Thời gian chờ tiêu chuẩn cho các bệnh thông thường, thường là 30 ngày'),
(3, 'Chờ bệnh có sẵn', 'Thời gian chờ cho các bệnh/thương tật đã có từ trước khi tham gia bảo hiểm'),
(4, 'Chờ bệnh đặc biệt', 'Thời gian chờ cho các bệnh được liệt kê trong danh sách bệnh đặc biệt'),
(5, 'Chờ thai sản / biến chứng', 'Thời gian chờ cho quyền lợi thai sản và các biến chứng liên quan'),
(6, 'Prorata thai sản / biến chứng', 'Quyền lợi thai sản được tính theo tỷ lệ thời gian tham gia thực tế'),
(7, 'Chờ tử vong', 'Thời gian chờ cho quyền lợi tử vong do bệnh tật');



-- Chèn dữ liệu mẫu cho bảng sign_CF
INSERT INTO sign_CF (id, mo_ta) VALUES
(1, 'Miễn cả dấu & chữ ký'),
(2, 'Mộc treo + chữ ký đại diện'),
(3, 'Chỉ cần mộc treo'),
(4, 'Chỉ cần chữ ký đại diện'),
(5, 'Yêu cầu cả dấu & chữ ký');



INSERT INTO nhom_quyenloi (ten_nhom, mo_ta) VALUES 
('OP', 'Ngoại trú'),
('OP_MR', 'Điểm mở rộng liên quan ngoại trú'),
('IP', 'Nội trú'),
('IP_MR', 'Điểm mở rộng liên quan nội trú'),
('Accident', 'Tai nạn'),
('Accident_MR', 'Điểm mở rộng liên quan tai nạn')


-- SQLite
INSERT INTO hopdong_baohiem (id, soHopDong, tenCongTy, HLBH_tu, HLBH_den, coPay, sign_CF_id, isActive, created_by, created_at, updated_at)
VALUES (1, 'HCM.D07.BVC.25.HD13', 'Công ty TNHH SANOFI', '2025-01-01', '2025-12-31', 0, 1, 1, 1, '2025-06-19 13:32:16', '2025-06-19 13:32:16')


-- SQLite
INSERT INTO quyenloi_chitiet (id, hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at)
VALUES (1,1,1,"Ngoại trú","2.400.000đ / lk / kghsl","",1,'2025-06-19 13:32:16');

INSERT INTO quyenloi_chitiet (id, hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at)
VALUES (2,1,1,"Răng","2.400.000đ / năm ","MR NK",1,'2025-06-19 13:32:16');
INSERT INTO quyenloi_chitiet (id, hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at)
VALUES (3,1,1,"Khám thai","800.000đ / năm","",1,'2025-06-19 13:32:16');

INSERT INTO quyenloi_chitiet (id, hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at)
VALUES (4,1,3,"Viện phí","4.000.000đ / ngày","MR phòng vip",1,'2025-06-19 13:32:16');

DELETE FROM quyenloi_chitiet WHERE id = 4;