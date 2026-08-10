"""Tool bên ngoài cho agent gọi khi cần dữ liệu real-time / hệ thống ngân hàng.

- get_exchange_rate: gọi API tỷ giá THẬT, miễn phí, không cần key (open.er-api.com).
- check_card_status_mock: MOCK — mô phỏng gọi hệ thống ngân hàng nội bộ (không có
  hệ thống thật để kết nối trong phạm vi project này), luôn gắn nhãn [MOCK] rõ
  ràng trong output để không gây hiểu nhầm là dữ liệu thật.
"""

import random

import httpx
from langchain_core.tools import tool


@tool
def get_exchange_rate(currency: str = "USD") -> str:
    """Tra tỷ giá hối đoái hiện tại của 1 loại ngoại tệ so với VND.
    Input: mã tiền tệ 3 chữ viết hoa (VD: USD, KRW, EUR, JPY, CNY)."""
    currency = currency.strip().upper()
    try:
        resp = httpx.get(f"https://open.er-api.com/v6/latest/{currency}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get("VND")
        if rate is None:
            return f"Không tìm thấy tỷ giá VND cho {currency}."
        updated = data.get("time_last_update_utc", "N/A")
        return f"1 {currency} = {rate:,.0f} VND (tỷ giá tham khảo, cập nhật: {updated})"
    except Exception as exc:  # noqa: BLE001 — trả lỗi dễ hiểu cho agent thay vì crash
        return f"Không thể tra tỷ giá lúc này ({exc})."


@tool
def check_card_status_mock(card_last4: str = "0000") -> str:
    """[MOCK] Tra trạng thái thẻ ngân hàng theo 4 số cuối. Đây là dữ liệu giả lập
    để demo tool-calling, KHÔNG kết nối hệ thống ngân hàng thật."""
    statuses = [
        "Đang hoạt động bình thường",
        "Đang chờ kích hoạt",
        "Đã tạm khóa do nghi ngờ giao dịch bất thường",
    ]
    return f"[DỮ LIỆU GIẢ LẬP] Thẻ ****{card_last4}: {random.choice(statuses)}."


@tool
def calculate_savings_interest(amount_vnd: float = 100_000_000, term_months: int = 12, interest_rate_year: float = 5.5) -> str:
    """Tính toán số tiền lãi tiết kiệm và tổng số tiền thu được khi đáo hạn."""
    interest = amount_vnd * (interest_rate_year / 100) * (term_months / 12)
    total = amount_vnd + interest
    return (
        f"Số tiền gửi tiết kiệm: {amount_vnd:,.0f} VND\n"
        f"Kỳ hạn gửi: {term_months} tháng | Lãi suất: {interest_rate_year}%/năm\n"
        f"Tiền lãi dự kiến thu được: {interest:,.0f} VND\n"
        f"Tổng số tiền thực nhận khi đáo hạn: {total:,.0f} VND"
    )


@tool
def search_atm_branch_mock(location: str = "Quận 1") -> str:
    """[MOCK] Tra cứu vị trí cây ATM và chi nhánh/phòng giao dịch ngân hàng gần nhất theo quận/huyện/tỉnh."""
    location_clean = location.strip() if location else "Quận 1"
    return (
        f"[DỮ LIỆU MÔ PHỎNG] Chi nhánh & Cây ATM gần khu vực '{location_clean}':\n"
        f"1. Chi nhánh Trung tâm: 123 Đường Lê Lợi, {location_clean} (Giờ mở cửa: 08:00 - 17:00)\n"
        f"2. Cây ATM 24/7 Số 1: 45 Đường Nguyễn Huệ, {location_clean} (Nạp/rút tiền tự động)\n"
        f"3. Cây ATM 24/7 Số 2: 78 Đường Nam Kỳ Khởi Nghĩa, {location_clean}"
    )


