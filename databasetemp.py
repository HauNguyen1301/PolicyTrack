# databasetemp.py
# -*- coding: utf-8 -*-

import sys
import os
from pprint import pprint

# Thêm thư mục gốc của dự án vào sys.path để có thể import các module khác
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import các hàm cần thiết từ module database chính
    from database import get_db_connection, _to_dicts
except ImportError as e:
    print(f"Lỗi không thể import từ database.py: {e}")
    print("Vui lòng đảm bảo bạn chạy script này từ thư mục gốc của dự án.")
    sys.exit(1)

def inspect_schema():
    """
    Kết nối tới database, liệt kê tất cả các bảng, và in ra schema cho mỗi bảng.
    """
    print("Đang kết nối tới database để kiểm tra schema...")
    try:
        client = get_db_connection()
        print("Kết nối thành công.")

        # 1. Liệt kê tất cả các bảng
        print("\n--- CÁC BẢNG TRONG DATABASE ---")
        tables_rs = client.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        # Sử dụng _to_dicts để xử lý kết quả một cách nhất quán
        tables_list = _to_dicts(tables_rs)
        tables = [table['name'] for table in tables_list]

        if not tables:
            print("Không tìm thấy bảng nào của người dùng trong database.")
            return

        pprint(tables)

        # 2. Hiển thị schema cho mỗi bảng
        print("\n--- CHI TIẾT SCHEMA TỪNG BẢNG ---")
        for table_name in tables:
            print(f"\n--- Bảng: {table_name} ---")
            try:
                schema_rs = client.execute(f"PRAGMA table_info('{table_name}')")
                schema_info = _to_dicts(schema_rs)
                if schema_info:
                    # In tiêu đề
                    headers = schema_info[0].keys()
                    print(f"{' | '.join(str(h) for h in headers)}")
                    print('-' * (sum(len(str(h)) for h in headers) + 3 * (len(headers) - 1)))
                    # In các dòng dữ liệu
                    for row in schema_info:
                        print(f"{' | '.join(str(row[h]) for h in headers)}")
                else:
                    print("Không thể lấy thông tin schema.")
            except Exception as e:
                print(f"Lỗi khi lấy schema cho bảng {table_name}: {e}")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình kiểm tra schema: {e}")
    finally:
        # Không cần đóng client ở đây vì nó là singleton được quản lý trong database.py
        print("\nKiểm tra schema hoàn tất.")

if __name__ == "__main__":
    inspect_schema()