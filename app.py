import streamlit as st
import requests
import urllib.parse
import pandas as pd
import re
from duckduckgo_search import DDGS
import time

st.set_page_config(page_title="Trợ Lý Săn Deal Đa Nền Tảng", page_icon="🛍️", layout="wide")
st.title("🛍️ Hệ Thống Quét Deal Lai (Hybrid)")
st.write("Tự động kết hợp dữ liệu API trực tiếp và Vệ tinh tìm kiếm.")

ten_sp = st.text_input("Nhập tên sản phẩm (Ví dụ: iPhone 16):")

def tim_gia(text):
    mau_gia = r'(\d{1,3}(?:[.,]\d{3})+(?:\s?[đ₫]|(?:\s?VND|VNĐ)))'
    kq = re.findall(mau_gia, text, re.IGNORECASE)
    return kq[0] if kq else "Bấm link để xem giá"

if st.button("🚀 Quét Toàn Bộ Internet"):
    if not ten_sp.strip():
        st.error("⚠️ Vui lòng gõ tên sản phẩm!")
    else:
        ket_qua_tong_hop = []
        
        with st.spinner(f"🔄 Đang kết nối API chuyên dụng và lùng sục mạng lưới cho '{ten_sp}'..."):
            
            # --- LUỒNG 1: Lấy dữ liệu chắc chắn từ TIKI API ---
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                url_tiki = f"https://tiki.vn/api/v2/products?limit=5&q={urllib.parse.quote(ten_sp)}"
                res = requests.get(url_tiki, headers=headers, timeout=5)
                if res.status_code == 200:
                    for item in res.json().get('data', []):
                        if 'price' in item:
                            ket_qua_tong_hop.append({
                                "Nguồn": "Tiki 🔵",
                                "Sản phẩm": item.get('name')[:60] + "...",
                                "Mức giá": f"{item.get('price'):,} ₫",
                                "Đường link": f"https://tiki.vn/{item.get('url_path')}"
                            })
            except Exception:
                pass # Bỏ qua lỗi nếu Tiki lag

            # ---             # --- LUỒNG 2: Quét các trang bán lẻ (Không bị chặn như Shopee/Lazada) ---
            # Chúng ta sẽ tìm kiếm trực tiếp trên google (thông qua DDGS) 
            # nhưng giới hạn kết quả vào các trang bán lẻ uy tín
            try:
                ddgs = DDGS()
                # Danh sách các trang web bán lẻ thân thiện với bot
                danh_sach_web = ["cellphones.com.vn", "hoanghamobile.com"]
                
                for site in danh_sach_web:
                    # Tìm kiếm sản phẩm trong chính website đó
                    truy_van = f"site:{site} {ten_sp}"
                    ket_qua_ddgs = ddgs.text(truy_van, region='vn-vi', max_results=2)
                    
                    for item in ket_qua_ddgs:
                        ket_qua_tong_hop.append({
                            "Nguồn": site.split('.')[0].capitalize() + " 🌐",
                            "Sản phẩm": item['title'][:50] + "...",
                            "Mức giá": "Bấm để xem",
                            "Đường link": item['href']
                        })
            except Exception:
                pass

        # --- TỔNG HỢP VÀ HIỂN THỊ ---
        if ket_qua_tong_hop:
            df = pd.DataFrame(ket_qua_tong_hop)
            st.success(f"🎉 Đã tìm thấy {len(df)} kết quả hợp lệ!")
            st.dataframe(
                df,
                column_config={"Đường link": st.column_config.LinkColumn("Xem Deal Ngay")},
                hide_index=True,
                use_container_width=True
            )
        else:
            st.error("😭 Máy chủ đang bị chặn toàn diện hoặc không có mặt hàng này. Vui lòng thử lại sau 5 phút.")
