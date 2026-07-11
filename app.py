import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="Săn Deal Đa Nền Tảng", page_icon="🛍️", layout="wide")
st.title("🛍️ Săn Deal Đa Nền Tảng")
st.caption("Tiki: giá thật lấy trực tiếp qua API. Các nguồn khác: tìm qua Tavily — giá trên mô tả có thể cũ, hãy bấm link để xem giá chính xác.")

# ── Đọc API key từ Secrets (không dán key vào code để tránh lộ) ──
try:
    TAVILY_KEY = str(st.secrets["TAVILY_API_KEY"]).strip()
except Exception:
    TAVILY_KEY = ""

# ── Hướng dẫn cài key hiện ngay trong app nếu chưa có ──
if not TAVILY_KEY:
    st.warning("⚠️ Chưa cài Tavily API key — hiện tại chỉ quét được Tiki. Làm theo hướng dẫn dưới đây (1 lần, ~5 phút).")
    with st.expander("⚙️ Hướng dẫn lấy key miễn phí và cài vào app", expanded=True):
        st.markdown(
            "1. Vào **app.tavily.com** → đăng ký (đăng nhập bằng Google nhanh nhất). "
            "Miễn phí **1.000 lượt/tháng**, không cần thẻ tín dụng.\n"
            "2. Ở trang chính sau khi đăng nhập, **copy API key** (chuỗi bắt đầu bằng `tvly-`).\n"
            "3. Vào **share.streamlit.io** → app của bạn → menu **⋮** → **Settings** → **Secrets** → dán dòng sau rồi bấm **Save**:\n"
            "```\n"
            "TAVILY_API_KEY = \"tvly-dan-key-cua-ban-vao-day\"\n"
            "```\n"
            "4. Đợi app tự khởi động lại (~1 phút) là dùng được."
        )

# ── Các nguồn tìm qua Tavily (mỗi nguồn = 1 lượt/lần quét) ──
NGUON_TAVILY = {
    "Shopee": "shopee.vn",
    "Lazada": "lazada.vn",
    "CellphoneS": "cellphones.com.vn",
    "Hoàng Hà Mobile": "hoanghamobile.com",
    "Thế Giới Di Động": "thegioididong.com",
    "Điện Máy Xanh": "dienmayxanh.com",
}

ten_sp = st.text_input("Nhập tên sản phẩm (ví dụ: iPhone 16):")
chon = st.multiselect(
    "Nguồn tìm thêm ngoài Tiki:",
    list(NGUON_TAVILY.keys()),
    default=["Shopee", "Lazada", "CellphoneS"],
)
if TAVILY_KEY:
    st.caption(f"💳 Lần quét này dùng {len(chon)} lượt Tavily (miễn phí 1.000 lượt/tháng → khoảng {1000 // max(len(chon), 1)} lần quét/tháng với lựa chọn hiện tại).")


# ── Tiện ích ──
def tim_gia(text):
    """Tìm chuỗi giá kiểu Việt Nam (vd 19.990.000đ) trong đoạn văn bản."""
    mau = r"(\d{1,3}(?:[.,]\d{3})+\s?(?:[đ₫]|VN[DĐ]))"
    kq = re.findall(mau, text or "", re.IGNORECASE)
    return kq[0] if kq else "Bấm link để xem giá"


def gia_so(chuoi):
    """Đổi chuỗi giá thành số để sắp xếp; trả None nếu không có số."""
    so = re.sub(r"[^\d]", "", str(chuoi))
    return int(so) if so else None


