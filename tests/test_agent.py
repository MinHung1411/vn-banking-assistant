"""Unit test cho logic routing — không cần load model/gọi API thật,
nên chạy được trong CI (GitHub Actions) mà không cần GEMINI_API_KEY hay GPU.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app
from src.agent import route_decision


def test_route_escalate_khi_co_co_negative_va_aspect_nhay_cam():
    state = {"message": "tài khoản tôi bị trừ tiền lạ", "escalate": True}
    assert route_decision(state) == "escalate"


def test_route_tool_khi_hoi_ty_gia():
    state = {"message": "tỷ giá USD hôm nay bao nhiêu", "escalate": False}
    assert route_decision(state) == "tool"


def test_route_tool_khi_hoi_trang_thai_the():
    state = {"message": "kiểm tra thẻ của tôi có bị khóa không", "escalate": False}
    assert route_decision(state) == "tool"


def test_route_rag_mac_dinh():
    state = {"message": "lãi suất tiết kiệm ngân hàng hiện nay thế nào", "escalate": False}
    assert route_decision(state) == "rag"


def test_chat_api_normalizes_gemini_list_response_to_string():
    with patch(
        "api.run_agent",
        return_value={
            "aspect": "DISCOUNT",
            "sentiment": "negative",
            "escalate": False,
            "response": [{"type": "text", "text": "Tỷ giá hôm nay là 26.000 VND."}],
        },
    ) as mock_run:
        client = TestClient(app)
        resp = client.post("/chat", json={"message": "Tỷ giá hôm nay như thế nào ? ", "thread_id": "session_test"})

        assert resp.status_code == 200
        assert resp.json()["response"] == "Tỷ giá hôm nay là 26.000 VND."
        mock_run.assert_called_once_with("Tỷ giá hôm nay như thế nào ? ", "session_test")


def test_clear_chat_api():
    with patch("api.clear_agent_history", return_value=True) as mock_clear:
        client = TestClient(app)
        resp = client.post("/chat/clear", json={"thread_id": "session_test"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "thread_id": "session_test", "cleared": True}
        mock_clear.assert_called_once_with("session_test")


def test_get_threads_api():
    fake_threads = [{"thread_id": "t1", "title": "Tỷ giá USD", "message_count": 2}]
    with patch("api.list_agent_threads", return_value=fake_threads):
        client = TestClient(app)
        resp = client.get("/chat/threads")
        assert resp.status_code == 200
        assert resp.json() == {"threads": fake_threads}


def test_get_history_api():
    fake_msgs = [{"role": "user", "content": "Tỷ giá USD"}, {"role": "assistant", "content": "25.000 VND"}]
    with patch("api.get_agent_history", return_value=fake_msgs):
        client = TestClient(app)
        resp = client.get("/chat/history/t1")
        assert resp.status_code == 200
        assert resp.json() == {"thread_id": "t1", "messages": fake_msgs}


def test_route_tool_khi_tinh_lai_tiet_kiem():
    state = {"message": "tính lãi gửi tiết kiệm 100 triệu", "escalate": False}
    assert route_decision(state) == "tool"


def test_calculate_savings_interest_tool():
    from src.tools import calculate_savings_interest
    res = calculate_savings_interest.invoke({"amount_vnd": 100_000_000, "term_months": 12, "interest_rate_year": 5.0})
    assert "5,000,000" in res or "5.000.000" in res or "5000000" in res or "Số tiền gửi tiết kiệm" in res


def test_delete_thread_api():
    with patch("api.clear_agent_history", return_value=True) as mock_clear:
        client = TestClient(app)
        resp = client.delete("/chat/threads/t1")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "thread_id": "t1", "deleted": True}
        mock_clear.assert_called_once_with("t1")


def test_redact_pii():
    from src.agent import redact_pii
    text = "Số CCCD của tôi là 012345678901 và số thẻ 4123456789012345 mã OTP: 123456"
    cleaned = redact_pii(text)
    assert "0123****8901" in cleaned
    assert "4123-****-****-2345" in cleaned
    assert "123456" not in cleaned


def test_search_atm_branch_tool():
    from src.tools import search_atm_branch_mock
    res = search_atm_branch_mock.invoke({"location": "Quận 1"})
    assert "Quận 1" in res
    assert "Chi nhánh Trung tâm" in res


def test_route_tool_khi_tim_atm():
    state = {"message": "tìm cây atm gần nhất ở quận 1", "escalate": False}
    assert route_decision(state) == "tool"


def test_rewrite_query_with_context_no_history():
    from src.agent import rewrite_query_with_context
    state = {"message": "lãi suất tiết kiệm", "messages": []}
    assert rewrite_query_with_context(state) == "lãi suất tiết kiệm"


def test_rewrite_query_with_context_with_history():
    from langchain_core.messages import HumanMessage, AIMessage
    from src.agent import rewrite_query_with_context
    state = {
        "message": "kỳ hạn 6 tháng thì sao",
        "messages": [
            HumanMessage(content="gói tiết kiệm online"),
            AIMessage(content="Gói tiết kiệm online có nhiều kỳ hạn"),
            HumanMessage(content="kỳ hạn 6 tháng thì sao")
        ]
    }
    with patch("src.agent.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value.content = "Lãi suất gửi tiết kiệm online kỳ hạn 6 tháng"
        res = rewrite_query_with_context(state)
        assert res == "Lãi suất gửi tiết kiệm online kỳ hạn 6 tháng"





