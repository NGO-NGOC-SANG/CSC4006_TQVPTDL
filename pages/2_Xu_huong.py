"""PAGE 2 – XU HƯỚNG DOANH THU THEO THỜI GIAN"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (setup_page, COLOR_MAPS, MEASURE_COLORS, SERIES, fmt_money, fmt_pct, get_filtered, insight,
                   page_header, round_bars, show_chart)

setup_page("Xu hướng thời gian")
df, dff, f = get_filtered()
page_header("📅 Xu hướng doanh thu theo thời gian", "Doanh thu tăng hay giảm theo thời gian?", f)

FREQ = {"Tháng": "MS", "Quý": "QS", "Năm": "YS"}
FMT = {"Tháng": "%m/%Y", "Quý": None, "Năm": "%Y"}

c1, c2, c3 = st.columns([1.2, 1.5, 1])
gran = c1.radio("Độ chi tiết thời gian", list(FREQ), horizontal=True)
measures = c2.multiselect("Chỉ số hiển thị", ["Doanh thu", "Lợi nhuận"],
                          default=["Doanh thu", "Lợi nhuận"])
show_ma = c3.toggle("Đường trung bình động 3 kỳ", value=(gran == "Tháng"))
if not measures:
    st.warning("Hãy chọn ít nhất một chỉ số.")
    st.stop()

ts = (dff.set_index("Order Date")[["Sales", "Profit"]]
      .resample(FREQ[gran]).sum().reset_index())
ts["Label"] = (ts["Order Date"].dt.to_period("Q").astype(str).str.replace("Q", " – Q")
               if gran == "Quý" else ts["Order Date"].dt.strftime(FMT[gran]))

# ---------------------------------------------------------------- Line chart chính
fig = go.Figure()
for name, col in [("Doanh thu", "Sales"), ("Lợi nhuận", "Profit")]:
    if name not in measures:
        continue
    fig.add_trace(go.Scatter(x=ts["Order Date"], y=ts[col], name=name, mode="lines+markers",
                             line=dict(color=MEASURE_COLORS[col], width=2), marker=dict(size=7),
                             customdata=ts["Label"],
                             hovertemplate="%{customdata}<br>" + name + ": $%{y:,.0f}<extra></extra>"))
    if show_ma and len(ts) >= 3:
        fig.add_trace(go.Scatter(x=ts["Order Date"], y=ts[col].rolling(3).mean(),
                                 name=f"{name} – TB động 3 kỳ", mode="lines",
                                 line=dict(color=MEASURE_COLORS[col], width=2, dash="dot"),
                                 opacity=0.7, hovertemplate="TB 3 kỳ: $%{y:,.0f}<extra></extra>"))
fig.update_layout(title=f"{' & '.join(measures)} theo {gran.lower()}", hovermode="x unified")
fig.update_yaxes(tickprefix="$", tickformat="~s", title="USD")
fig.update_xaxes(title="")
show_chart(fig, 430)

peak = ts.loc[ts["Sales"].idxmax()]
low = ts.loc[ts["Sales"].idxmin()]
msg = (f"Doanh thu cao nhất ở kỳ **{peak['Label']}** ({fmt_money(peak['Sales'])}), thấp nhất ở "
       f"**{low['Label']}** ({fmt_money(low['Sales'])}).")
if len(ts) >= 2:
    first, last = ts["Sales"].iloc[0], ts["Sales"].iloc[-1]
    trend = ts["Sales"].reset_index(drop=True)
    slope = pd.Series(range(len(trend))).cov(trend) / pd.Series(range(len(trend))).var()
    msg += (f" Xu hướng chung **{'tăng' if slope > 0 else 'giảm'}** "
            f"(độ dốc ≈ {fmt_money(slope)}/{gran.lower()}); doanh thu biến động mạnh theo mùa nên cần "
            f"so sánh cùng kỳ thay vì kỳ liền kề.")
insight(msg)

st.divider()

# ---------------------------------------------------------------- Năm & mùa vụ
left, right = st.columns(2, gap="large")
with left:
    st.subheader("📊 Tăng trưởng theo năm")
    yr = dff.groupby("Year")[["Sales", "Profit"]].sum()
    yr["Tăng trưởng DT"] = yr["Sales"].pct_change()
    yr["Biên LN"] = yr["Profit"] / yr["Sales"]
    fig_y = px.bar(yr.reset_index(), x="Year", y="Sales", text_auto=".3s",
                   labels={"Year": "Năm", "Sales": "Doanh thu ($)"}, title="Doanh thu theo năm",
                   color_discrete_sequence=[MEASURE_COLORS["Sales"]])
    fig_y.update_traces(textposition="outside", hovertemplate="Năm %{x}<br>$%{y:,.0f}<extra></extra>")
    fig_y.update_xaxes(type="category")
    fig_y.update_yaxes(tickprefix="$", tickformat="~s")
    show_chart(round_bars(fig_y), 360)
    st.dataframe(yr.reset_index(), hide_index=True, width="stretch", column_config={
        "Year": st.column_config.NumberColumn("Năm", format="%d"),
        "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
        "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
        "Tăng trưởng DT": st.column_config.NumberColumn(format="percent"),
        "Biên LN": st.column_config.NumberColumn(format="percent"),
    })
    if len(yr) >= 2:
        g = yr["Tăng trưởng DT"].dropna()
        cagr = (yr["Sales"].iloc[-1] / yr["Sales"].iloc[0]) ** (1 / (len(yr) - 1)) - 1
        insight(f"Doanh thu từ {yr.index[0]} đến {yr.index[-1]} tăng trưởng kép **{fmt_pct(cagr)}/năm**. "
                f"Năm tăng mạnh nhất: **{g.idxmax()}** ({fmt_pct(g.max(), signed=True)}); "
                f"năm yếu nhất: **{g.idxmin()}** ({fmt_pct(g.min(), signed=True)}).")
    else:
        insight("Khoảng thời gian đang chọn chỉ có một năm – hãy mở rộng bộ lọc để so sánh tăng trưởng.")

with right:
    st.subheader("🍂 Tính mùa vụ – so sánh cùng kỳ")
    season = dff.groupby(["Year", "Month Num"])["Sales"].sum().reset_index()
    years = sorted(season["Year"].unique())
    fig_s = go.Figure()
    for i, y in enumerate(years):
        s = season[season["Year"] == y]
        fig_s.add_trace(go.Scatter(x=s["Month Num"], y=s["Sales"], name=str(y), mode="lines+markers",
                                   line=dict(color=SERIES[i % len(SERIES)], width=2),
                                   marker=dict(size=7),
                                   hovertemplate=f"Tháng %{{x}}/{y}: $%{{y:,.0f}}<extra></extra>"))
    fig_s.update_layout(title="Doanh thu theo tháng của từng năm",
                        hovermode="x unified")
    fig_s.update_xaxes(tickmode="array", tickvals=list(range(1, 13)),
                       ticktext=[f"T{m}" for m in range(1, 13)], title="")
    fig_s.update_yaxes(tickprefix="$", tickformat="~s", title="Doanh thu")
    show_chart(fig_s, 360)
    by_m = dff.groupby("Month Num")["Sales"].sum()
    q4 = by_m.loc[by_m.index >= 10].sum() / by_m.sum()
    top3 = by_m.nlargest(3).index.tolist()
    insight(f"Các tháng bán chạy nhất: **{', '.join(f'T{m}' for m in sorted(top3))}**. "
            f"Quý 4 chiếm **{fmt_pct(q4)}** doanh thu – nên chuẩn bị tồn kho và nhân sự từ tháng 9; "
            f"tháng 1–2 là mùa thấp điểm, phù hợp cho khuyến mãi kích cầu.")

st.divider()

# ---------------------------------------------------------------- Theo nhóm
st.subheader("🔍 Xu hướng theo nhóm")
dim = st.segmented_control("Chia theo", ["Category", "Region", "Segment"], default="Category",
                           format_func=lambda x: {"Category": "Danh mục", "Region": "Khu vực",
                                                  "Segment": "Phân khúc"}[x])
dim = dim or "Category"
grp = (dff.groupby([pd.Grouper(key="Order Date", freq="QS"), dim])["Sales"].sum().reset_index())
fig_g = px.line(grp, x="Order Date", y="Sales", color=dim, markers=True,
                color_discrete_map=COLOR_MAPS[dim],
                labels={"Order Date": "", "Sales": "Doanh thu ($)"},
                title="Doanh thu theo quý của từng nhóm")
fig_g.update_traces(line_width=2, marker_size=7,
                    hovertemplate="%{x|%m/%Y}: $%{y:,.0f}")
fig_g.update_yaxes(tickprefix="$", tickformat="~s")
fig_g.update_layout(hovermode="x unified")
show_chart(fig_g, 400)

yrs = sorted(dff["Year"].unique())
if len(yrs) >= 2:
    gy = dff[dff["Year"].isin([yrs[0], yrs[-1]])].pivot_table(index=dim, columns="Year",
                                                             values="Sales", aggfunc="sum")
    gy["g"] = gy[yrs[-1]] / gy[yrs[0]] - 1
    gy = gy.dropna().sort_values("g")
    insight(f"Từ {yrs[0]} đến {yrs[-1]}, nhóm tăng trưởng nhanh nhất là **{gy.index[-1]}** "
            f"({fmt_pct(gy['g'].iloc[-1], signed=True)}), chậm nhất là **{gy.index[0]}** "
            f"({fmt_pct(gy['g'].iloc[0], signed=True)}).")
else:
    insight("Mở rộng khoảng thời gian (≥ 2 năm) để so sánh tăng trưởng giữa các nhóm.")
