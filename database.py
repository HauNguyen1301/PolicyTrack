import os
from typing import Any, Dict, List, Tuple
import bcrypt
import re
import libsql_client
import certifi
# Use certifi's CA bundle when system store may be missing
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
from dotenv import load_dotenv

# --- Load Environment Variables for Turso ---
load_dotenv()  # Load environment variables from a .env file if present

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
# --- Turso Connection Helper (singleton) ---
from typing import Optional
from datetime import datetime, timedelta

_CLIENT: Optional[libsql_client.Client] = None
_CLIENT_CREATED_AT: Optional[datetime] = None  # UTC timestamp of creation

def get_db_connection() -> libsql_client.Client:
    """Return a singleton synchronous Turso client using HTTPS.

    This avoids the overhead of creating a new HTTP connection pool for
    every DB operation. All functions share the same client instance.
    """
    global _CLIENT, _CLIENT_CREATED_AT
    now = datetime.utcnow()
    # Recreate client if missing or older than 8 hours
    if _CLIENT is None or _CLIENT_CREATED_AT is None or now - _CLIENT_CREATED_AT > timedelta(hours=8):
        if _CLIENT is not None:
            try:
                _CLIENT.close()
            except Exception:
                pass
            _CLIENT = None
        
        http_url = TURSO_DATABASE_URL.replace("libsql", "https", 1)
        _CLIENT = libsql_client.create_client_sync(url=http_url, auth_token=TURSO_AUTH_TOKEN)
        _CLIENT_CREATED_AT = now
        
    return _CLIENT


def close_db_connection():
    """Close the global Turso client (call once on application exit)."""
    global _CLIENT
    if _CLIENT is not None:
        try:
            _CLIENT.close()
        finally:
            _CLIENT = None


# --- Helper to convert Turso rows to dictionaries ---
def _to_dicts(rs: libsql_client.ResultSet) -> List[Dict[str, Any]]:
    """Converts an ExecuteResult to a list of dictionaries, decoding bytes to UTF-8 strings."""
    if not rs.rows:
        return []
    columns = rs.columns
    
    def process_row(row):
        values = [v.decode('utf-8') if isinstance(v, bytes) else v for v in row]
        return dict(zip(columns, values))
        
    return [process_row(row) for row in rs.rows]

def hash_password(password):
    """Mã hóa mật khẩu."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed_password):
    """Kiểm tra mật khẩu có khớp với hash không."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def apply_schema_updates(schema_file='schema.sql'):
    """
    (ĐÃ VÔ HIỆU HÓA THEO YÊU CẦU)
    Chức năng này dùng để cập nhật schema (đặc biệt là các trigger) một cách thủ công.
    Nó không còn được gọi tự động khi khởi động ứng dụng.
    """
    print("INFO: Automatic schema update process is disabled as per user request.")
    return

def init_db(schema_file='schema.sql'):
    """Initializes the database by creating tables and a default admin user if they don't exist."""
    client = get_db_connection()
    try:
        # Check if the 'users' table exists as a proxy for DB initialization
        rs = client.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if len(rs.rows) > 0:
            print("Database already initialized.")
            return

        print("Database not initialized. Creating schema and default users...")

        # Read and execute schema file
        with open(schema_file, 'r', encoding='utf-8') as f:
            # Split SQL script into individual statements
            sql_script = f.read()
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            
            # Execute each statement individually as transactions are not supported over HTTP
            for statement in statements:
                client.execute(statement)

        # Add default users
        hashed_password_admin = hash_password('admin')
        client.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ['admin', hashed_password_admin, 'Administrator', 'admin']
        )
        
        hashed_password_user = hash_password('user')
        client.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ['user', hashed_password_user, 'Normal User', 'user']
        )
        
        print("Database initialized successfully.")

    except Exception as e:
        print(f"An error occurred during DB initialization: {e}")
    finally:
        pass  # keep global client open


# --- Các hàm xác thực và quản lý người dùng ---

def verify_user(username, password):
    """Verifies user credentials against the database."""
    client = get_db_connection()
    try:
        rs = client.execute("SELECT * FROM users WHERE username = ?", [username])
        
        if not rs.rows:
            return None
            
        # Manually build the user dict to preserve password as bytes
        user_row = rs.rows[0]
        columns = rs.columns
        user_dict = {}
        hashed_password = None

        for idx, col_name in enumerate(columns):
            value = user_row[idx]
            if col_name == 'password':
                hashed_password = value # Keep as bytes
                user_dict[col_name] = value
            else:
                # Decode other byte strings to text
                user_dict[col_name] = value.decode('utf-8') if isinstance(value, bytes) else value

        if hashed_password and check_password(password, hashed_password):
            # Do not return the password hash to the application
            del user_dict['password']
            return user_dict
            
    except Exception as e:
        print(f"Error during user verification: {e}")
    finally:
        pass  # keep global client open
        
    return None

