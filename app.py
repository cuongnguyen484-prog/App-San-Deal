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

            # --- LUỒNG 2: Dùng DuckDuckGo quét thêm các web ngoài ---
            try:
                ddgs = DDGS()
                # Tách nhỏ truy vấn để không bị hệ thống chặn
                cac_nguon_ngoai = ["hoanghamobile", "cellphones"] 
                
                for nguon in cac_nguon_ngoai:
                    truy_van = f"{ten_sp} {nguon}"
                    kq_tim_kiem = ddgs.text(truy_van, region='vn-vi', max_results=3)
                    
                    if kq_tim_kiem:
                        for item in kq_tim_kiem:
                            # Chỉ lấy kết quả thực sự thuộc về nguồn đang tìm
                            if nguon in item['href'].lower():
                                ket_qua_tong_hop.append({
                                    "Nguồn": nguon.capitalize() + " 🌐",
                                    "Sản phẩm": item['title'][:60] + "...",
                                    "Mức giá": tim_gia(item['body'] + " " + item['title']),
                                    "Đường link": item['href']
                                })
                    time.sleep(0.5) # Chờ nửa giây để tránh bị spam IP
            except Exception as e:
                st.toast(f"Luồng tìm kiếm ngoài bị nghẽn nhẹ: {e}", icon="⚠️")

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
