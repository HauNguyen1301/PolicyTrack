-- 1. Bảng Users (Cập nhật với cột password_hash)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password VARCHAR(255) NOT NULL,
    role TEXT,
    isActive INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Tra Cứu: Hình thức xác nhận trên hồ sơ bồi thường
CREATE TABLE sign_CF (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mo_ta TEXT NOT NULL UNIQUE
);

-- 3. Bảng Tra Cứu: Các loại quy định về thời gian chờ
CREATE TABLE thoi_gian_cho (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loai_cho TEXT NOT NULL UNIQUE,
    mo_ta TEXT
);

-- 4. Bảng Tra Cứu: Nhóm quyền lợi
CREATE TABLE nhom_quyenloi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_nhom TEXT NOT NULL UNIQUE,
    mo_ta TEXT
);

-- 5. Bảng Hợp Đồng Bảo Hiểm (Bảng chính, chỉ lưu trạng thái hiện tại)
CREATE TABLE hopdong_baohiem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    soHopDong TEXT NOT NULL UNIQUE,
    tenCongTy TEXT NOT NULL,
    HLBH_tu DATE NOT NULL,
    HLBH_den DATE NOT NULL,
    coPay TEXT NOT NULL DEFAULT 0.0,
    sign_CF_id INTEGER,
    isActive INTEGER DEFAULT 1,
    created_by INTEGER,
    mr_app TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sign_CF_id) REFERENCES sign_CF(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- (Các bảng và trigger còn lại giữ nguyên)
-- 6. Bảng Nối: Áp dụng quy định chờ cho hợp đồng
CREATE TABLE hopdong_quydinh_cho (
    hopdong_id INTEGER NOT NULL,
    cho_id INTEGER NOT NULL,
    gia_tri TEXT,
    ghi_chu TEXT,
    PRIMARY KEY (hopdong_id, cho_id),
    FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE,
    FOREIGN KEY (cho_id) REFERENCES thoi_gian_cho(id)
);
-- 7. Bảng Quyền lợi Mở rộng
CREATE TABLE quyenloi_chitiet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hopdong_id INTEGER NOT NULL,
    nhom_id INTEGER,
    ten_quyenloi TEXT NOT NULL,
    han_muc REAL DEFAULT 0.0,
    mo_ta TEXT,
    isActive INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE,
    FOREIGN KEY (nhom_id) REFERENCES nhom_quyenloi(id)
);
-- ===================================================================
-- 8. CÁC BẢNG HISTORY CẦN THIẾT
-- ===================================================================
-- 8.1. Bảng Lịch sử Sửa đổi Hợp đồng Bảo hiểm
CREATE TABLE hopdong_baohiem_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hopdong_id INTEGER NOT NULL,
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    old_data TEXT, -- JSON string
    new_data TEXT, -- JSON string
    FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
-- 8.2. Bảng Lịch sử Sửa đổi Quyền lợi Mở rộng
CREATE TABLE quyenloi_chitiet_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quyenloi_id INTEGER NOT NULL,
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    old_data TEXT, -- JSON string
    new_data TEXT, -- JSON string
    FOREIGN KEY (quyenloi_id) REFERENCES quyenloi_chitiet(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
-- ===================================================================
-- 9. CÁC TRIGGER TỰ ĐỘNG
-- ===================================================================
-- 9.1. Trigger tự động cập nhật updated_at cho hopdong_baohiem
CREATE TRIGGER update_hopdong_baohiem_updated_at
AFTER UPDATE ON hopdong_baohiem
FOR EACH ROW
BEGIN
    UPDATE hopdong_baohiem
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;
-- 9.2. Trigger tự động ghi log khi CẬP NHẬT hopdong_baohiem
CREATE TRIGGER log_hopdong_baohiem_update
AFTER UPDATE ON hopdong_baohiem
FOR EACH ROW
BEGIN
    INSERT INTO hopdong_baohiem_history (hopdong_id, updated_by, old_data, new_data)
    VALUES (
        OLD.id,
        NEW.created_by, -- Giả sử user ID được truyền vào khi cập nhật
        JSON_OBJECT(
            'soHopDong', OLD.soHopDong, 'tenCongTy', OLD.tenCongTy,
            'HLBH_tu', OLD.HLBH_tu, 'HLBH_den', OLD.HLBH_den,
            'coPay', OLD.coPay, 'sign_CF_id', OLD.sign_CF_id,
            'isActive', OLD.isActive,
            'mr_app', OLD.mr_app
        ),
        JSON_OBJECT(
            'soHopDong', NEW.soHopDong, 'tenCongTy', NEW.tenCongTy,
            'HLBH_tu', NEW.HLBH_tu, 'HLBH_den', NEW.HLBH_den,
            'coPay', NEW.coPay, 'sign_CF_id', NEW.sign_CF_id,
            'isActive', NEW.isActive,
            'mr_app', NEW.mr_app
        )
    );
END;
-- 9.3. Trigger tự động ghi log khi CẬP NHẬT quyenloi_chitiet
CREATE TRIGGER log_quyenloi_chitiet_update
AFTER UPDATE ON quyenloi_chitiet
FOR EACH ROW
BEGIN
    INSERT INTO quyenloi_chitiet_history (quyenloi_id, old_data, new_data)
    VALUES (
        OLD.id,
        JSON_OBJECT(
            'ten_quyenloi', OLD.ten_quyenloi, 'han_muc', OLD.han_muc,
            'mo_ta', OLD.mo_ta, 'isActive', OLD.isActive    ,
            'nhom_id', OLD.nhom_id
        ),
        JSON_OBJECT(
            'ten_quyenloi', NEW.ten_quyenloi, 'han_muc', NEW.han_muc,
            'mo_ta', NEW.mo_ta, 'isActive', NEW.isActive,
            'nhom_id', NEW.nhom_id
        )
    );
END;

-- ===================================================================
-- 10. INDEXES
-- ===================================================================
CREATE INDEX idx_hopdong_soHopDong ON hopdong_baohiem(soHopDong);
CREATE INDEX idx_quyenloi_hopdong_id ON quyenloi_chitiet(hopdong_id);
CREATE INDEX idx_hopdong_history_id ON hopdong_baohiem_history(hopdong_id);
CREATE INDEX idx_quyenloi_history_id ON quyenloi_chitiet_history(quyenloi_id);

-- 11. Bảng Thẻ Đặc Biệt (Gán theo hợp đồng)
CREATE TABLE sothe_dacbiet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hopdong_id INTEGER NOT NULL,
    so_the TEXT NOT NULL,
    ten_NDBH TEXT NOT NULL, -- ten Nguoi Duoc Bao Hiem
    ghi_chu TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE
);  

CREATE INDEX idx_sothe_dacbiet_hopdong_id ON sothe_dacbiet(hopdong_id);