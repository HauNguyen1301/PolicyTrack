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
    """Trả về một đối tượng client Turso đồng bộ duy nhất (singleton) sử dụng HTTPS.

    Cơ chế singleton giúp tránh chi phí tạo một connection pool HTTP mới cho mỗi
    thao tác với cơ sở dữ liệu. Tất cả các hàm sẽ dùng chung một đối tượng client.
    Kết nối sẽ được tự động tạo mới nếu chưa có hoặc đã quá 8 giờ.

    Returns:
        libsql_client.Client: Đối tượng client để tương tác với DB.
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
    """Đóng kết nối client Turso toàn cục. Nên gọi một lần khi ứng dụng thoát."""
    global _CLIENT
    if _CLIENT is not None:
        try:
            _CLIENT.close()
        finally:
            _CLIENT = None


# --- Helper to convert Turso rows to dictionaries ---
def _to_dicts(rs: libsql_client.ResultSet) -> List[Dict[str, Any]]:
    """Chuyển đổi một đối tượng ResultSet của Turso thành danh sách các dictionary.

    Hàm này cũng tự động giải mã các giá trị kiểu bytes thành chuỗi UTF-8.

    Args:
        rs (libsql_client.ResultSet): Kết quả trả về từ một câu lệnh execute.

    Returns:
        List[Dict[str, Any]]: Danh sách các dictionary, mỗi dict là một hàng dữ liệu.
    """
    if not rs.rows:
        return []
    columns = rs.columns
    
    def process_row(row):
        values = [v.decode('utf-8') if isinstance(v, bytes) else v for v in row]
        return dict(zip(columns, values))
        
    return [process_row(row) for row in rs.rows]

def hash_password(password: str) -> bytes:
    """Mã hóa mật khẩu chuỗi thành một chuỗi bytes đã được hash bằng bcrypt.

    Args:
        password (str): Mật khẩu ở dạng chuỗi thuần.

    Returns:
        bytes: Mật khẩu đã được mã hóa.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, hashed_password: bytes) -> bool:
    """Kiểm tra mật khẩu chuỗi có khớp với mật khẩu đã được mã hóa hay không.

    Args:
        password (str): Mật khẩu chuỗi thuần cần kiểm tra.
        hashed_password (bytes): Mật khẩu đã được mã hóa từ trước.

    Returns:
        bool: True nếu mật khẩu khớp, False nếu không khớp.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def apply_schema_updates(schema_file='schema.sql'):
    """
    (ĐÃ VÔ HIỆU HÓA THEO YÊU CẦU)
    Chức năng này dùng để cập nhật schema (đặc biệt là các trigger) một cách thủ công.
    Nó không còn được gọi tự động khi khởi động ứng dụng.
    """
    print("INFO: Automatic schema update process is disabled as per user request.")
    return

def init_db(schema_file: str = 'schema.sql'):
    """Khởi tạo cơ sở dữ liệu nếu chưa có.

    Hàm này sẽ kiểm tra sự tồn tại của bảng 'users'. Nếu chưa có, nó sẽ thực thi
    các câu lệnh trong file schema.sql để tạo bảng và tạo 2 người dùng mặc định
    ('admin' và 'user').

    Args:
        schema_file (str): Đường dẫn tới file .sql chứa schema của DB.
    """
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

def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Xác thực thông tin đăng nhập của người dùng.

    Args:
        username (str): Tên đăng nhập.
        password (str): Mật khẩu chuỗi thuần.

    Returns:
        Optional[Dict[str, Any]]: Một dictionary chứa thông tin người dùng (trừ mật khẩu)
                                  nếu xác thực thành công, ngược lại trả về None.
    """
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

def update_password(username: str, new_password: str):
    """Cập nhật mật khẩu cho một người dùng.

    Args:
        username (str): Tên đăng nhập của người dùng cần cập nhật.
        new_password (str): Mật khẩu mới.
    """
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

def update_user_role(username: str, new_role: str):
    """Cập nhật vai trò (role) cho một người dùng.

    Args:
        username (str): Tên đăng nhập của người dùng.
        new_role (str): Vai trò mới ('admin' hoặc 'user').
    """
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

