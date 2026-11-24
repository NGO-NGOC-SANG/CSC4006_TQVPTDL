"""PAGE 1 – TỔNG QUAN KINH DOANH"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (setup_page, CATEGORY_COLORS, MEASURE_COLORS, SEGMENT_COLORS, apply_filters, fmt_int,
                   fmt_money, fmt_pct, get_filtered, insight, page_header, round_bars, show_chart)

setup_page("Tổng quan kinh doanh")
df, dff, f = get_filtered()
page_header("📈 Tổng quan kinh doanh", "Tôi muốn nhìn nhanh tình hình kinh doanh tổng thể.", f)


# ---------------------------------------------------------------- KPI
def kpis(d: pd.DataFrame) -> dict:
    sales, profit, orders = d["Sales"].sum(), d["Profit"].sum(), d["Order ID"].nunique()
    return {
        "sales": sales, "orders": orders, "products": d["Product ID"].nunique(), "profit": profit,
        "margin": profit / sales if sales else 0, "customers": d["Customer ID"].nunique(),
        "aov": sales / orders if orders else 0, "qty": d["Quantity"].sum(),
    }


cur = kpis(dff)
# Kỳ trước có cùng độ dài (để tính delta), giữ nguyên các bộ lọc khác
start, end = pd.Timestamp(f.start), pd.Timestamp(f.end)
span = end - start + pd.Timedelta(days=1)
prev_start, prev_end = start - span, start - pd.Timedelta(days=1)
base = apply_filters(df, f, ignore_date=True)
prev_df = base[base["Order Date"].between(prev_start, prev_end)]
has_prev = prev_start >= df["Order Date"].min() and not prev_df.empty
prev = kpis(prev_df) if has_prev else None


def delta(key: str, pct: bool = True):
    if prev is None or prev[key] == 0:
        return None
    if key == "margin":
        return f"{(cur[key] - prev[key]) * 100:+.1f} điểm %"
    return fmt_pct(cur[key] / prev[key] - 1, signed=True)


st.subheader("Chỉ số chính (KPI)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Tổng doanh thu", fmt_money(cur["sales"]), delta("sales"),
          help="Tổng cột Sales trong khoảng lọc")
c2.metric("🧾 Số đơn hàng", fmt_int(cur["orders"]), delta("orders"),
          help="Số Order ID khác nhau")
c3.metric("📦 Số sản phẩm đã bán", fmt_int(cur["products"]), delta("products"),
          help="Số Product ID khác nhau xuất hiện trong các đơn")
c4.metric("📈 Tổng lợi nhuận", fmt_money(cur["profit"]), delta("profit"))
c5, c6, c7, c8 = st.columns(4)
c5.metric("Biên lợi nhuận", fmt_pct(cur["margin"]), delta("margin"))
c6.metric("Số khách hàng", fmt_int(cur["customers"]), delta("customers"))
c7.metric("Giá trị TB / đơn", fmt_money(cur["aov"]), delta("aov"))
c8.metric("Số lượng bán", fmt_int(cur["qty"]), delta("qty"))
if has_prev:
    st.caption(f"Mũi tên ▲▼ so sánh với kỳ trước cùng độ dài: "
               f"{prev_start:%d/%m/%Y} – {prev_end:%d/%m/%Y}.")
else:
    st.caption("Không có kỳ trước cùng độ dài trong dữ liệu nên không hiển thị mức thay đổi.")

msg = (f"Trong giai đoạn đang xem, cửa hàng thu về **{fmt_money(cur['sales'])}** từ "
       f"**{fmt_int(cur['orders'])} đơn hàng**, lãi **{fmt_money(cur['profit'])}** "
       f"(biên {fmt_pct(cur['margin'])}), trung bình mỗi đơn **{fmt_money(cur['aov'])}**.")
if has_prev:
    g = cur["sales"] / prev["sales"] - 1
    msg += f" Doanh thu {'tăng' if g >= 0 else 'giảm'} **{fmt_pct(abs(g))}** so với kỳ trước."
insight(msg)

st.divider()


# ---------------------------------------------------------------- GROUPBY
def summarize(d: pd.DataFrame, by: str) -> pd.DataFrame:
    t = (d.groupby(by)
         .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"),
              Quantity=("Quantity", "sum"))
         .sort_values("Sales", ascending=False))
    t["Margin"] = t["Profit"] / t["Sales"]
    t["Share"] = t["Sales"] / t["Sales"].sum()
    return t.reset_index()


col_cfg = {
    "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
    "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
    "Orders": st.column_config.NumberColumn("Số đơn", format="localized"),
    "Quantity": st.column_config.NumberColumn("Số lượng", format="localized"),
    "Margin": st.column_config.NumberColumn("Biên LN", format="percent"),
    "Share": st.column_config.ProgressColumn("Tỷ trọng DT", format="percent", min_value=0,
                                             max_value=1),
}


def bar_sales_profit(t: pd.DataFrame, by: str, title: str):
    long = t.melt(id_vars=by, value_vars=["Sales", "Profit"], var_name="Chỉ số", value_name="Giá trị")
    long["Chỉ số"] = long["Chỉ số"].map({"Sales": "Doanh thu", "Profit": "Lợi nhuận"})
    fig = px.bar(long, x=by, y="Giá trị", color="Chỉ số", barmode="group", title=title,
                 color_discrete_map={"Doanh thu": MEASURE_COLORS["Sales"],
                                     "Lợi nhuận": MEASURE_COLORS["Profit"]},
                 labels={by: "", "Giá trị": "USD"}, text_auto=".3s")
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return round_bars(fig)


left, right = st.columns(2, gap="large")

with left:
    st.subheader("📦 Theo danh mục sản phẩm")
    cat = summarize(dff, "Category")
    st.dataframe(cat, hide_index=True, width="stretch",
                 column_config={"Category": "Danh mục", **col_cfg})
    show_chart(bar_sales_profit(cat, "Category", "Doanh thu & lợi nhuận theo danh mục"), 380)
    best = cat.loc[cat["Margin"].idxmax()]
    worst = cat.loc[cat["Margin"].idxmin()]
    insight(f"**{cat.iloc[0]['Category']}** dẫn đầu doanh thu ({fmt_pct(cat.iloc[0]['Share'])} tổng). "
            f"**{best['Category']}** sinh lời tốt nhất (biên {fmt_pct(best['Margin'])}), trong khi "
            f"**{worst['Category']}** chỉ đạt biên {fmt_pct(worst['Margin'])} dù doanh thu "
            f"{fmt_money(worst['Sales'])} – cần xem lại chính sách giá/chiết khấu.")

with right:
    st.subheader("👥 Theo phân khúc khách hàng")
    seg = summarize(dff, "Segment")
    st.dataframe(seg, hide_index=True, width="stretch",
                 column_config={"Segment": "Phân khúc", **col_cfg})
    show_chart(bar_sales_profit(seg, "Segment", "Doanh thu & lợi nhuận theo phân khúc"), 380)
    bests = seg.loc[seg["Margin"].idxmax()]
    insight(f"Khách **{seg.iloc[0]['Segment']}** đóng góp nhiều nhất ({fmt_pct(seg.iloc[0]['Share'])} "
            f"doanh thu). Phân khúc **{bests['Segment']}** có biên lợi nhuận cao nhất "
            f"({fmt_pct(bests['Margin'])}) – tiềm năng để mở rộng.")

st.divider()

# ---------------------------------------------------------------- Category x Segment
st.subheader("🔀 Ma trận Danh mục × Phân khúc")
mtx = dff.pivot_table(index="Category", columns="Segment", values="Sales", aggfunc="sum",
                      fill_value=0, margins=True, margins_name="Tổng")
mtx_p = dff.pivot_table(index="Category", columns="Segment", values="Profit", aggfunc="sum",
                        fill_value=0, margins=True, margins_name="Tổng")
mc1, mc2 = st.columns(2)
with mc1:
    st.caption("Doanh thu ($)")
    st.dataframe(mtx.style.format("${:,.0f}").background_gradient(cmap="Blues", axis=None,
                 subset=pd.IndexSlice[mtx.index[:-1], mtx.columns[:-1]]), width="stretch")
with mc2:
    st.caption("Lợi nhuận ($)")
    st.dataframe(mtx_p.style.format("${:,.0f}"), width="stretch")
inner = mtx.iloc[:-1, :-1].stack()
top_cell = inner.idxmax()
inner_p = mtx_p.iloc[:-1, :-1].stack()
low_cell = inner_p.idxmin()
insight(f"Cặp lớn nhất là **{top_cell[0]} × {top_cell[1]}** ({fmt_money(inner.max())}); cặp lãi thấp "
        f"nhất là **{low_cell[0]} × {low_cell[1]}** ({fmt_money(inner_p.min())}).")
