"""PAGE 4 – PHÂN TÍCH SẢN PHẨM"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.colors import sample_colorscale

from utils import (setup_page, CATEGORY_COLORS, NEG_COLOR, POS_COLOR, SEQ_SCALE, DIV_SCALE, contrast_text,
                   fmt_money, fmt_pct, get_filtered, insight, page_header, round_bars, show_chart)

setup_page("Phân tích sản phẩm")
df, dff, f = get_filtered()
page_header("📦 Phân tích sản phẩm", "Sản phẩm nào mang lại doanh thu cao?", f)
st.caption("Lọc **thời gian** và **khu vực** ở sidebar; chọn số lượng Top N và cấp độ phân tích bên dưới.")

METRIC_VN = {"Sales": "Doanh thu", "Profit": "Lợi nhuận", "Quantity": "Số lượng"}
LEVEL_VN = {"Product Name": "Sản phẩm", "Sub-Category": "Danh mục con"}

# ---------------------------------------------------------------- Top N
c1, c2, c3 = st.columns([2, 1.2, 1.2])
n = c1.slider("Chọn N (số sản phẩm Top)", 5, 30, 10)
level = c2.radio("Cấp độ", list(LEVEL_VN), format_func=LEVEL_VN.get, horizontal=True)
metric = c3.radio("Xếp hạng theo", list(METRIC_VN), format_func=METRIC_VN.get, horizontal=True)

prod = (dff.groupby([level, "Category"])
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"),
             Orders=("Order ID", "nunique"))
        .reset_index())
prod["Margin"] = prod["Profit"] / prod["Sales"]
top = prod.nlargest(n, metric).sort_values(metric)
top["Nhãn"] = top[level].str.slice(0, 45) + top[level].str.len().gt(45).map({True: "…", False: ""})

fig = px.bar(top, x=metric, y="Nhãn", orientation="h", color="Category",
             color_discrete_map=CATEGORY_COLORS,
             custom_data=[level, "Sales", "Profit", "Quantity", "Margin"],
             labels={metric: METRIC_VN[metric], "Nhãn": "", "Category": "Danh mục"},
             title=f"Top {len(top)} {LEVEL_VN[level].lower()} theo {METRIC_VN[metric].lower()}")
fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Doanh thu: $%{customdata[1]:,.0f}"
                                "<br>Lợi nhuận: $%{customdata[2]:,.0f}<br>Số lượng: %{customdata[3]:,}"
                                "<br>Biên LN: %{customdata[4]:.1%}<extra></extra>")
if metric != "Quantity":
    fig.update_xaxes(tickprefix="$", tickformat="~s")
fig.update_layout(yaxis=dict(categoryorder="total ascending"))
show_chart(round_bars(fig), max(420, 30 * len(top)))

total = prod[metric].sum()
share = top[metric].sum() / total if total else 0
lead = top.iloc[-1]
neg = top[top["Profit"] < 0]
cat_mode = top["Category"].value_counts()
txt = (f"Top {len(top)} chiếm **{fmt_pct(share)}** tổng {METRIC_VN[metric].lower()} "
       f"(trên {len(prod):,} {LEVEL_VN[level].lower()}). Dẫn đầu là **{lead[level]}** "
       f"(doanh thu {fmt_money(lead['Sales'])}); danh mục xuất hiện nhiều nhất trong Top là "
       f"**{cat_mode.index[0]}** ({cat_mode.iloc[0]}/{len(top)}).")
if not neg.empty and metric != "Profit":
    txt += (f" ⚠️ {len(neg)} mục trong Top doanh thu lại **thua lỗ** (ví dụ *{neg.iloc[-1][level][:50]}*: "
            f"{fmt_money(neg.iloc[-1]['Profit'])}) – doanh thu cao chưa chắc mang lại lợi nhuận.")
insight(txt)

with st.expander("📋 Xem bảng Top N chi tiết"):
    st.dataframe(top.sort_values(metric, ascending=False).drop(columns="Nhãn"), hide_index=True,
                 width="stretch", column_config={
                     level: LEVEL_VN[level], "Category": "Danh mục",
                     "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
                     "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
                     "Quantity": st.column_config.NumberColumn("Số lượng", format="localized"),
                     "Orders": st.column_config.NumberColumn("Số đơn", format="localized"),
                     "Margin": st.column_config.NumberColumn("Biên LN", format="percent"),
                 })

st.divider()

# ---------------------------------------------------------------- Sub-category profit
st.subheader("💹 Lợi nhuận theo danh mục con")
sub = (dff.groupby(["Sub-Category", "Category"]).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                                                     Discount=("Discount", "mean")).reset_index())
sub["Margin"] = sub["Profit"] / sub["Sales"]
sub = sub.sort_values("Profit")
sub["Kết quả"] = sub["Profit"].map(lambda v: "Lãi" if v >= 0 else "Lỗ")
left, right = st.columns([3, 2], gap="large")
with left:
    fig_sub = px.bar(sub, x="Profit", y="Sub-Category", orientation="h", color="Kết quả",
                     color_discrete_map={"Lãi": POS_COLOR, "Lỗ": NEG_COLOR},
                     custom_data=["Category", "Sales", "Margin", "Discount"],
                     labels={"Profit": "Lợi nhuận ($)", "Sub-Category": ""},
                     title="Lợi nhuận từng danh mục con (đỏ = lỗ)")
    fig_sub.update_traces(hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Lợi nhuận: $%{x:,.0f}"
                                        "<br>Doanh thu: $%{customdata[1]:,.0f}<br>Biên: %{customdata[2]:.1%}"
                                        "<br>Chiết khấu TB: %{customdata[3]:.0%}<extra></extra>")
    fig_sub.update_xaxes(tickprefix="$", tickformat="~s")
    fig_sub.update_layout(yaxis=dict(categoryorder="total ascending"))
    show_chart(round_bars(fig_sub), 480)
with right:
    bins = ["0%", "1–20%", "21–40%", "41–80%"]
    disc = dff.assign(Bin=pd.cut(dff["Discount"], [-0.01, 0, 0.2, 0.4, 0.8], labels=bins))
    disc = disc.groupby("Bin", observed=True).agg(Profit=("Profit", "mean"), N=("Profit", "size")).reset_index()
    # Nhãn dạng "0%" bị Plotly đoán là số -> ép kiểu chuỗi và trục phân loại theo đúng thứ tự
    disc["Bin"] = disc["Bin"].astype(str)
    disc["Kết quả"] = disc["Profit"].map(lambda v: "Lãi" if v >= 0 else "Lỗ")
    fig_d = px.bar(disc, x="Bin", y="Profit", color="Kết quả", text_auto="$.0f",
                   color_discrete_map={"Lãi": POS_COLOR, "Lỗ": NEG_COLOR}, custom_data=["N"],
                   labels={"Bin": "Mức chiết khấu", "Profit": "Lợi nhuận TB / dòng ($)"},
                   title="Chiết khấu cao → lợi nhuận âm")
    fig_d.update_traces(textposition="outside",
                        hovertemplate="Chiết khấu %{x}<br>LN TB: $%{y:,.1f}<br>%{customdata[0]:,} dòng"
                                      "<extra></extra>")
    fig_d.update_xaxes(type="category", categoryorder="array", categoryarray=bins)
    show_chart(round_bars(fig_d), 480)

loss_sub = sub[sub["Profit"] < 0]
best_sub = sub.iloc[-1]
txt = f"**{best_sub['Sub-Category']}** mang lại lợi nhuận lớn nhất ({fmt_money(best_sub['Profit'])})."
if not loss_sub.empty:
    txt += (f" Các danh mục con đang lỗ: **{', '.join(loss_sub['Sub-Category'])}** "
            f"(tổng {fmt_money(loss_sub['Profit'].sum())}), có chiết khấu TB "
            f"{fmt_pct(loss_sub['Discount'].mean(), 0)} so với {fmt_pct(sub['Discount'].mean(), 0)} chung.")
insight(txt)

st.divider()

# ---------------------------------------------------------------- Pivot Category x Region
st.subheader("🧮 Pivot table: Danh mục × Khu vực")
pc1, pc2 = st.columns([1, 2])
val = pc1.radio("Giá trị", ["Sales", "Profit", "Margin"], horizontal=True,
                format_func=lambda x: {"Sales": "Doanh thu", "Profit": "Lợi nhuận", "Margin": "Biên LN"}[x])
row_dim = pc2.radio("Hàng", ["Category", "Sub-Category"], horizontal=True,
                    format_func=lambda x: "Danh mục" if x == "Category" else "Danh mục con")
if val == "Margin":
    ps = dff.pivot_table(index=row_dim, columns="Region", values="Sales", aggfunc="sum")
    pp = dff.pivot_table(index=row_dim, columns="Region", values="Profit", aggfunc="sum")
    pv = pp / ps
else:
    pv = dff.pivot_table(index=row_dim, columns="Region", values=val, aggfunc="sum", fill_value=0)

if val == "Sales":
    scale = SEQ_SCALE
    zmin, zmax = float(np.nanmin(pv.values)), float(np.nanmax(pv.values))
else:  # thang phân kỳ đỏ – xám – xanh, đối xứng quanh 0
    scale = DIV_SCALE
    lim = float(np.nanmax(np.abs(pv.values))) or 1.0
    zmin, zmax = -lim, lim
fig_h = px.imshow(pv, aspect="auto", color_continuous_scale=scale, range_color=(zmin, zmax),
                  labels=dict(x="Khu vực", y="", color={"Sales": "Doanh thu", "Profit": "Lợi nhuận",
                                                         "Margin": "Biên LN"}[val]),
                  title="Heatmap pivot " + ("Danh mục" if row_dim == "Category" else "Danh mục con")
                        + " × Khu vực")
# Nhãn từng ô: màu chữ đen/trắng chọn theo độ sáng của màu ô để luôn đọc được
fmt_cell = (lambda v: fmt_pct(v)) if val == "Margin" else fmt_money
for r_name, row in pv.iterrows():
    for c_name, v in row.items():
        if pd.isna(v):
            continue
        t = 0.5 if zmax == zmin else (v - zmin) / (zmax - zmin)
        fill = sample_colorscale(scale if isinstance(scale[0], list)
                                 else [[i / (len(scale) - 1), c] for i, c in enumerate(scale)],
                                 [min(max(t, 0), 1)], colortype="rgb")[0]
        rgb = [int(float(x)) for x in fill[fill.index("(") + 1:-1].split(",")]
        fig_h.add_annotation(x=c_name, y=r_name, text=fmt_cell(v), showarrow=False,
                             font=dict(color=contrast_text("#%02x%02x%02x" % tuple(rgb)), size=13))
fig_h.update_xaxes(side="top")
show_chart(fig_h, 300 if row_dim == "Category" else 620)

with st.expander("📋 Bảng pivot (có tổng)"):
    if val == "Margin":
        st.dataframe(pv.style.format("{:.1%}"), width="stretch")
    else:
        full = dff.pivot_table(index=row_dim, columns="Region", values=val, aggfunc="sum", fill_value=0,
                               margins=True, margins_name="Tổng")
        st.dataframe(full.style.format("${:,.0f}"), width="stretch")

stacked = pv.stack()
hi, lo = stacked.idxmax(), stacked.idxmin()
fv = (lambda v: fmt_pct(v)) if val == "Margin" else fmt_money
insight(f"Ô cao nhất: **{hi[0]} tại {hi[1]}** ({fv(stacked.max())}); ô thấp nhất: "
        f"**{lo[0]} tại {lo[1]}** ({fv(stacked.min())}). Ưu tiên đẩy mạnh nhóm cao và rà soát giá/chiết khấu "
        f"của nhóm thấp tại đúng khu vực đó.")