def update_password(username, new_password):
    """Updates the password for a given user."""
    client = get_db_connection()
    try:
        hashed_password = hash_password(new_password)
        client.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            [hashed_password, username]
        )
    except Exception as e:
        print(f"Error updating password: {e}")
    finally:
        pass  # keep global client open

def update_user_role(username, new_role):
    """Updates the role for a given user."""
    client = get_db_connection()
    try:
        client.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            [new_role, username]
        )
    except Exception as e:
        print(f"Error updating user role: {e}")
    finally:
        pass  # keep global client open

def create_user(username, password, full_name, role) -> Tuple[bool, str]:
    """
    Tạo một người dùng mới trong cơ sở dữ liệu.
    Kiểm tra xem người dùng đã tồn tại chưa trước khi tạo.
    Trả về:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    conn = get_db_connection()
    try:
        # Kiểm tra xem username đã tồn tại chưa
        rs = conn.execute("SELECT username FROM users WHERE username = ?", [username])
        if len(rs.rows) > 0:
            return (False, f"Tên đăng nhập '{username}' đã tồn tại.")

        hashed_password = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            [username, hashed_password, full_name, role]
        )
        return (True, f"Người dùng '{username}' đã được tạo thành công!")
    except Exception as e:
        return (False, f"Đã xảy ra lỗi khi tạo người dùng: {e}")
    finally:
        pass  # keep global client open

def get_all_users():
    """Retrieves a list of all users (without passwords)."""
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, username, full_name, role FROM users ORDER BY username")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        pass  # keep global client open

def search_users(search_term):
    """Searches for users by username or full name."""
    client = get_db_connection()
    try:
        like_term = f'%{search_term}%'
        rs = client.execute(
            "SELECT id, username, full_name, role FROM users WHERE username LIKE ? OR full_name LIKE ?",
            [like_term, like_term]
        )
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error searching users: {e}")
        return []
    finally:
        pass  # keep global client open


# --- Các hàm CRUD cho Hợp đồng ---

def get_all_sign_cf():
    """Retrieves all Sign CF options."""
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, mo_ta FROM sign_CF ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting sign cf options: {e}")
        return []
    finally:
        pass  # keep global client open

def add_contract(contract_data):
    """Adds a new contract and its related details sequentially."""
    client = get_db_connection()
    try:
        # Step 1: Insert the main contract details
        rs = client.execute(
            """
            INSERT INTO hopdong_baohiem (
                soHopDong, tenCongTy, HLBH_tu, HLBH_den, coPay, sign_CF_id, created_by, mr_app
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                contract_data['soHopDong'],
                contract_data['tenCongTy'],
                contract_data['HLBH_tu'],
                contract_data['HLBH_den'],
                contract_data['coPay'],
                contract_data['sign_CF_id'],
                contract_data.get('created_by'),
                contract_data['mr_app']
            ]
        )
        contract_id = rs.last_insert_rowid

        if not contract_id:
            raise Exception("Failed to retrieve the new contract ID after insertion.")

        # Step 2: Insert waiting periods
        for waiting_period in contract_data.get('waiting_periods', []):
            client.execute(
                "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                [contract_id, waiting_period['id'], waiting_period['value']]
            )

        # Step 3: Insert benefit details
        for benefit in contract_data.get('benefits', []):
            client.execute(
                """
                INSERT INTO quyenloi_chitiet (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [
                    contract_id,
                    benefit['group_id'],
                    benefit['name'],
                    benefit['limit'],
                    benefit['description'],
                    1  # isActive default
                ]
            )

        # Step 4: Insert special cards
        for card in contract_data.get('special_cards', []):
            client.execute(
                "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                [contract_id, card['number'], card['holder_name'], card['notes']]
            )
        
        return True, "Thêm hợp đồng thành công!"

    except Exception as e:
        print(f"Failed to add contract: {e}")
        # NOTE: Cannot roll back changes due to lack of transaction support.
        return False, f"Lỗi khi thêm hợp đồng: {e}"
    finally:
        pass  # keep global client open

def get_all_benefit_groups():
    """Retrieves all benefit group options."""
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, ten_nhom FROM nhom_quyenloi ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting benefit groups: {e}")
        return []
    finally:
        pass  # keep global client open

def search_contracts(company_name='', contract_number='', benefit_group_ids=None):
    if benefit_group_ids is None:
        benefit_group_ids = []
    """
    Searches for contracts using a per-operation connection and positional parameters for robustness.
    """
    conn = get_db_connection() # Create a fresh connection for this operation
    try:
        base_query = """
            SELECT DISTINCT hdb.id, hdb.tenCongTy, hdb.soHopDong, hdb.HLBH_tu, hdb.HLBH_den,
                            hdb.coPay, COALESCE(sc.mo_ta, '') AS signCF, hdb.mr_app
            FROM hopdong_baohiem hdb
            LEFT JOIN sign_CF sc ON hdb.sign_CF_id = sc.id
        """
        # Luôn lọc hợp đồng đang hoạt động
        conditions = ["hdb.isActive = 1"]
        params = []  # Use a list for positional parameters

        if company_name:
            conditions.append("tenCongTy LIKE ?")
            params.append(f"%{company_name}%")

        if contract_number:
            conditions.append("soHopDong LIKE ?")
            params.append(f"%{contract_number}%")

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        # Giới hạn số kết quả tối đa 10 bản ghi để giảm tải UI
        base_query += " LIMIT 10"

        # Execute the primary search query
        rs = conn.execute(base_query, params)
        all_matching_contracts = _to_dicts(rs)

        if not all_matching_contracts:
            return []

        # If benefit groups are selected, filter the results
        if benefit_group_ids:
            ids_placeholder = ', '.join(['?'] * len(benefit_group_ids))
            # Note: Table and column names in this query must match your actual schema
            filter_query = f"""
                SELECT DISTINCT hopdong_id FROM quyenloi_chitiet WHERE nhom_id IN ({ids_placeholder})
            """
            filter_rs = conn.execute(filter_query, benefit_group_ids)
            valid_contract_ids = {row[0] for row in filter_rs.rows}
            
            contracts_to_process = [c for c in all_matching_contracts if c['id'] in valid_contract_ids]
        else:
            contracts_to_process = all_matching_contracts

        # Fetch details for the final list of contracts
        results = []
        for contract_details in contracts_to_process:
            contract_id = contract_details['id']
            contract_data = {
                "details": contract_details,
                # Pass the active connection to helper functions
                "waiting_periods": get_waiting_periods_for_contract(conn, contract_id),
                "benefits": get_benefits_for_contract(conn, contract_id, benefit_group_ids),
                "special_cards": get_special_cards_for_contract(conn, contract_id)
            }
            results.append(contract_data)
        return results

    except Exception as e:
        print(f"An error occurred during contract search: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            pass  # keep global client open # Ensure the connection is closed

# --- Helper functions for contract details (using the passed connection) ---

def get_waiting_periods_for_contract(conn, contract_id):
    """Trả về list of dicts [{'loai_cho': name, 'gia_tri': value}] cho một hợp đồng."""
    query = """
        SELECT tgc.loai_cho, hqc.gia_tri
        FROM hopdong_quydinh_cho hqc
        JOIN thoi_gian_cho tgc ON hqc.cho_id = tgc.id
        WHERE hqc.hopdong_id = ?
    """
    rs = conn.execute(query, [contract_id])
    return _to_dicts(rs)

def get_benefits_for_contract(conn, contract_id, benefit_group_ids=None):
    """Trả về list of dicts để UI hiển thị."""
    base_query = """
        SELECT qlc.ten_quyenloi, qlc.han_muc, qlc.mo_ta
        FROM quyenloi_chitiet qlc
        WHERE qlc.hopdong_id = ? AND qlc.isActive = 1
    """
    params = [contract_id]

    if benefit_group_ids:
        placeholders = ', '.join(['?'] * len(benefit_group_ids))
        query = f"{base_query} AND qlc.nhom_id IN ({placeholders})"
        params.extend(benefit_group_ids)
    else:
        query = base_query

    rs = conn.execute(query, params)
    return _to_dicts(rs)

def get_special_cards_for_contract(conn, contract_id):
    """Trả về danh sách thẻ đặc biệt của hợp đồng với tên cột đúng UI mong đợi."""
    query = """
        SELECT so_the, ten_NDBH, ghi_chu
        FROM sothe_dacbiet
        WHERE hopdong_id = ?
    """
    try:
        rs = conn.execute(query, [contract_id])
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error fetching special cards for contract {contract_id}: {e}")
        return []
        print(f"Error fetching special cards for contract {contract_id}: {e}")
        return []

def add_benefit(contract_id, benefit_group_id, benefit_name, benefit_limit, benefit_desc, created_by: Optional[int] = None, is_active: int = 1):
    """Adds a single benefit to a contract.

    Args:
        contract_id: ID of the contract.
        benefit_group_id: Benefit group ID.
        benefit_name: Name of the benefit.
        benefit_limit: Limit value.
        benefit_desc: Description.
        created_by: ID of the user performing the insert.
        is_active: 1 (default) or 0.
    """
    client = get_db_connection()
    try:
        client.execute(
            """INSERT INTO quyenloi_chitiet (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, created_by, isActive, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            [contract_id, benefit_group_id, benefit_name, benefit_limit, benefit_desc, created_by, is_active]
        )
        print(f"Successfully added benefit '{benefit_name}' to contract {contract_id}.")
        return True
    except Exception as e:
        print(f"Error adding benefit to contract {contract_id}: {e}")
        return False
    finally:
        pass  # keep global client open

def update_contract_general_info(hopdong_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Cập nhật thông tin chung cho một hợp đồng cụ thể.

    Args:
        hopdong_id: ID của hợp đồng cần cập nhật.
        data: Một từ điển chứa các trường cần cập nhật.
              Các key phải khớp với tên cột trong bảng 'hopdong_baohiem'.
              Ví dụ: {'soHopDong': '123', 'tenCongTy': 'Tên mới'}

    Returns:
        Một tuple (success: bool, message: str).
    """
    client = get_db_connection()
    if not data:
        return False, "Không có dữ liệu để cập nhật."

    # Xây dựng phần SET của câu lệnh SQL một cách linh hoạt
    set_clauses = []
    params = []
    # Danh sách các cột được phép cập nhật
    allowed_columns = ['soHopDong', 'tenCongTy', 'HLBH_tu', 'HLBH_den', 'coPay']

    for key, value in data.items():
        if key in allowed_columns:
            set_clauses.append(f"{key} = ?")
            params.append(value)

    if not set_clauses:
        return False, "Không có trường hợp lệ nào để cập nhật."

    params.append(hopdong_id)  # Cho mệnh đề WHERE

    sql = f"UPDATE hopdong_baohiem SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        client.execute(sql, params)
        return True, "Cập nhật thông tin chung thành công!"
    except Exception as e:
        print(f"Lỗi khi cập nhật thông tin chung của hợp đồng: {e}")
        return False, f"Lỗi khi cập nhật thông tin chung: {e}"
    finally:
        pass  # Giữ kết nối client toàn cục


def get_all_waiting_times():
    """Retrieves all waiting time options."""
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, loai_cho, mo_ta FROM thoi_gian_cho ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting waiting times: {e}")
        return []
    finally:
        pass  # keep global client open

def update_contract_waiting_periods(hopdong_id, waiting_periods):
    """
    Atomically updates the waiting periods for a contract using a batch operation.
    This first deletes all existing periods for the contract, then inserts the new ones.
    """
    conn = get_db_connection()
    try:
        stmts = []
        # Statement to delete old periods
        stmts.append(libsql_client.Statement("DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [hopdong_id]))

        # Statements to insert new periods
        if waiting_periods:
            for wp in waiting_periods:
                stmts.append(
                    libsql_client.Statement(
                        "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                        [hopdong_id, wp['cho_id'], wp['gia_tri']]
                    )
                )
        
        # Execute as a batch
        if stmts:
            conn.batch(stmts)
        print(f"Đã cập nhật thành công {len(waiting_periods)} quy định thời gian chờ cho hợp đồng ID: {hopdong_id}")

    except Exception as e:
        print(f"Database error while updating waiting periods for contract {hopdong_id}: {e}")
        raise Exception(f"Lỗi database khi cập nhật thời gian chờ: {e}")

def update_contract_special_cards(hopdong_id, special_cards):
    """
    Atomically updates the special cards for a contract using a batch operation.
    This first deletes all existing cards for the contract, then inserts the new ones.
    """
    conn = get_db_connection()
    try:
        stmts = []
        # Statement to delete old cards
        stmts.append(libsql_client.Statement("DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [hopdong_id]))

        # Statements to insert new cards
        if special_cards:
            for card in special_cards:
                stmts.append(
                    libsql_client.Statement(
                        "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                        [hopdong_id, card['so_the'], card['ten_NDBH'], card['ghi_chu']]
                    )
                )
        
        # Execute as a batch
        if stmts:
            conn.batch(stmts)
        print(f"Đã cập nhật thành công {len(special_cards)} thẻ đặc biệt cho hợp đồng ID: {hopdong_id}")

    except Exception as e:
        print(f"Database error while updating special cards for contract {hopdong_id}: {e}")
        raise Exception(f"Lỗi database khi cập nhật thẻ đặc biệt: {e}")

def add_waiting_time(loai_cho, mo_ta):
    """Adds a new waiting time definition."""
    client = get_db_connection()
    try:
        client.execute(
            "INSERT INTO thoi_gian_cho (loai_cho, mo_ta) VALUES (?, ?)",
            [loai_cho, mo_ta]
        )
        return True
    except Exception as e:
        print(f"Error adding waiting time (might be a duplicate): {e}")
        return False
    finally:
        pass  # keep global client open

# === NEW SEARCH FUNCTION ===


def get_contract_by_id(hopdong_id: int, benefit_group_ids=None):
    """Fetch a single contract with all related details by its ID.

    Returns list with one element (same shape as search_contracts) or empty list
    """
    if benefit_group_ids is None:
        benefit_group_ids = []
    conn = get_db_connection()
    try:
        rs = conn.execute(
            """
            SELECT hdb.id, hdb.tenCongTy, hdb.soHopDong, hdb.HLBH_tu, hdb.HLBH_den,
                   hdb.coPay, COALESCE(sc.mo_ta, '') AS signCF, hdb.mr_app, hdb.isActive
            FROM hopdong_baohiem hdb
            LEFT JOIN sign_CF sc ON hdb.sign_CF_id = sc.id
            WHERE hdb.id = ?
            LIMIT 1
            """,
            [hopdong_id]
        )
        rows = rs.rows
        if not rows:
            return []
        details = _to_dicts(rs)[0]
        contract = {
            'details': details,
            'waiting_periods': get_waiting_periods_for_contract(conn, hopdong_id),
            'benefits': get_benefits_for_contract(conn, hopdong_id, benefit_group_ids),
            'special_cards': get_special_cards_for_contract(conn, hopdong_id)
        }
        return [contract]
    except Exception as exc:
        print(f"Error in get_contract_by_id: {exc}")
        return []
    finally:
        pass  # keep connection

# === NEW SEARCH FUNCTION ===

def search_contracts_keyword(search_term: str, benefit_group_ids=None):
    """Search contracts by a single keyword matching either company name or contract number.
    Args:
        search_term: The keyword to look for (partial match).
        benefit_group_ids: Optional list of benefit group IDs to filter results by.
    Returns:
        List of contract dicts with same structure as search_contracts.
    """
    if benefit_group_ids is None:
        benefit_group_ids = []

    conn = get_db_connection()
    try:
        base_query = (
            """
            SELECT DISTINCT hdb.id, hdb.tenCongTy, hdb.soHopDong, hdb.HLBH_tu, hdb.HLBH_den,
                            hdb.coPay, COALESCE(sc.mo_ta, '') AS signCF, hdb.mr_app
            FROM hopdong_baohiem hdb
            LEFT JOIN sign_CF sc ON hdb.sign_CF_id = sc.id
            WHERE hdb.isActive = 1 AND (hdb.tenCongTy LIKE ? OR hdb.soHopDong LIKE ?)
            LIMIT 10
            """
        )
        like_term = f"%{search_term}%"
        rs = conn.execute(base_query, [like_term, like_term])
        candidate_contracts = _to_dicts(rs)
        if not candidate_contracts:
            return []

        # Optional filtering by benefit groups
        if benefit_group_ids:
            placeholders = ', '.join(['?'] * len(benefit_group_ids))
            filter_q = f"SELECT DISTINCT hopdong_id FROM quyenloi_chitiet WHERE nhom_id IN ({placeholders})"
            filter_rs = conn.execute(filter_q, benefit_group_ids)
            valid_ids = {row[0] for row in filter_rs.rows}
            contracts_to_process = [c for c in candidate_contracts if c['id'] in valid_ids]
        else:
            contracts_to_process = candidate_contracts

        results = []
        for details in contracts_to_process:
            cid = details['id']
            results.append({
                'details': details,
                'waiting_periods': get_waiting_periods_for_contract(conn, cid),
                'benefits': get_benefits_for_contract(conn, cid, benefit_group_ids),
                'special_cards': get_special_cards_for_contract(conn, cid)
            })
        return results
    except Exception as exc:
        print(f"Error in search_contracts_keyword: {exc}")
        return []
    finally:
        pass  # keep global client open