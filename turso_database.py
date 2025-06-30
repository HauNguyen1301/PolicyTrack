"""
Turso-backed database layer for PolicyTrack.
Requires environment variables TURSO_DATABASE_URL and TURSO_AUTH_TOKEN or a .env file.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import bcrypt
from dotenv import load_dotenv
import libsql_client

load_dotenv()

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
    raise RuntimeError("Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN environment variables")

# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db_connection() -> libsql_client.Client:
    """Return a synchronous Turso client using HTTPS to avoid WebSocket issues."""
    http_url = TURSO_DATABASE_URL.replace("libsql", "https", 1)
    return libsql_client.create_client_sync(url=http_url, auth_token=TURSO_AUTH_TOKEN)

# ---------------------------------------------------------------------------
# Helper to convert rows
# ---------------------------------------------------------------------------

def _to_dicts(rs: libsql_client.ExecuteResult) -> List[Dict[str, Any]]:
    """Converts an ExecuteResult to a list of dictionaries, decoding bytes to UTF-8 strings."""
    if not rs.rows:
        return []
    columns = rs.columns
    
    def process_row(row):
        # Decode any value that is bytes to a utf-8 string
        values = [v.decode('utf-8') if isinstance(v, bytes) else v for v in row]
        return dict(zip(columns, values))
        
    return [process_row(row) for row in rs.rows]

# ---------------------------------------------------------------------------
# Public API used by UI
# ------------------------

def init_db():
    """Initializes the database schema and creates a default admin user if needed."""
    conn = get_db_connection()
    try:
        # Execute each statement individually since HTTPS does not support transactions
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hopdong_baohiem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soHopDong TEXT UNIQUE NOT NULL,
            tenCongTy TEXT NOT NULL,
            diaChi TEXT,
            soDienThoai TEXT,
            email TEXT,
            HLBH_tu DATE,
            HLBH_den DATE,
            chuongTrinhBH TEXT,
            soNguoiThamGia INTEGER,
            phiBaoHiem REAL,
            ghiChu TEXT,
            nguoi_phu_trach TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS thongtin_bosung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hopdong_id INTEGER NOT NULL,
            ma_nhan_vien TEXT,
            ho_ten TEXT,
            ngay_sinh DATE,
            gioi_tinh TEXT,
            chuc_vu TEXT,
            phong_ban TEXT,
            chi_nhanh TEXT,
            email_cong_ty TEXT,
            so_dien_thoai TEXT,
            quan_he TEXT,
            FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS thongtin_taikham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hopdong_id INTEGER NOT NULL,
            thoi_gian_cho_benh_dac_biet INTEGER,
            thoi_gian_cho_sinh_de INTEGER,
            FOREIGN KEY (hopdong_id) REFERENCES hopdong_baohiem(id) ON DELETE CASCADE
        );
        """)

        # Check if admin user exists
        rs = conn.execute("SELECT id FROM users WHERE username = 'admin'")
        if not rs.rows:
            # Create default admin user if not present
            hashed_password = bcrypt.hashpw(b'admin', bcrypt.gensalt())
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('admin', hashed_password, 'admin')
            )
            print("Default admin user created.")
        
        print("Database initialized successfully.")
    except libsql_client.LibsqlError as e:
        print(f"Database initialization failed: {e}")
    finally:
        conn.close()

def check_user(username: str, password: str) -> Dict[str, Any] | None:
    conn = get_db_connection()
    try:
        rs = conn.execute("SELECT * FROM users WHERE username = ? AND isActive = 1", (username,))
        if not rs.rows:
            return None
        user = rs.rows[0]
        stored = user["password"]
        if isinstance(stored, str):
            stored = stored.encode()
        if bcrypt.checkpw(password.encode(), stored):
            return dict(user)
        return None
    finally:
        conn.close()


def get_all_contracts() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        rs = conn.execute(
            "SELECT id, soHopDong, tenCongTy, HLBH_den FROM hopdong_baohiem ORDER BY HLBH_den DESC"
        )
        return _to_dicts(rs)
    finally:
        conn.close()


def get_data_for_add_contract_frame() -> Tuple[Dict[str, int], Dict[str, int]]:
    conn = get_db_connection()
    try:
        rs1 = conn.execute("SELECT id, mo_ta FROM sign_CF ORDER BY mo_ta")
        rs2 = conn.execute("SELECT id, loai_cho FROM thoi_gian_cho ORDER BY loai_cho")
        return {r["mo_ta"]: r["id"] for r in rs1.rows}, {r["loai_cho"]: r["id"] for r in rs2.rows}
    finally:
        conn.close()


def add_contract(contract_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Adds a new contract by executing statements sequentially (no transaction)."""
    conn = get_db_connection()
    hopdong_id = None
    try:
        # Step 1: Insert into the main contract table
        rs_main = conn.execute(
            "INSERT INTO hopdong_baohiem (soHopDong, tenCongTy, diaChi, soDienThoai, email, HLBH_tu, HLBH_den, chuongTrinhBH, soNguoiThamGia, phiBaoHiem, ghiChu, nguoi_phu_trach) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                contract_data['soHopDong'], contract_data['tenCongTy'], contract_data.get('diaChi'),
                contract_data.get('soDienThoai'), contract_data.get('email'), contract_data.get('HLBH_tu'),
                contract_data.get('HLBH_den'), contract_data.get('chuongTrinhBH'), contract_data.get('soNguoiThamGia'),
                contract_data.get('phiBaoHiem'), contract_data.get('ghiChu'), contract_data.get('nguoi_phu_trach')
            )
        )
        hopdong_id = rs_main.last_row_id
        if hopdong_id is None:
            # Attempt to retrieve the ID by querying the unique contract number
            rs_id = conn.execute("SELECT id FROM hopdong_baohiem WHERE soHopDong = ?", (contract_data['soHopDong'],))
            if rs_id.rows:
                hopdong_id = rs_id.rows[0][0]
            else:
                raise libsql_client.LibsqlError("Failed to get last row ID and could not retrieve it manually.", "UNKNOWN")

        # Step 2: Insert into the waiting time table
        taikham_data = contract_data.get('thongtin_taikham', {})
        conn.execute(
            "INSERT INTO thongtin_taikham (hopdong_id, thoi_gian_cho_benh_dac_biet, thoi_gian_cho_sinh_de) VALUES (?, ?, ?)",
            (hopdong_id, taikham_data.get('thoi_gian_cho_benh_dac_biet'), taikham_data.get('thoi_gian_cho_sinh_de'))
        )

        # Step 3: Insert supplementary info for each person
        bosung_list = contract_data.get('thongtin_bosung', [])
        for person_data in bosung_list:
            conn.execute(
                "INSERT INTO thongtin_bosung (hopdong_id, ma_nhan_vien, ho_ten, ngay_sinh, gioi_tinh, chuc_vu, phong_ban, chi_nhanh, email_cong_ty, so_dien_thoai, quan_he) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    hopdong_id, person_data.get('ma_nhan_vien'), person_data.get('ho_ten'), person_data.get('ngay_sinh'),
                    person_data.get('gioi_tinh'), person_data.get('chuc_vu'), person_data.get('phong_ban'),
                    person_data.get('chi_nhanh'), person_data.get('email_cong_ty'), person_data.get('so_dien_thoai'),
                    person_data.get('quan_he')
                )
            )
        
        return True, "Thêm hợp đồng thành công!"
    except libsql_client.LibsqlError as exc:
        if "UNIQUE constraint failed" in str(exc):
            return False, "Số hợp đồng đã tồn tại."
        return False, f"DB error: {exc}"
    finally:
        conn.close()
