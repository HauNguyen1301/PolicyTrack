import sqlite3
import json
import os
import bcrypt
from database import get_db_connection, init_db

# Thư mục chứa các tệp JSON
IMPORT_DIR = "data_export"

# Thứ tự nhập liệu để đảm bảo các khóa ngoại (foreign keys) được tôn trọng
IMPORT_ORDER = [
    'users',
    'sign_CF', # Thêm bảng này vào
    'nhom_quyenloi',
    'thoi_gian_cho',
    'hopdong_baohiem',
    'quyenloi_chitiet',
    'sothe_dacbiet',
    'hopdong_baohiem_history',
    'quyenloi_chitiet_history'
]

def import_data():
    """
    Nhập dữ liệu từ các tệp JSON vào một database mới.
    """
    print("Starting data import process...")
    
    # 1. Khởi tạo một database mới, sạch sẽ
    print("  - Initializing a new, clean database...")
    # Tạm thời xóa DB cũ nếu có để đảm bảo sự trong sạch
    if os.path.exists('policy_track.db'):
        os.remove('policy_track.db')
    init_db()
    print("    -> New database created.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Xóa dữ liệu mặc định đã được tạo bởi init_db() để tránh lỗi UNIQUE constraint
    print("  - Clearing default data from tables...")
    try:
        cursor.execute("DELETE FROM users;")
        cursor.execute("DELETE FROM nhom_quyenloi;")
        conn.commit()
        print("    -> Default data cleared successfully.")
    except sqlite3.Error as e:
        print(f"    -> Warning: Could not clear default data. {e}")

    # Tạo các bản ghi giữ chỗ cho sign_CF để tránh lỗi FOREIGN KEY
    sign_cf_ids_to_ensure = set()
    hopdong_file_path = os.path.join(IMPORT_DIR, "hopdong_baohiem.json")
    if os.path.exists(hopdong_file_path):
        print("  - Pre-scanning contract data for foreign key requirements...")
        with open(hopdong_file_path, 'r', encoding='utf-8') as f:
            hopdong_data = json.load(f)
            for record in hopdong_data:
                if record.get('sign_CF_id') is not None:
                    sign_cf_ids_to_ensure.add(record['sign_CF_id'])
    
    if sign_cf_ids_to_ensure:
        print(f"  - Found {len(sign_cf_ids_to_ensure)} required 'sign_CF' records. Ensuring they exist...")
        for cf_id in sign_cf_ids_to_ensure:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO sign_CF (id, mo_ta) VALUES (?, ?)",
                    (cf_id, f"Dữ liệu bị thiếu (ID: {cf_id})")
                )
            except sqlite3.Error as e:
                print(f"    -> WARNING: Could not insert placeholder for sign_CF ID {cf_id}: {e}")
        conn.commit()
        print("    -> Placeholder records for 'sign_CF' ensured.")

    # 2. Nhập dữ liệu theo đúng thứ tự
    for table_name in IMPORT_ORDER:
        file_path = os.path.join(IMPORT_DIR, f"{table_name}.json")
        
        if not os.path.exists(file_path):
            print(f"  - Skipping table '{table_name}': JSON file not found.")
            continue

        print(f"  - Importing data for table: {table_name}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"    -> Error: Could not decode JSON from {file_path}. Skipping.")
                continue

        if not data:
            print(f"    -> No data to import for '{table_name}'.")
            continue

        for record in data:
            # Đặc biệt xử lý bảng 'users' để khôi phục đúng hash mật khẩu
            if table_name == 'users' and 'password' in record:
                # Mật khẩu trong file JSON là dạng string của hash gốc.
                # Ta chỉ cần encode nó lại thành bytes để lưu vào DB.
                password_hash_str = record['password']
                record['password'] = password_hash_str.encode('utf-8')

            # Tạo câu lệnh INSERT
            columns = ', '.join(record.keys())
            placeholders = ', '.join(['?'] * len(record))
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            try:
                cursor.execute(sql, list(record.values()))
            except sqlite3.Error as e:
                print(f"    -> ERROR inserting record into '{table_name}': {e}")
                print(f"       SKIPPED RECORD: {record}")

    conn.commit()
    conn.close()
    print("\nData import process finished successfully!")

if __name__ == '__main__':
    import_data()
