import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="Săn Deal Đa Nền Tảng", page_icon="🛍️", layout="wide")
st.title("🛍️ Săn Deal Đa Nền Tảng")
st.caption("Tiki: giá thật + ảnh thật qua API. Nguồn khác: tìm qua Tavily — giá trên mô tả có thể cũ, bấm link để xem giá chính xác.")

# ── Đọc API key từ Secrets ──
try:
    TAVILY_KEY = str(st.secrets["TAVILY_API_KEY"]).strip()
except Exception:
    TAVILY_KEY = ""

if not TAVILY_KEY:
    st.warning("⚠️ Chưa cài Tavily API key — hiện tại chỉ quét được Tiki.")
    with st.expander("⚙️ Hướng dẫn lấy key miễn phí và cài vào app", expanded=True):
        st.markdown(
            "1. Vào **app.tavily.com** → đăng ký (đăng nhập bằng Google nhanh nhất). "
            "Miễn phí **1.000 lượt/tháng**, không cần thẻ tín dụng.\n"
            "2. Copy API key (chuỗi bắt đầu bằng `tvly-`).\n"
            "3. Vào **share.streamlit.io** → app → **⋮** → **Settings** → **Secrets** → dán rồi **Save**:\n"
            "```\n"
            "TAVILY_API_KEY = \"tvly-dan-key-cua-ban-vao-day\"\n"
            "```\n"
            "4. Đợi app khởi động lại (~1 phút)."
        )

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
loc_chat = st.checkbox(
    "🎯 Lọc chặt — chỉ giữ kết quả khớp tên sản phẩm (khuyên bật)",
    value=True,
    help="Từ khóa chứa số (vd 'v8', '256gb') bắt buộc phải xuất hiện trong kết quả; loại link trang chủ/danh mục. Bỏ tick nếu muốn xem tất cả.",
)
if TAVILY_KEY:
    st.caption(f"💳 Lần quét này dùng {len(chon)} lượt Tavily (miễn phí 1.000 lượt/tháng).")


# ══ Tiện ích ══
def tim_gia(text):
    """Tìm chuỗi giá kiểu Việt Nam (vd 19.990.000đ) trong văn bản."""
    mau = r"(\d{1,3}(?:[.,]\d{3})+\s?(?:[đ₫]|VN[DĐ]))"
    kq = re.findall(mau, text or "", re.IGNORECASE)
    return kq[0] if kq else "Bấm link để xem giá"


def gia_so(chuoi):
    """Đổi chuỗi giá thành số để sắp xếp; None nếu không có số."""
    so = re.sub(r"[^\d]", "", str(chuoi))
    return int(so) if so else None


def _sach(t):
    """Loại ký tự phá vỡ định dạng markdown khỏi văn bản hiển thị."""
    return re.sub(r"[\*\_\[\]`|#>]", " ", str(t)).strip()


def _tach_tu(s):
    """Tách chuỗi thành các từ (hỗ trợ tiếng Việt có dấu)."""
    return re.findall(r"[0-9a-zà-ỹ]+", (s or "").lower())


def khop(tu_khoa, van_ban):
    """Kiểm tra kết quả có khớp từ khóa không.
    - Từ chứa SỐ (vd 'v8', '16', '256gb') là mã model → BẮT BUỘC có mặt.
    - Từ chữ: cần khớp >= 60%.
    """
    q = _tach_tu(tu_khoa)
    t = set(_tach_tu(van_ban))
    if not q:
        return True
    tu_so = [x for x in q if any(c.isdigit() for c in x)]
    tu_chu = [x for x in q if x not in tu_so]
    # Từ có số khớp cả khi viết dính liền (vd 'v8' khớp 'v8pro')
    if any(not any(x in tok for tok in t) for x in tu_so):
        return False
    if not tu_chu:
        return True
    ty_le = sum(1 for x in tu_chu if x in t) / len(tu_chu)
    return ty_le >= 0.6


def url_rac(link):
    """Nhận diện link trang chủ / danh mục chung (không phải trang sản phẩm)."""
    m = re.match(r"https?://[^/]+(/.*)?$", link or "")
    if not m:
        return True
    duong = (m.group(1) or "").strip("/")
    return len(duong) < 8


