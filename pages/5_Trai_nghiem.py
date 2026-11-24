"""PAGE 5 – TƯƠNG TÁC & TRẢI NGHIỆM NGƯỜI DÙNG"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (setup_page, COLOR_MAPS, VN, fmt_int, fmt_money, fmt_pct, get_filtered, insight, page_header, surface,
                   round_bars, show_chart)

setup_page("Khám phá & trải nghiệm")
df, dff, f = get_filtered(advanced=True)
page_header("🧩 Khám phá & trải nghiệm người dùng",
            "Dashboard phải dễ dùng cho người không chuyên.", f)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Số dòng sau lọc", fmt_int(len(dff)), f"{fmt_pct(len(dff) / len(df))} dữ liệu",
          delta_color="off")
k2.metric("Doanh thu", fmt_money(dff["Sales"].sum()))
k3.metric("Lợi nhuận", fmt_money(dff["Profit"].sum()))
k4.metric("Số đơn hàng", fmt_int(dff["Order ID"].nunique()))

DIMS = {"Category": "Danh mục", "Region": "Khu vực", "Segment": "Phân khúc", "Ship Mode": "Hình thức giao"}
NUMS = {"Sales": "Doanh thu ($)", "Profit": "Lợi nhuận ($)", "Quantity": "Số lượng",
        "Discount": "Chiết khấu", "Ship Days": "Số ngày giao hàng"}

tab_help, tab_dist, tab_group, tab_data = st.tabs(
    ["📖 Hướng dẫn sử dụng", "📊 Phân phối dữ liệu", "🧱 So sánh nhóm (grouped/stacked)", "🔎 Tra cứu dữ liệu"])

# ============================================================ TAB 1 – Hướng dẫn
with tab_help:
    st.markdown("### 3 bước để dùng dashboard")
    s1, s2, s3 = st.columns(3)
    with s1.container(border=True):
        st.markdown("**① Chọn bộ lọc**  \nỞ **thanh bên trái**: khoảng thời gian, khu vực, danh mục, "
                    "phân khúc. Mở *Bộ lọc nâng cao* để chọn hình thức giao và danh mục con.")
    with s2.container(border=True):
        st.markdown("**② Chọn trang**  \nMỗi trang trả lời một câu hỏi: tổng quan, xu hướng, khu vực, "
                    "sản phẩm, khám phá. Bộ lọc được **giữ nguyên** khi chuyển trang.")
    with s3.container(border=True):
        st.markdown("**③ Tương tác với biểu đồ**  \nRê chuột để xem số liệu chi tiết, kéo để phóng to, "
                    "nhấp đúp để về mặc định, bấm vào chú thích để ẩn/hiện một nhóm.")

    with st.expander("📚 Giải thích các chỉ số", expanded=True):
        st.markdown(
            "| Chỉ số | Ý nghĩa |\n|---|---|\n"
            "| **Doanh thu (Sales)** | Số tiền bán hàng (USD) sau chiết khấu |\n"
            "| **Lợi nhuận (Profit)** | Doanh thu trừ chi phí; số âm = thua lỗ |\n"
            "| **Biên lợi nhuận** | Lợi nhuận ÷ Doanh thu – mỗi 100$ bán ra giữ lại bao nhiêu |\n"
            "| **Chiết khấu (Discount)** | Tỷ lệ giảm giá trên dòng hàng (0 – 80%) |\n"
            "| **Số đơn hàng** | Số mã đơn (Order ID) khác nhau – một đơn có thể gồm nhiều sản phẩm |\n"
            "| **Giá trị TB/đơn** | Doanh thu ÷ Số đơn hàng |"
        )
    with st.expander("❓ Câu hỏi thường gặp"):
        st.markdown(
            "- **Biểu đồ trống / có cảnh báo?** Bạn đã bỏ hết lựa chọn của một bộ lọc – hãy chọn lại "
            "hoặc bấm **↺ Đặt lại bộ lọc**.\n"
            "- **Mũi tên xanh/đỏ dưới KPI là gì?** Mức thay đổi so với kỳ trước có cùng độ dài.\n"
            "- **Tải dữ liệu ở đâu?** Tab *Tra cứu dữ liệu* có nút tải CSV theo bộ lọc hiện tại.\n"
            "- **Vì sao chạy nhanh?** Dữ liệu được đọc một lần và lưu cache (`@st.cache_data`)."
        )
    with st.expander("🧾 Bộ lọc đang áp dụng"):
        st.json({
            "Thời gian": f"{f.start:%d/%m/%Y} – {f.end:%d/%m/%Y}",
            "Khu vực": f.regions, "Danh mục": f.categories, "Phân khúc": f.segments,
            "Hình thức giao": f.ship_modes, "Danh mục con": f.sub_categories,
        })

# ============================================================ TAB 2 – Phân phối
with tab_dist:
    c1, c2, c3 = st.columns([1.3, 1.3, 1])
    var = c1.selectbox("Biến số cần xem phân phối", list(NUMS), format_func=NUMS.get)
    by = c2.selectbox("Tách theo nhóm", list(DIMS), format_func=DIMS.get)
    log_y = c3.toggle("Trục Y dạng log", value=var in ("Sales", "Profit"),
                      help="Hữu ích khi dữ liệu lệch phải mạnh (vài giá trị rất lớn).")

    left, right = st.columns(2, gap="large")
    with left:
        fig_h = px.histogram(dff, x=var, nbins=60 if var in ("Sales", "Profit") else 20,
                             labels={var: NUMS[var]}, log_y=log_y,
                             title=f"Histogram: phân phối {NUMS[var].lower()}",
                             color_discrete_sequence=["#2a78d6"])
        # Tách cột bằng khoảng hở (không dùng viền) để đúng ở mọi theme
        fig_h.update_traces(marker_line_width=0,
                            hovertemplate="Khoảng %{x}<br>%{y:,} dòng<extra></extra>")
        fig_h.update_layout(bargap=0.08)
        fig_h.update_yaxes(title="Số dòng")
        med = dff[var].median()
        fig_h.add_vline(x=med, line_dash="dash", line_color="rgba(128,128,128,0.9)",
                        annotation_text=f"Trung vị {med:,.2f}", annotation_position="top right")
        show_chart(fig_h, 420)
    with right:
        fig_b = px.box(dff, x=by, y=var, color=by, color_discrete_map=COLOR_MAPS[by], log_y=False,
                       points="outliers", labels={var: NUMS[var], by: DIMS[by]},
                       title=f"Boxplot: {NUMS[var].lower()} theo {DIMS[by].lower()}")
        fig_b.update_layout(showlegend=False)
        if log_y and (dff[var] > 0).all():
            fig_b.update_yaxes(type="log")
        show_chart(fig_b, 420)

    s = dff[var]
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    out = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
    skew = s.skew()
    meds = dff.groupby(by)[var].median().sort_values()
    insight(f"Trung bình **{s.mean():,.2f}** so với trung vị **{s.median():,.2f}** (độ lệch {skew:.2f}"
            f"{' – lệch phải: số ít giao dịch rất lớn kéo trung bình lên' if skew > 1 else ''}). "
            f"Theo quy tắc IQR có **{fmt_int(out)} giá trị ngoại lệ** ({fmt_pct(out / len(s))}). "
            f"Nhóm có trung vị cao nhất: **{meds.index[-1]}** ({meds.iloc[-1]:,.2f}), thấp nhất: "
            f"**{meds.index[0]}** ({meds.iloc[0]:,.2f}).")

    with st.expander("📐 Thống kê mô tả theo nhóm"):
        desc = dff.groupby(by)[var].describe()
        desc.columns = ["Số dòng", "Trung bình", "Độ lệch chuẩn", "Min", "Q1", "Trung vị", "Q3", "Max"]
        st.dataframe(desc.style.format("{:,.2f}"), width="stretch")

# ============================================================ TAB 3 – Grouped / stacked
with tab_group:
    c1, c2, c3, c4 = st.columns(4)
    x_dim = c1.selectbox("Trục X", ["Year", "Region", "Category", "Segment", "Ship Mode"],
                         format_func=lambda x: "Năm" if x == "Year" else DIMS[x])
    color_opts = [d for d in DIMS if d != x_dim]
    c_dim = c2.selectbox("Màu (nhóm con)", color_opts, format_func=DIMS.get)
    meas = c3.selectbox("Chỉ số", ["Sales", "Profit", "Quantity", "Orders"],
                        format_func=lambda x: {"Sales": "Doanh thu", "Profit": "Lợi nhuận",
                                               "Quantity": "Số lượng", "Orders": "Số đơn hàng"}[x])
    mode = c4.radio("Kiểu biểu đồ", ["group", "stack", "percent"], horizontal=False,
                    format_func=lambda x: {"group": "Nhóm (grouped)", "stack": "Chồng (stacked)",
                                           "percent": "Chồng 100%"}[x])
    if meas == "Orders":
        agg = dff.groupby([x_dim, c_dim])["Order ID"].nunique().rename("Orders").reset_index()
    else:
        agg = dff.groupby([x_dim, c_dim])[meas].sum().reset_index()
    if mode == "percent":
        agg["Share"] = agg[meas] / agg.groupby(x_dim)[meas].transform("sum")
        ycol, ylab = "Share", "Tỷ trọng"
    else:
        ycol, ylab = meas, {"Sales": "Doanh thu ($)", "Profit": "Lợi nhuận ($)", "Quantity": "Số lượng",
                            "Orders": "Số đơn hàng"}[meas]
    if x_dim == "Year":
        agg["Year"] = agg["Year"].astype(str)
    fig_g = px.bar(agg, x=x_dim, y=ycol, color=c_dim, color_discrete_map=COLOR_MAPS[c_dim],
                   barmode="group" if mode == "group" else "relative",
                   labels={x_dim: "Năm" if x_dim == "Year" else DIMS[x_dim], ycol: ylab, c_dim: DIMS[c_dim]},
                   title=f"{ylab} theo {('năm' if x_dim == 'Year' else DIMS[x_dim].lower())}, "
                         f"chia theo {DIMS[c_dim].lower()}")
    if mode == "percent":
        fig_g.update_yaxes(tickformat=".0%", range=[0, 1])
        fig_g.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:.1%}<extra></extra>")
    elif meas in ("Sales", "Profit"):
        fig_g.update_yaxes(tickprefix="$", tickformat="~s")
        fig_g.update_traces(hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}<extra></extra>")
    if mode != "group":
        fig_g.update_traces(marker_line_color=surface(), marker_line_width=2)
    fig_g.update_xaxes(type="category")  # năm "2014"... không bị hiểu thành số/ngày
    show_chart(round_bars(fig_g) if mode == "group" else fig_g, 460)

    piv = agg.pivot_table(index=x_dim, columns=c_dim, values=meas, aggfunc="sum", fill_value=0)
    shares = piv.div(piv.sum(axis=1), axis=0)
    dom = shares.mean().idxmax()
    spread = shares[dom].max() - shares[dom].min()
    best_x = piv.sum(axis=1).idxmax()
    insight(f"**{dom}** chiếm tỷ trọng lớn nhất ở hầu hết các nhóm (trung bình {fmt_pct(shares[dom].mean())}, "
            f"dao động {fmt_pct(spread)} giữa các nhóm X). Nhóm X có tổng cao nhất: **{best_x}**. "
            f"{'Cơ cấu khá ổn định giữa các nhóm.' if spread < 0.1 else 'Cơ cấu khác biệt rõ – nên tách chiến lược theo nhóm.'}")

    st.markdown("#### Biểu đồ chồng: lợi nhuận theo hình thức giao & phân khúc")
    sm = dff.groupby(["Ship Mode", "Segment"]).agg(Sales=("Sales", "sum"), Days=("Ship Days", "mean")).reset_index()
    fig_sm = px.bar(sm, x="Sales", y="Ship Mode", color="Segment", orientation="h",
                    color_discrete_map=COLOR_MAPS["Segment"],
                    labels={"Sales": "Doanh thu ($)", "Ship Mode": "", "Segment": "Phân khúc"},
                    title="Doanh thu theo hình thức giao hàng (chồng theo phân khúc)")
    fig_sm.update_traces(marker_line_color=surface(), marker_line_width=2,
                         hovertemplate="%{y}<br>%{fullData.name}: $%{x:,.0f}<extra></extra>")
    fig_sm.update_xaxes(tickprefix="$", tickformat="~s")
    fig_sm.update_layout(barmode="stack", yaxis=dict(categoryorder="total ascending"))
    show_chart(fig_sm, 340)
    ship = dff.groupby("Ship Mode").agg(Sales=("Sales", "sum"), Days=("Ship Days", "mean"))
    ship["Share"] = ship["Sales"] / ship["Sales"].sum()
    top_ship = ship["Share"].idxmax()
    fast = ship["Days"].idxmin()
    insight(f"**{top_ship}** chiếm {fmt_pct(ship.loc[top_ship, 'Share'])} doanh thu với thời gian giao TB "
            f"{ship.loc[top_ship, 'Days']:.1f} ngày; **{fast}** nhanh nhất ({ship.loc[fast, 'Days']:.1f} ngày) "
            f"nhưng chỉ chiếm {fmt_pct(ship.loc[fast, 'Share'])} – có thể khai thác như dịch vụ cao cấp.")

# ============================================================ TAB 4 – Tra cứu
with tab_data:
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("🔍 Tìm theo tên sản phẩm, khách hàng, thành phố hoặc mã đơn",
                      placeholder="ví dụ: Canon, Los Angeles, CA-2017-...")
    only_loss = c2.toggle("Chỉ hiện dòng thua lỗ", value=False)
    view = dff
    if q:
        ql = q.lower()
        m = np.zeros(len(view), dtype=bool)
        for col in ["Product Name", "Customer Name", "City", "Order ID", "State"]:
            m |= view[col].str.lower().str.contains(ql, regex=False).to_numpy()
        view = view[m]
    if only_loss:
        view = view[view["Profit"] < 0]
    cols = ["Order ID", "Order Date", "Customer Name", "Segment", "City", "State", "Region",
            "Category", "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit"]
    # Escape "$" để Streamlit không hiểu đoạn giữa hai dấu $ là công thức LaTeX
    st.caption((f"Hiển thị **{fmt_int(len(view))}** dòng · doanh thu {fmt_money(view['Sales'].sum())} · "
                f"lợi nhuận {fmt_money(view['Profit'].sum())}").replace("$", "\\$"))
    st.dataframe(view[cols].sort_values("Order Date", ascending=False), hide_index=True, width="stretch",
                 height=420, column_config={
                     "Order Date": st.column_config.DateColumn("Ngày đặt", format="DD/MM/YYYY"),
                     "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
                     "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
                     "Discount": st.column_config.NumberColumn("Chiết khấu", format="percent"),
                 })
    st.download_button("⬇️ Tải dữ liệu đã lọc (CSV)", view[cols].to_csv(index=False).encode("utf-8-sig"),
                       file_name="superstore_filtered.csv", mime="text/csv")
    if len(view):
        insight(f"Trong {fmt_int(len(view))} dòng đang hiển thị, **{fmt_pct((view['Profit'] < 0).mean())}** "
                f"là giao dịch thua lỗ; chiết khấu TB của nhóm lỗ là "
                f"{fmt_pct(view.loc[view['Profit'] < 0, 'Discount'].mean() if (view['Profit'] < 0).any() else 0)}.")
