"""Dashboard Superstore Sales – trang chủ. Chạy: python -m streamlit run app.py

Các page phân tích nằm trong thư mục pages/. Streamlit tự nhận thư mục này (multipage),
menu tiếng Việt và CSS dùng chung được dựng bởi utils.setup_page().
"""
import streamlit as st

from utils import fmt_int, fmt_money, load_data, setup_page

setup_page("Trang chủ")
df = load_data()
st.title("📊 Dashboard Phân tích Doanh số Superstore")
st.markdown(
    "Hệ thống dashboard giúp **doanh nghiệp bán lẻ Superstore** theo dõi tình hình kinh doanh, "
    "phân tích xu hướng doanh thu, so sánh hiệu quả giữa các khu vực – sản phẩm và hỗ trợ "
    "ra quyết định quản lý."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Số dòng giao dịch", fmt_int(len(df)))
c2.metric("Số cột dữ liệu gốc", "21")
c3.metric("Giai đoạn", f"{df['Order Date'].min():%m/%Y} – {df['Order Date'].max():%m/%Y}")
c4.metric("Tổng doanh thu", fmt_money(df["Sales"].sum()))

st.subheader("🧭 Cấu trúc dashboard")
pages = [
    ("pages/1_Tong_quan.py", "1️⃣ Tổng quan kinh doanh",
     "KPI doanh thu, đơn hàng, sản phẩm, lợi nhuận; bảng tổng hợp theo danh mục & phân khúc."),
    ("pages/2_Xu_huong.py", "2️⃣ Xu hướng theo thời gian",
     "Doanh thu/lợi nhuận theo tháng – quý – năm, tăng trưởng và tính mùa vụ."),
    ("pages/3_Khu_vuc.py", "3️⃣ Phân tích khu vực",
     "So sánh Region và State, bản đồ doanh thu, các bang đang thua lỗ."),
    ("pages/4_San_pham.py", "4️⃣ Phân tích sản phẩm",
     "Top N sản phẩm, danh mục con lãi/lỗ, pivot Danh mục × Khu vực."),
    ("pages/5_Trai_nghiem.py", "5️⃣ Khám phá & trải nghiệm",
     "Hướng dẫn sử dụng, phân phối dữ liệu, biểu đồ nhóm/chồng, tra cứu & tải dữ liệu."),
]
cols = st.columns(5)
for col, (path, label, desc) in zip(cols, pages):
    with col.container(border=True):
        st.page_link(path, label=label)
        st.caption(desc)

st.subheader("🗂️ Mô tả dữ liệu")
st.markdown(
    "- **Nguồn:** [Kaggle – Superstore Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)\n"
    "- **Quy mô:** 9.994 dòng × 21 cột; mỗi dòng là **một sản phẩm trong một đơn hàng** "
    f"({fmt_int(df['Order ID'].nunique())} đơn, {fmt_int(df['Customer ID'].nunique())} khách hàng, "
    f"{fmt_int(df['Product ID'].nunique())} mã sản phẩm, {df['State'].nunique()} bang của Mỹ).\n"
    "- **Chất lượng:** không có giá trị thiếu, không có dòng trùng lặp."
)
with st.expander("Xem ý nghĩa các biến"):
    st.table(
        {
            "Nhóm": ["Đơn hàng", "Khách hàng", "Địa lý", "Sản phẩm", "Chỉ số"],
            "Biến": ["Row ID, Order ID, Order Date, Ship Date, Ship Mode",
                     "Customer ID, Customer Name, Segment",
                     "Country, City, State, Postal Code, Region",
                     "Product ID, Category, Sub-Category, Product Name",
                     "Sales, Quantity, Discount, Profit"],
            "Kiểu": ["Định danh / Thời gian / Phân loại", "Định danh / Phân loại",
                     "Phân loại", "Định danh / Phân loại", "Số (liên tục / rời rạc)"],
            "Ý nghĩa": ["Mã dòng, mã đơn, ngày đặt, ngày giao, hình thức giao",
                        "Mã, tên khách hàng; phân khúc Consumer/Corporate/Home Office",
                        "Quốc gia (US), thành phố, bang, mã bưu chính, 4 vùng",
                        "Mã, 3 danh mục, 17 danh mục con, tên sản phẩm",
                        "Doanh thu ($), số lượng, tỷ lệ chiết khấu (0–0.8), lợi nhuận ($)"],
        }
    )
st.info("👈 Chọn trang ở thanh bên trái. Bộ lọc (thời gian, khu vực, danh mục, phân khúc) "
        "xuất hiện ở sidebar của mỗi trang và được giữ nguyên khi chuyển trang.")
