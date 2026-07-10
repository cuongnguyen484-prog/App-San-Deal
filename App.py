import streamlit as st
from duckduckgo_search import DDGS
import pandas as pd
import re

st.set_page_config(page_title="Trợ Lý Săn Deal Vạn Năng", page_icon="🛍️", layout="wide")

st.title("🛍️ Hệ Thống Quét Deal Đa Nền Tảng (Không Cần Cấu Hình)")
st.write("Sử dụng vệ tinh tìm kiếm toàn cầu để bóc tách giá từ mọi website (Shopee, Lazada, Tiki, v.v.)")

# Ô nhập liệu
ten_sp = st.text_input("Nhập tên sản phẩm (Ví dụ: Galaxy S25 Ultra, iPhone 16):")

# Hàm tự động nhận diện và bóc tách giá tiền từ văn bản lộn xộn
def tim_gia_trong_van_ban(text):
    # Tìm các mẫu chữ số giống tiền tệ Việt Nam (VD: 25.000.000 đ, 25,000,000₫)
    mau_gia = r'(\d{1,3}(?:[.,]\d{3})+(?:\s?[đ₫]|(?:\s?VND|VNĐ)))'
    ket_qua = re.findall(mau_gia, text, re.IGNORECASE)
    if ket_qua:
        return ket_qua[0] # Lấy mức giá đầu tiên tìm thấy
    return "Bấm link để xem giá"

if st.button("🚀 Quét Toàn Bộ Internet"):
    if not ten_sp.strip():
        st.error("⚠️ Vui lòng gõ tên sản phẩm!")
    else:
        with st.spinner(f"🔄 Đang thả bot lùng sục '{ten_sp}' trên toàn mạng lưới..."):
            ket_qua_tong_hop = []
            
            try:
                # Gọi vệ tinh DuckDuckGo (Không cần API key, không bị chặn)
                ddgs = DDGS()
                
                # Cú pháp tìm kiếm ép kết quả trả về từ các trang TMĐT lớn tại VN
                truy_van = f"{ten_sp} site:shopee.vn OR site:lazada.vn OR site:tiki.vn OR site:hoanghamobile.com OR site:cellphones.com.vn"
                
                # Lấy 20 kết quả hàng đầu
                ket_qua_tim_kiem = ddgs.text(truy_van, region='vn-vi', max_results=20)
                
                for item in ket_qua_tim_kiem:
                    # Tự động trích xuất tên miền để xem deal từ nguồn nào
                    nguon = item['href'].split('/')[2].replace("www.", "")
                    
                    # Trích xuất giá từ mô tả của kết quả tìm kiếm
                    gia_tim_thay = tim_gia_trong_van_ban(item['body'] + " " + item['title'])
                    
                    ket_qua_tong_hop.append({
                        "Nguồn website": nguon,
                        "Tiêu đề/Sản phẩm": item['title'][:70] + "...", # Cắt ngắn cho gọn
                        "Giá trích xuất": gia_tim_thay,
                        "Đường link sản phẩm": item['href']
                    })
                    
            except Exception as e:
                st.error(f"Máy chủ tìm kiếm đang bận, vui lòng thử lại sau. Lỗi: {e}")

            # Hiển thị kết quả
            if ket_qua_tong_hop:
                df = pd.DataFrame(ket_qua_tong_hop)
                st.success(f"🎉 Đã quét xong! Phân tích tự động được {len(df)} nguồn bán tiềm năng.")
                
                st.dataframe(
                    df,
                    column_config={
                        "Đường link sản phẩm": st.column_config.LinkColumn("Bấm để xem/mua ngay")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("😭 Không quét được deal nào. Hãy thử lại với từ khóa khác.")
