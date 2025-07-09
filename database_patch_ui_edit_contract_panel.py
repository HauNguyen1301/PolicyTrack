# PATCH: Các hàm cập nhật dành cho UI EditContractPanel
from typing import Tuple
from database import get_db_connection

def update_contract_waiting_periods(contract_id: int, periods: list) -> Tuple[bool, str]:
    """Cập nhật danh sách thời gian chờ cho hợp đồng."""
    client = get_db_connection()
    try:
        client.execute("DELETE FROM thoi_giancho_hopdong WHERE hopdong_id = ?", [contract_id])
        for p in periods:
            client.execute(
                "INSERT INTO thoi_giancho_hopdong (hopdong_id, cho_id, gia_tri) VALUES (?, ?, ?)",
                [contract_id, p['cho_id'], p['gia_tri']]
            )
        return True, "Cập nhật thời gian chờ thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật thời gian chờ: {e}"

def update_contract_general_info(contract_id: int, general_info: dict) -> Tuple[bool, str]:
    """Cập nhật thông tin chung của hợp đồng."""
    client = get_db_connection()
    try:
        set_clause = ', '.join([f"{k} = ?" for k in general_info.keys()])
        params = list(general_info.values()) + [contract_id]
        query = f"UPDATE hopdong_baohiem SET {set_clause} WHERE id = ?"
        client.execute(query, params)
        return True, "Cập nhật thông tin chung thành công!"
    except Exception as e:
        return False, f"Lỗi khi cập nhật thông tin chung: {e}"