def tim_tiki(ten):
    """Giá thật + ảnh thật từ API công khai của Tiki."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://tiki.vn/api/v2/products?limit=8&q={urllib.parse.quote(ten)}"
    r = requests.get(url, headers=headers, timeout=8)
    if r.status_code != 200:
        return [], f"Tiki trả mã lỗi {r.status_code}"
    kq = []
    for item in r.json().get("data", []):
        gia = item.get("price")
        if not gia:
            continue
        ten_hang = item.get("name") or "Không rõ tên"
        duong_dan = item.get("url_path")
        link = f"https://tiki.vn/{duong_dan}" if duong_dan else f"https://tiki.vn/search?q={urllib.parse.quote(ten)}"
        kq.append({
            "Nguồn": "Tiki ✅ giá thật",
            "Sản phẩm": ten_hang,
            "Mức giá": f"{gia:,.0f} ₫".replace(",", "."),
            "Đường link": link,
            "Ảnh": item.get("thumbnail_url") or "",
            "_vanban": ten_hang,
        })
    return kq, None


def tim_tavily(ten, domain):
    """Tìm trong 1 tên miền qua Tavily. Trả (kết quả, lỗi)."""
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


# ══ Nút quét chính ══
if st.button("🚀 Quét giá ngay", type="primary"):
    if not ten_sp.strip():
        st.error("⚠️ Vui lòng gõ tên sản phẩm trước!")
    else:
        tu_khoa = ten_sp.strip()
        tong_hop = []
        cac_loi = []
        with st.spinner(f"Đang quét giá cho “{tu_khoa}”..."):
            # Luồng 1: Tiki
            try:
                kq, loi = tim_tiki(tu_khoa)
                tong_hop.extend(kq)
                if loi:
                    cac_loi.append(f"Tiki: {loi}")
            except Exception as e:
                cac_loi.append(f"Tiki: không kết nối được ({e})")

            # Luồng 2: Tavily từng nguồn
            if chon and not TAVILY_KEY:
                cac_loi.append("Các nguồn khác: chưa có Tavily API key — xem hướng dẫn phía trên.")
            elif TAVILY_KEY:
                for ten_nguon in chon:
                    domain = NGUON_TAVILY[ten_nguon]
                    try:
                        kq, loi = tim_tavily(tu_khoa, domain)
                        if loi:
                            cac_loi.append(f"{ten_nguon}: {loi}")
                            if "key" in loi.lower() or "hết lượt" in loi.lower():
                                break
                            continue
                        for it in kq:
                            tieu_de = it.get("title") or "Không rõ tên"
                            noi_dung = it.get("content") or ""
                            tong_hop.append({
                                "Nguồn": f"{ten_nguon} 🌐",
                                "Sản phẩm": tieu_de,
                                "Mức giá": tim_gia(tieu_de + " " + noi_dung),
                                "Đường link": it.get("url") or "",
                                "Ảnh": "",
                                "_vanban": tieu_de + " " + noi_dung,
                            })
                    except Exception as e:
                        cac_loi.append(f"{ten_nguon}: không kết nối được ({e})")

        # ── Bộ lọc chặt ──
        if loc_chat and tong_hop:
            truoc = len(tong_hop)
            tong_hop = [
                r for r in tong_hop
                if khop(tu_khoa, r["_vanban"]) and not url_rac(r.get("Đường link"))
            ]
            so_an = truoc - len(tong_hop)
            if so_an:
                st.caption(f"🎯 Đã ẩn {so_an} kết quả không khớp (sai model, phụ kiện, trang chủ/danh mục). Bỏ tick 'Lọc chặt' để xem tất cả.")

        # ── Lỗi hiện rõ ràng ──
        for loi in cac_loi:
            st.warning(loi)

        # ── Hiển thị kết quả dạng thẻ (tên đầy đủ, có ảnh) ──
        if tong_hop:
            def _khoa(r):
                g = gia_so(r["Mức giá"])
                return (g is None, g or 0)

            sap_xep = sorted(tong_hop, key=_khoa)
            st.success(f"🎉 {len(sap_xep)} kết quả — xếp giá thấp → cao (chưa rõ giá nằm cuối).")

            for r in sap_xep:
                c1, c2 = st.columns([1, 4])
                with c1:
                    if r.get("Ảnh"):
                        st.image(r["Ảnh"], width=76)
                    else:
                        st.markdown("## 🛒")
                with c2:
                    st.markdown(f"**{_sach(r['Sản phẩm'])}**")
                    dong = f"{_sach(r['Nguồn'])} · :red[**{_sach(r['Mức giá'])}**]"
                    link = r.get("Đường link") or ""
                    if link.startswith("http"):
                        dong += f" · [Xem ngay](<{link}>)"
                    st.markdown(dong)
                st.divider()
            st.caption("💡 Giá Tiki là giá thật thời điểm quét. Giá nguồn khác lấy từ mô tả kết quả tìm kiếm nên có thể cũ — bấm link xem giá chính xác. Ảnh chỉ có ở Tiki (API cung cấp); các nguồn khác không kèm ảnh sản phẩm.")
        elif not cac_loi:
            st.info("Không có kết quả khớp. Thử: bỏ bớt chữ trong từ khóa (giữ hãng + model, vd 'Dodoto V8'), hoặc bỏ tick 'Lọc chặt' để xem tất cả.")