def tim_tiki(ten):
    """Lấy giá thật từ API công khai của Tiki."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://tiki.vn/api/v2/products?limit=5&q={urllib.parse.quote(ten)}"
    r = requests.get(url, headers=headers, timeout=8)
    if r.status_code != 200:
        return [], f"Tiki trả mã lỗi {r.status_code}"
    kq = []
    for item in r.json().get("data", []):
        gia = item.get("price")
        if not gia:
            continue  # bỏ qua sản phẩm thiếu giá thay vì làm sập cả luồng
        duong_dan = item.get("url_path")
        link = f"https://tiki.vn/{duong_dan}" if duong_dan else f"https://tiki.vn/search?q={urllib.parse.quote(ten)}"
        kq.append({
            "Nguồn": "Tiki ✅ giá thật",
            "Sản phẩm": (item.get("name") or "Không rõ tên")[:70],
            "Mức giá": f"{gia:,.0f} ₫".replace(",", "."),
            "Đường link": link,
        })
    return kq, None


def tim_tavily(ten, domain):
    """Tìm sản phẩm trong 1 tên miền qua Tavily. Trả (kết quả, lỗi)."""
    r = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {TAVILY_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query": f"{ten} giá",
            "include_domains": [domain],
            "max_results": 5,
            "search_depth": "basic",
        },
        timeout=15,
    )
    if r.status_code == 200:
        return r.json().get("results", []), None
    # Lỗi được trả về rõ ràng, KHÔNG giấu đi
    try:
        chi_tiet = r.json().get("detail", "")
        if isinstance(chi_tiet, dict):
            chi_tiet = chi_tiet.get("error", "") or str(chi_tiet)
    except Exception:
        chi_tiet = r.text[:120]
    if r.status_code == 401:
        return [], "API key sai hoặc chưa dán đúng vào Secrets."
    if r.status_code in (429, 432, 433):
        return [], "Đã hết lượt miễn phí tháng này, hoặc quét quá nhanh — thử lại sau."
    return [], f"Lỗi {r.status_code}: {chi_tiet}"


# ── Nút quét chính ──
if st.button("🚀 Quét giá ngay", type="primary"):
    if not ten_sp.strip():
        st.error("⚠️ Vui lòng gõ tên sản phẩm trước!")
    else:
        tong_hop = []
        cac_loi = []
        with st.spinner(f"Đang quét giá cho “{ten_sp.strip()}”..."):
            # Luồng 1: Tiki (giá thật, không tốn lượt Tavily)
            try:
                kq, loi = tim_tiki(ten_sp.strip())
                tong_hop.extend(kq)
                if loi:
                    cac_loi.append(f"Tiki: {loi}")
            except Exception as e:
                cac_loi.append(f"Tiki: không kết nối được ({e})")

            # Luồng 2: Tavily cho từng nguồn đã chọn
            if chon and not TAVILY_KEY:
                cac_loi.append("Các nguồn khác: chưa có Tavily API key — xem hướng dẫn phía trên.")
            elif TAVILY_KEY:
                for ten_nguon in chon:
                    domain = NGUON_TAVILY[ten_nguon]
                    try:
                        kq, loi = tim_tavily(ten_sp.strip(), domain)
                        if loi:
                            cac_loi.append(f"{ten_nguon}: {loi}")
                            if "key" in loi.lower() or "hết lượt" in loi.lower():
                                break  # lỗi chung cho mọi nguồn, dừng để khỏi phí lượt
                            continue
                        for it in kq:
                            tong_hop.append({
                                "Nguồn": f"{ten_nguon} 🌐",
                                "Sản phẩm": (it.get("title") or "Không rõ tên")[:70],
                                "Mức giá": tim_gia((it.get("title") or "") + " " + (it.get("content") or "")),
                                "Đường link": it.get("url") or "",
                            })
                    except Exception as e:
                        cac_loi.append(f"{ten_nguon}: không kết nối được ({e})")

        # ── Hiển thị lỗi (nếu có) một cách RÕ RÀNG ──
        for loi in cac_loi:
            st.warning(loi)

        # ── Hiển thị kết quả ──
        if tong_hop:
            def _khoa(r):
                g = gia_so(r["Mức giá"])
                return (g is None, g or 0)

            sap_xep = sorted(tong_hop, key=_khoa)
            st.success(f"🎉 Tìm thấy {len(sap_xep)} kết quả — xếp giá thấp → cao (chưa rõ giá nằm cuối).")

            def _sach(t):
                return str(t).replace("|", "-").replace("\n", " ").strip()

            dong = ["| Nguồn | Sản phẩm | Mức giá | Link |", "|---|---|---|---|"]
            for r in sap_xep:
                link = r.get("Đường link") or ""
                lk = f"[Xem ngay](<{link}>)" if link.startswith("http") else ""
                dong.append(f"| {_sach(r['Nguồn'])} | {_sach(r['Sản phẩm'])} | **{_sach(r['Mức giá'])}** | {lk} |")
            st.markdown("\n".join(dong))
            st.caption("💡 Giá Tiki là giá thật thời điểm quét. Giá nguồn khác lấy từ mô tả kết quả tìm kiếm nên có thể cũ vài ngày — bấm link để xem giá chính xác.")
        elif not cac_loi:
            st.info("Không tìm thấy kết quả nào cho từ khoá này. Thử từ khoá ngắn gọn hơn (vd: bỏ màu sắc, dung lượng).")