def create_user(username: str, password: str, full_name: str, role: str) -> Tuple[bool, str]:
    """Tạo một người dùng mới trong cơ sở dữ liệu.

    Hàm sẽ kiểm tra xem tên đăng nhập đã tồn tại chưa trước khi tạo.

    Args:
        username (str): Tên đăng nhập mới.
        password (str): Mật khẩu mới.
        full_name (str): Tên đầy đủ.
        role (str): Vai trò ('admin' hoặc 'user').

    Returns:
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

def get_all_users() -> List[Dict[str, Any]]:
    """Lấy danh sách tất cả người dùng (không bao gồm mật khẩu).

    Returns:
        List[Dict[str, Any]]: Danh sách các dictionary chứa thông tin người dùng.
    """
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, username, full_name, role FROM users ORDER BY username")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        pass  # keep global client open

def search_users(search_term: str) -> List[Dict[str, Any]]:
    """Tìm kiếm người dùng theo tên đăng nhập hoặc tên đầy đủ.

    Args:
        search_term (str): Từ khóa tìm kiếm.

    Returns:
        List[Dict[str, Any]]: Danh sách người dùng khớp với từ khóa.
    """
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

def get_all_sign_cf() -> List[Dict[str, Any]]:
    """Lấy tất cả các tùy chọn 'Sign CF' từ bảng sign_CF.

    Returns:
        List[Dict[str, Any]]: Danh sách các tùy chọn.
    """
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, mo_ta FROM sign_CF ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting sign cf options: {e}")
        return []
    finally:
        pass  # keep global client open



def add_contract(contract_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Thêm một hợp đồng mới và các chi tiết liên quan (thời gian chờ, quyền lợi, thẻ đặc biệt).

    Thực hiện tuần tự các bước insert. Lưu ý: không có cơ chế rollback nếu một bước thất bại.

    Args:
        contract_data (Dict[str, Any]): Dictionary chứa toàn bộ thông tin hợp đồng.

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:
        # Step 1: Insert the main contract details
        rs = client.execute(
            """
            INSERT INTO hopdong_baohiem (
                soHopDong, tenCongTy, HLBH_tu, HLBH_den, coPay, sign_CF_id, created_by, mr_app, isActive, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+7 hours'))
            """,
            [
                contract_data['soHopDong'],
                contract_data['tenCongTy'],
                contract_data['HLBH_tu'],
                contract_data['HLBH_den'],
                contract_data['coPay'],
                contract_data['sign_CF_id'],
                contract_data.get('created_by'),
                contract_data['mr_app'],
                contract_data['isActive']
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
                 VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+7 hours'))
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

def get_all_benefit_groups() -> List[Dict[str, Any]]:
    """Lấy tất cả các nhóm quyền lợi từ bảng nhom_quyenloi.

    Returns:
        List[Dict[str, Any]]: Danh sách các nhóm quyền lợi.
    """
    client = get_db_connection()
    try:
        rs = client.execute("SELECT id, ten_nhom FROM nhom_quyenloi ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error getting benefit groups: {e}")
        return []
    finally:
        pass  # keep global client open

def search_contracts(company_name: str = '', contract_number: str = '', benefit_group_ids: Optional[List[int]] = None, status: str = 'active') -> List[Dict[str, Any]]:
    """Tìm kiếm hợp đồng dựa trên tên công ty, số hợp đồng, và trạng thái.

    Args:
        company_name (str): Tên công ty (có thể là một phần).
        contract_number (str): Số hợp đồng (có thể là một phần).
        benefit_group_ids (Optional[List[int]]): Danh sách ID các nhóm quyền lợi để lọc.
        status (str): Trạng thái hợp đồng để lọc ('active', 'inactive', 'all').

    Returns:
        List[Dict[str, Any]]: Danh sách các hợp đồng tìm thấy.
    """
    conn = get_db_connection()
    try:
        base_query = """
            SELECT DISTINCT hdb.id, hdb.tenCongTy, hdb.soHopDong, hdb.HLBH_tu, hdb.HLBH_den,
                            hdb.coPay, COALESCE(sc.mo_ta, '') AS signCF, hdb.mr_app, hdb.isActive
            FROM hopdong_baohiem hdb
            LEFT JOIN sign_CF sc ON hdb.sign_CF_id = sc.id
        """
        params = []
        where_clauses = []

        # Kiểm tra xem có bất kỳ tiêu chí tìm kiếm nào được chọn không
        has_search_criteria = company_name or contract_number or (benefit_group_ids and benefit_group_ids != [])

        # Nếu không có tiêu chí tìm kiếm nào, hiển thị tất cả hợp đồng
        if not has_search_criteria:
            base_query += " LIMIT 20"
            rs = conn.execute(base_query, params)
            contracts = _to_dicts(rs)
            detailed_contracts = []
            for contract_summary in contracts:
                details = get_contract_details_by_id(contract_summary['id'])
                if details:
                    detailed_contracts.append(details)
            return detailed_contracts

        # Lọc theo trạng thái
        if status == 'active':
            where_clauses.append("hdb.isActive = 1")
        elif status == 'inactive':
            where_clauses.append("hdb.isActive = 0")
        # Nếu status là 'all', không thêm điều kiện

        # Lọc theo từ khóa tìm kiếm (tên công ty hoặc số HĐ)
        if company_name or contract_number:
            search_conditions = []
            if company_name:
                search_conditions.append("hdb.tenCongTy LIKE ?")
                params.append(f"%{company_name}%")
            if contract_number:
                search_conditions.append("hdb.soHopDong LIKE ?")
                params.append(f"%{contract_number}%")
        
            if search_conditions:  # Chỉ thêm điều kiện nếu có search_conditions
                where_clauses.append(f"({ ' AND '.join(search_conditions) })")

        # Lọc theo nhóm quyền lợi nếu được chọn
        if benefit_group_ids and benefit_group_ids != []:
            # Thêm JOIN để có thể lọc theo nhóm quyền lợi
            base_query += " JOIN quyenloi_chitiet qlc ON hdb.id = qlc.hopdong_id"
            # Tạo placeholders cho danh sách ID
            placeholders = ','.join(['?'] * len(benefit_group_ids))
            where_clauses.append(f"qlc.nhom_id IN ({placeholders})")
            params.extend(benefit_group_ids)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        # Giới hạn kết quả trả về
        base_query += " LIMIT 20"

        # Thực thi câu lệnh và trả về kết quả
        rs = conn.execute(base_query, params)
        
        # Chuyển đổi kết quả thành danh sách các dictionary chứa chi tiết đầy đủ
        contracts = _to_dicts(rs)
        detailed_contracts = []
        for contract_summary in contracts:
            # Lấy chi tiết đầy đủ cho mỗi hợp đồng tìm thấy
            # Điều này đảm bảo dữ liệu nhất quán với các phần khác của ứng dụng
            details = get_contract_details_by_id(contract_summary['id'])
            if details:
                detailed_contracts.append(details)
        
        return detailed_contracts

    except Exception as e:
        print(f"An error occurred during contract search: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            pass  # keep global client open # Ensure the connection is closed

# --- Helper functions for contract details (using the passed connection) ---

def get_waiting_periods_for_contract(conn: libsql_client.Client, contract_id: int) -> List[Dict[str, Any]]:
    """Lấy danh sách thời gian chờ cho một hợp đồng cụ thể."""
    query = """
        SELECT tgc.loai_cho, hqc.gia_tri, tgc.mo_ta
        FROM hopdong_quydinh_cho hqc
        JOIN thoi_gian_cho tgc ON hqc.cho_id = tgc.id
        WHERE hqc.hopdong_id = ?
    """
    rs = conn.execute(query, [contract_id])
    return _to_dicts(rs)

def get_benefits_for_contract(conn: libsql_client.Client, contract_id: int, benefit_group_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Lấy danh sách quyền lợi chi tiết cho một hợp đồng, có thể lọc theo nhóm."""
    try:
        # Nếu không có nhóm quyền lợi được chọn, lấy tất cả quyền lợi
        if not benefit_group_ids:
            query = """
                SELECT qlc.*, nql.ten_nhom
                FROM quyenloi_chitiet qlc
                LEFT JOIN nhom_quyenloi nql ON qlc.nhom_id = nql.id
                WHERE qlc.hopdong_id = ?
            """
            rs = conn.execute(query, [contract_id])
            return _to_dicts(rs)
        
        # Nếu có nhóm quyền lợi được chọn, chỉ lấy quyền lợi thuộc các nhóm đó
        placeholders = ','.join(['?'] * len(benefit_group_ids))
        query = f"""
            SELECT qlc.*, nql.ten_nhom
            FROM quyenloi_chitiet qlc
            LEFT JOIN nhom_quyenloi nql ON qlc.nhom_id = nql.id
            WHERE qlc.hopdong_id = ? AND qlc.nhom_id IN ({placeholders})
        """
        params = [contract_id] + benefit_group_ids
        rs = conn.execute(query, params)
        return _to_dicts(rs)
    except Exception as e:
        print(f"Error fetching benefits for contract {contract_id}: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
        return []

def get_special_cards_for_contract(conn: libsql_client.Client, contract_id: int) -> List[Dict[str, Any]]:
    """Lấy danh sách thẻ đặc biệt của hợp đồng."""
    try:
        rs = conn.execute("""
            SELECT * FROM sothe_dacbiet WHERE hopdong_id = ?
        """, [contract_id])
        
        if not rs.rows:
            return []
            
        # Xử lý từng hàng dữ liệu
        special_cards = []
        for row in rs.rows:
            card = {}
            for i, col_name in enumerate(rs.columns):
                value = row[i]
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                card[col_name] = value
            special_cards.append(card)
            
        return special_cards
        
    except Exception as e:
        print(f"Error fetching special cards for contract {contract_id}: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
        return []

def get_contract_details_by_id(contract_id: int) -> Optional[Dict[str, Any]]:
    """Lấy toàn bộ chi tiết của một hợp đồng cụ thể dựa vào ID.

    Bao gồm thông tin chính, thời gian chờ, quyền lợi và thẻ đặc biệt.

    Args:
        contract_id (int): ID của hợp đồng cần lấy chi tiết.

    Returns:
        Optional[Dict[str, Any]]: Một dictionary chứa toàn bộ chi tiết hợp đồng, hoặc None nếu không tìm thấy.
    """
    conn = get_db_connection()
    try:
        # Lấy thông tin cơ bản của hợp đồng
        rs = conn.execute(
            """
            SELECT hdb.*, scf.mo_ta as signCF
            FROM hopdong_baohiem hdb
            LEFT JOIN sign_CF scf ON hdb.sign_CF_id = scf.id
            WHERE hdb.id = ?
            """,
            [contract_id]
        )
        
        # Xử lý kết quả trả về
        if not rs.rows:
            return None
            
        # Lấy hàng đầu tiên (chỉ có 1 hàng)
        row = rs.rows[0]
        columns = rs.columns
        
        # Chuyển đổi hàng dữ liệu thành dictionary
        contract_details = {}
        for i, col_name in enumerate(columns):
            value = row[i]
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            contract_details[col_name] = value

        # Lấy các chi tiết khác
        waiting_periods = get_waiting_periods_for_contract(conn, contract_id)
        benefits = get_benefits_for_contract(conn, contract_id)
        special_cards = get_special_cards_for_contract(conn, contract_id)

        # Trả về kết quả
        return {
            "details": contract_details,
            "waiting_periods": waiting_periods,
            "benefits": benefits,
            "special_cards": special_cards
        }

    except Exception as e:
        print(f"Error fetching contract details for ID {contract_id}: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
        return None
    finally:
        pass # keep global client open

def update_contract(contract_id: int, contract_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Cập nhật một hợp đồng hiện có.

    Thực hiện bằng cách xóa tất cả dữ liệu liên quan cũ (thời gian chờ, quyền lợi, thẻ)
    và chèn lại dữ liệu mới. Điều này đảm bảo tính nhất quán.

    Args:
        contract_id (int): ID của hợp đồng cần cập nhật.
        contract_data (Dict[str, Any]): Dictionary chứa thông tin mới của hợp đồng.

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:


        # Xóa và thêm lại dữ liệu mới
        client.execute("DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM quyenloi_chitiet WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [contract_id])

        # Cập nhật hợp đồng chính
        client.execute(
            """
            UPDATE hopdong_baohiem SET 
                soHopDong = ?,
                tenCongTy = ?,
                HLBH_tu = ?,
                HLBH_den = ?,
                coPay = ?,
                sign_CF_id = ?,
                mr_app = ?,
                updated_at = datetime('now', '+7 hours')
            WHERE id = ?
            """,
            [
                contract_data['soHopDong'],
                contract_data['tenCongTy'],
                contract_data['HLBH_tu'],
                contract_data['HLBH_den'],
                contract_data['coPay'],
                contract_data['sign_CF_id'],
                contract_data['mr_app'],
                contract_id
            ]
        )

        # Thêm lại thời gian chờ
        for waiting_period in contract_data.get('waiting_periods', []):
            client.execute(
                "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                [contract_id, waiting_period['id'], waiting_period['value']]
            )

        # Thêm lại quyền lợi
        for benefit in contract_data.get('benefits', []):
            client.execute(
                """
                INSERT INTO quyenloi_chitiet (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+7 hours'))
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

        # Thêm lại thẻ đặc biệt
        for card in contract_data.get('special_cards', []):
            client.execute(
                "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                [contract_id, card['number'], card['holder_name'], card['notes']]
            )
        
        return True, "Cập nhật hợp đồng thành công!"

    except Exception as e:
        print(f"Failed to update contract: {e}")
        return False, f"Lỗi khi cập nhật hợp đồng: {e}"
    """Cập nhật một hợp đồng hiện có.

    Thực hiện bằng cách xóa tất cả dữ liệu liên quan cũ (thời gian chờ, quyền lợi, thẻ)
    và chèn lại dữ liệu mới. Điều này đảm bảo tính nhất quán.

    Args:
        contract_id (int): ID của hợp đồng cần cập nhật.
        contract_data (Dict[str, Any]): Dictionary chứa thông tin mới của hợp đồng.

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:
        # Xóa dữ liệu cũ liên quan đến hợp đồng
        client.execute("DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM quyenloi_chitiet WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [contract_id])

        # Cập nhật thông tin chính của hợp đồng
        main_info = contract_data['main_info']
        client.execute(
            """UPDATE hopdong_baohiem
               SET tenCongTy=?, soHopDong=?, HLBH_tu=?, HLBH_den=?, coPay=?, sign_CF_id=?, mr_app=?, isActive=?
               WHERE id = ?""",
            [
                main_info['tenCongTy'], main_info['soHopDong'], main_info['HLBH_tu'],
                main_info['HLBH_den'], main_info['coPay'], main_info['sign_CF_id'],
                main_info['mr_app'], main_info.get('isActive', 1), contract_id
            ]
        )

        # Thêm lại dữ liệu mới
        for cho_id, gia_tri in contract_data.get('waiting_periods', {}).items():
            client.execute(
                "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                [contract_id, cho_id, gia_tri]
            )

        for benefit in contract_data.get('benefits', []):
            client.execute(
                """INSERT INTO quyenloi_chitiet (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [contract_id, benefit['nhom_id'], benefit['ten_quyenloi'], benefit['han_muc'], benefit['mo_ta'], 1]
            )

        for card in contract_data.get('special_cards', []):
            client.execute(
                "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                [contract_id, card['so_the'], card['ten_NDBH'], card['ghi_chu']]
            )

        return True, "Cập nhật hợp đồng thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật hợp đồng: {e}"
    finally:
        pass # keep global client open

def delete_contract(contract_id: int) -> Tuple[bool, str]:
    """Xóa một hợp đồng và tất cả dữ liệu liên quan.

    Args:
        contract_id (int): ID của hợp đồng cần xóa.

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:
        # Xóa từ các bảng phụ trước
        client.execute("DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM quyenloi_chitiet WHERE hopdong_id = ?", [contract_id])
        client.execute("DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [contract_id])
        # Xóa hợp đồng chính
        client.execute("DELETE FROM hopdong_baohiem WHERE id = ?", [contract_id])
        return True, f"Đã xóa thành công hợp đồng ID: {contract_id}."
    except Exception as e:
        return False, f"Lỗi khi xóa hợp đồng: {e}"
    finally:
        pass # keep global client open


def update_contract_status(contract_id: int, is_active: int) -> Tuple[bool, str]:
    """Cập nhật trạng thái hoạt động (isActive) của một hợp đồng.

    Args:
        contract_id (int): ID của hợp đồng cần cập nhật.
        is_active (int): Trạng thái mới (1 cho hoạt động, 0 cho không hoạt động).

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:
        client.execute(
            "UPDATE hopdong_baohiem SET isActive = ? WHERE id = ?",
            [is_active, contract_id]
        )
        return (True, "Cập nhật trạng thái hợp đồng thành công!")
    except Exception as e:
        return (False, f"Lỗi khi cập nhật trạng thái hợp đồng: {e}")
    finally:
        pass # keep global client open

def update_contract_verification(contract_id: int, user_id: int) -> Tuple[bool, str]:
    """Cập nhật người xác thực (verify_by) và thời gian xác thực cho hợp đồng."""
    client = get_db_connection()
    try:
        result = client.execute(
            "UPDATE hopdong_baohiem SET verify_by = ? WHERE id = ?",
            [user_id, contract_id]
        )
        
        if result.rows_affected > 0:
            return (True, "Xác thực hợp đồng thành công!")
        else:
            return (False, "Không tìm thấy hợp đồng để xác thực (ID không tồn tại).")
            
    except Exception as e:
        # Ghi lại lỗi ra terminal để gỡ lỗi nếu có vấn đề khác
        print(f"Database error during contract verification: {e}") 
        return (False, f"Lỗi khi xác thực hợp đồng: {e}")

# --- Các hàm quản lý Thời gian chờ, Quyền lợi, Thẻ đặc biệt (độc lập) ---

def get_all_waiting_times() -> List[Dict[str, Any]]:
    """Lấy danh sách tất cả các loại thời gian chờ có thể có.

    Returns:
        List[Dict[str, Any]]: Danh sách các dictionary chứa thông tin thời gian chờ.
    """
    conn = get_db_connection()
    try:
        rs = conn.execute("SELECT id, loai_cho, mo_ta FROM thoi_gian_cho ORDER BY id")
        return _to_dicts(rs)
    except Exception as e:
        print(f"Lỗi khi lấy danh sách thời gian chờ: {e}")
        return []
    finally:
        pass # Giữ kết nối toàn cục

def add_benefit(contract_id: int, group_id: int, name: str, limit: str, description: str) -> Tuple[bool, str]:
    """
    Thêm một quyền lợi mới cho hợp đồng.
    
    Args:
        contract_id (int): ID của hợp đồng.
        group_id (int): ID của nhóm quyền lợi.
        name (str): Tên quyền lợi.
        limit (str): Hạn mức quyền lợi.
        description (str): Mô tả chi tiết quyền lợi.
    
    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO quyenloi_chitiet (hopdong_id, nhom_id, ten_quyenloi, han_muc, mo_ta, isActive) 
            VALUES (?, ?, ?, ?, ?, 1)
        """, [contract_id, group_id, name, limit, description])
        return True, "Quyền lợi đã được thêm thành công"
    except Exception as e:
        return False, f"Lỗi khi thêm quyền lợi: {str(e)}"

def update_contract_special_cards(contract_id: int, special_cards: list) -> Tuple[bool, str]:
    """Cập nhật danh sách thẻ đặc biệt cho hợp đồng."""
    client = get_db_connection()
    try:
        client.execute("DELETE FROM sothe_dacbiet WHERE hopdong_id = ?", [contract_id])
        for card in special_cards:
            client.execute(
                "INSERT INTO sothe_dacbiet (hopdong_id, so_the, ten_NDBH, ghi_chu) VALUES (?, ?, ?, ?)",
                [contract_id, card.get('so_the', ''), card.get('ten_NDBH', ''), card.get('ghi_chu', '')]
            )
        return True, "Cập nhật thẻ đặc biệt thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật thẻ đặc biệt: {e}"

def update_contract_waiting_periods(contract_id: int, periods: list) -> Tuple[bool, str]:
    """Cập nhật danh sách thời gian chờ cho hợp đồng."""
    client = get_db_connection()
    try:
        client.execute("DELETE FROM hopdong_quydinh_cho WHERE hopdong_id = ?", [contract_id])
        for p in periods:
            client.execute(
                "INSERT INTO hopdong_quydinh_cho (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                [contract_id, p['cho_id'], p['gia_tri']]
            )
        return True, "Cập nhật thời gian chờ thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật thời gian chờ: {e}"

def add_waiting_time(loai_cho: str, mo_ta: str) -> Tuple[bool, str]:
    """Thêm một định nghĩa thời gian chờ mới.

    Args:
        loai_cho (str): Tên của loại thời gian chờ (VD: 'Bệnh thông thường').
        mo_ta (str): Mô tả chi tiết.

    Returns:
        Tuple[bool, str]: (True, "Thông báo thành công") hoặc (False, "Thông báo lỗi").
    """
    client = get_db_connection()
    try:
        client.execute(
            "INSERT INTO thoi_gian_cho (loai_cho, mo_ta) VALUES (?, ?)",
            [loai_cho, mo_ta]
        )
        return True, "Thêm thời gian chờ thành công."
    except Exception as e:
        error_message = f"Lỗi khi thêm thời gian chờ: {e}"
        print(error_message)
        return False, error_message
    finally:
        pass  # keep global client open
