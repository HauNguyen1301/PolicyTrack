import sqlite3
import os
import bcrypt

DB_FILE = "policy_track.db"

def get_db_connection():
    """Tạo kết nối đến database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password):
    """Mã hóa mật khẩu."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed_password):
    """Kiểm tra mật khẩu có khớp với hash không."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def apply_schema_updates():
    """Kiểm tra và áp dụng các thay đổi schema mới nhất mà không xóa dữ liệu."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Kiểm tra và tạo bảng sothe_dacbiet
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sothe_dacbiet'")
    if cursor.fetchone() is None:
        print("Applying schema update: Creating 'sothe_dacbiet' table...")
        cursor.executescript("""
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
        """)
        print("'sothe_dacbiet' table and index created.")

    # Thêm các thay đổi schema khác ở đây trong tương lai

    conn.commit()
    conn.close()

def init_db(schema_file='schema.sql'):
    """Khởi tạo database và tạo user mặc định nếu database chưa tồn tại."""
    db_exists = os.path.exists(DB_FILE)
    # Nếu file DB chưa tồn tại, tạo mới và thêm dữ liệu ban đầu
    if not db_exists:
        print("Creating database...")
        conn = get_db_connection()
        with open(schema_file, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

        # Thêm dữ liệu mẫu
        hashed_password_admin = hash_password('admin')
        hashed_password_user = hash_password('123456')

        conn.execute("INSERT INTO users (username, full_name, password, role) VALUES (?, ?, ?, ?)", 
                     ('admin', 'Admin User', hashed_password_admin, 'admin'))
        conn.execute("INSERT INTO users (username, full_name, password, role) VALUES (?, ?, ?, ?)", 
                     ('creator', 'Creator User', hashed_password_user, 'creator'))
        conn.execute("INSERT INTO users (username, full_name, password, role) VALUES (?, ?, ?, ?)", 
                     ('viewer', 'Viewer User', hashed_password_user, 'viewer'))

        conn.execute("INSERT INTO sign_CF (mo_ta) VALUES (?), (?), (?)", 
                     ('Bản cứng', 'Bản mềm', 'Không yêu cầu'))

        conn.execute("INSERT INTO nhom_quyenloi (ten_nhom) VALUES (?), (?), (?), (?)", 
                     ('Nội trú', 'Ngoại trú', 'Thai sản', 'Nha khoa'))
        
        conn.commit()
        conn.close()
        print("Database created and initialized.")

    # Luôn chạy kiểm tra cập nhật schema sau khi khởi tạo
    apply_schema_updates()

# --- Các hàm xác thực và quản lý người dùng ---

def verify_user(username, password):
    """Xac thuc nguoi dung."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password(password, user['password']):
        return user
    return None

def update_password(username, new_password):
    """Cập nhật mật khẩu cho người dùng / admin"""
    new_hashed_password = hash_password(new_password)
    conn = get_db_connection()
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
    conn.commit()
    conn.close()

def update_user_role(username, new_role):
    """Cập nhật vai trò cho người dùng. / admin """
    conn = get_db_connection()
    conn.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
    conn.commit()
    conn.close()

def create_user(username, password, full_name, role):
    """Tạo một user mới."""
    conn = get_db_connection()
    try:
        hashed_pw = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            (username, hashed_pw, full_name, role)
        )
        conn.commit()
        return True, "Tạo user thành công!"
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' đã tồn tại."
    finally:
        conn.close()


def get_all_users():
    """Lấy danh sách tất cả người dùng."""
    conn = get_db_connection()
    # Lấy các cột cần thiết, không lấy password
    users = conn.execute("SELECT id, username, full_name, role FROM users ORDER BY username").fetchall()
    conn.close()
    return users

def search_users(search_term):
    """Tìm kiếm người dùng theo username hoặc full_name."""
    conn = get_db_connection()
    like_term = f"%{search_term}%"
    users = conn.execute(
        "SELECT id, username, full_name, role FROM users WHERE username LIKE ? OR full_name LIKE ? ORDER BY username",
        (like_term, like_term)
    ).fetchall()
    conn.close()
    return users

# --- Các hàm CRUD cho Hợp đồng ---

def get_all_sign_cf():
    """Lấy danh sách tất cả các tùy chọn Sign CF."""
    conn = get_db_connection()
    # Lấy id và mo_ta để sử dụng cho combobox
    sign_cfs = conn.execute("SELECT id, mo_ta FROM sign_CF ORDER BY id").fetchall()
    conn.close()
    return sign_cfs

def add_contract(contract_data):
    """Thêm một hợp đồng mới vào database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hopdong_baohiem (
                soHopDong, tenCongTy, HLBH_tu, HLBH_den, coPay, sign_CF_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_data['soHopDong'],
            contract_data['tenCongTy'],
            contract_data['HLBH_tu'],
            contract_data['HLBH_den'],
            contract_data.get('coPay', 0.0),
            contract_data['sign_CF_id'],
            contract_data['user_id']
        ))
        conn.commit()
        return True, "Thêm hợp đồng thành công!"
    except sqlite3.IntegrityError:
        return False, f"Lỗi: Số hợp đồng '{contract_data['soHopDong']}' đã tồn tại."
    except Exception as e:
        return False, f"Đã xảy ra lỗi không xác định: {e}"
    finally:
        conn.close()

def get_all_benefit_groups():
    """Lấy danh sách tất cả các nhóm quyền lợi."""
    conn = get_db_connection()
    # Lấy id và ten_nhom để sử dụng cho việc lọc
    groups = conn.execute("SELECT id, ten_nhom FROM nhom_quyenloi ORDER BY id").fetchall()
    conn.close()
    return groups

def search_contracts(company_name, contract_number, benefit_group_ids):
    """
    Tìm kiếm hợp đồng, trả về dữ liệu được nhóm theo từng hợp đồng, bao gồm cả thẻ đặc biệt.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Bước 1: Lọc và lấy ID các hợp đồng thỏa mãn điều kiện ---
    filter_query = "SELECT DISTINCT h.id FROM hopdong_baohiem h"
    filter_params = []
    where_clauses = ["h.isActive = 1"]

    if benefit_group_ids:
        filter_query += " JOIN quyenloi_chitiet q ON h.id = q.hopdong_id"
        placeholders = ','.join('?' for _ in benefit_group_ids)
        where_clauses.append(f"q.nhom_id IN ({placeholders})")
        filter_params.extend(benefit_group_ids)

    if company_name:
        where_clauses.append("h.tenCongTy LIKE ?")
        filter_params.append(f"%{company_name}%")

    if contract_number:
        where_clauses.append("h.soHopDong LIKE ?")
        filter_params.append(f"%{contract_number}%")

    if len(where_clauses) > 1:
        filter_query += " WHERE " + " AND ".join(where_clauses)

    matching_ids = [row['id'] for row in cursor.execute(filter_query, filter_params).fetchall()]

    if not matching_ids:
        conn.close()
        return []

    # --- Bước 2: Lấy tất cả chi tiết cho các hợp đồng đã tìm thấy ---
    ids_placeholder = ','.join('?' for _ in matching_ids)
    details_params = list(matching_ids)

    details_query = f"""
        SELECT
            h.id AS hopdong_id, h.soHopDong, h.tenCongTy, h.HLBH_tu, h.HLBH_den, h.coPay,
            scf.mo_ta AS signCF_mo_ta,
            tgc.loai_cho AS thoigiancho_loai,
            hqc.gia_tri AS thoigiancho_giatri,
            q.ten_quyenloi, q.han_muc, q.mo_ta AS quyenloi_mo_ta
        FROM
            hopdong_baohiem h
        LEFT JOIN sign_CF scf ON h.sign_CF_id = scf.id
        LEFT JOIN hopdong_quydinh_cho hqc ON h.id = hqc.hopdong_id
        LEFT JOIN thoi_gian_cho tgc ON hqc.cho_id = tgc.id
        LEFT JOIN quyenloi_chitiet q ON h.id = q.hopdong_id
        WHERE h.id IN ({ids_placeholder})"""

    if benefit_group_ids:
        nhom_ids_placeholder = ','.join('?' for _ in benefit_group_ids)
        details_query += f" AND (q.nhom_id IS NULL OR q.nhom_id IN ({nhom_ids_placeholder}))"
        details_params.extend(benefit_group_ids)

    details_query += " ORDER BY h.soHopDong, q.ten_quyenloi, tgc.loai_cho"

    all_details = cursor.execute(details_query, details_params).fetchall()

    # --- Bước 3: Xử lý và nhóm kết quả bằng Python ---
    contracts_data = {}
    for row in all_details:
        hd_id = row['hopdong_id']
        if hd_id not in contracts_data:
            contracts_data[hd_id] = {
                'details': {
                    'id': hd_id, 
                    'soHopDong': row['soHopDong'], 'tenCongTy': row['tenCongTy'],
                    'HLBH_tu': row['HLBH_tu'], 'HLBH_den': row['HLBH_den'],
                    'coPay': row['coPay'], 'signCF': row['signCF_mo_ta']
                },
                'waiting_periods': set(),
                'benefits': set(),
                'special_cards': [] # Khởi tạo là list trống
            }
        
        if row['thoigiancho_loai']:
            contracts_data[hd_id]['waiting_periods'].add(
                (row['thoigiancho_loai'], row['thoigiancho_giatri'])
            )

        if row['ten_quyenloi']:
            contracts_data[hd_id]['benefits'].add(
                (row['ten_quyenloi'], row['han_muc'], row['quyenloi_mo_ta'])
            )

    # --- Bước 4: Lấy thông tin thẻ đặc biệt cho từng hợp đồng ---
    for hd_id in contracts_data:
        cursor.execute("SELECT so_the, ten_NDBH, ghi_chu FROM sothe_dacbiet WHERE hopdong_id = ?", (hd_id,))
        special_cards_raw = cursor.fetchall()
        contracts_data[hd_id]['special_cards'] = [dict(card) for card in special_cards_raw]

    conn.close() # Đóng kết nối sau khi tất cả các truy vấn hoàn tất

    # --- Bước 5: Chuyển set thành list và sắp xếp để có thứ tự nhất quán ---
    final_results = []
    for hd_id in sorted(contracts_data.keys()):
        data = contracts_data[hd_id]
        data['waiting_periods'] = sorted(list(data['waiting_periods']))
        data['benefits'] = sorted(list(data['benefits']))
        final_results.append(data)
        
    return final_results