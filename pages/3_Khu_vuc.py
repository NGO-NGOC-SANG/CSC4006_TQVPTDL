"""PAGE 3 – PHÂN TÍCH THEO KHU VỰC"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (setup_page, DIV_SCALE, MEASURE_COLORS, NEG_COLOR, POS_COLOR, REGION_COLORS, SEQ_SCALE,
                   STATE_CODES, fmt_money, fmt_pct, get_filtered, insight, page_header, round_bars,
                   show_chart)

setup_page("Phân tích khu vực")
df, dff, f = get_filtered()
page_header("🗺️ Phân tích theo khu vực", "Khu vực nào đang hoạt động tốt nhất?", f)

# ---------------------------------------------------------------- Chọn khu vực (riêng page 3)
region_opts = [r for r in REGION_COLORS if r in set(dff["Region"])]
sel_regions = st.multiselect(
    "🗺️ Chọn khu vực cần so sánh", region_opts, default=region_opts,
    help="Lọc thêm trên dữ liệu đã qua bộ lọc sidebar. Danh sách chỉ gồm các khu vực đang được "
         "chọn ở sidebar.")
if not sel_regions:
    st.warning("⚠️ Hãy chọn ít nhất một khu vực để so sánh.")
    st.stop()
dff = dff[dff["Region"].isin(sel_regions)]

# ---------------------------------------------------------------- Groupby Region
reg = (dff.groupby("Region")
       .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"),
            Customers=("Customer ID", "nunique"))
       .sort_values("Sales", ascending=False))
reg["Margin"] = reg["Profit"] / reg["Sales"]
reg["Share"] = reg["Sales"] / reg["Sales"].sum()
reg["AOV"] = reg["Sales"] / reg["Orders"]

cols = st.columns(len(reg))
for col, (name, r) in zip(cols, reg.iterrows()):
    col.metric(f"{name}", fmt_money(r["Sales"]), f"Biên LN {fmt_pct(r['Margin'])}",
               delta_color="normal" if r["Profit"] >= 0 else "inverse",
               help=f"Lợi nhuận {fmt_money(r['Profit'])} · {r['Orders']:,} đơn")

left, right = st.columns([3, 2], gap="large")
with left:
    long = reg.reset_index().melt(id_vars="Region", value_vars=["Sales", "Profit"],
                                  var_name="Chỉ số", value_name="USD")
    long["Chỉ số"] = long["Chỉ số"].map({"Sales": "Doanh thu", "Profit": "Lợi nhuận"})
    fig = px.bar(long, x="Region", y="USD", color="Chỉ số", barmode="group", text_auto=".3s",
                 color_discrete_map={"Doanh thu": MEASURE_COLORS["Sales"],
                                     "Lợi nhuận": MEASURE_COLORS["Profit"]},
                 labels={"Region": ""}, title="Doanh thu & lợi nhuận theo khu vực")
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>%{fullData.name}: $%{y:,.0f}")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    show_chart(round_bars(fig), 420)
with right:
    m = reg.reset_index().sort_values("Margin")
    fig_m = px.bar(m, x="Margin", y="Region", orientation="h", color="Region",
                   color_discrete_map=REGION_COLORS, text=m["Margin"].map(lambda v: fmt_pct(v)),
                   labels={"Margin": "Biên lợi nhuận", "Region": ""},
                   title="Biên lợi nhuận theo khu vực")
    fig_m.update_traces(textposition="outside", hovertemplate="%{y}: %{x:.1%}<extra></extra>")
    # Chừa khoảng trống hai đầu trục để nhãn % nằm ngoài cột không bị cắt
    lo, hi = min(0.0, m["Margin"].min()), max(0.0, m["Margin"].max())
    pad = max(hi - lo, 0.01) * 0.25
    fig_m.update_xaxes(tickformat=".0%", range=[lo - (pad if lo < 0 else 0), hi + pad])
    fig_m.update_layout(showlegend=False, margin=dict(r=30))
    show_chart(round_bars(fig_m), 420)

top = reg.iloc[0]
best_m = reg["Margin"].idxmax()
worst_m = reg["Margin"].idxmin()
txt = (f"**{reg.index[0]}** là khu vực nổi bật nhất với doanh thu {fmt_money(top['Sales'])} "
       f"({fmt_pct(top['Share'])} tổng) và lợi nhuận {fmt_money(top['Profit'])}.")
if len(reg) > 1:
    txt += (f" Biên lợi nhuận cao nhất thuộc về **{best_m}** ({fmt_pct(reg.loc[best_m, 'Margin'])}), "
            f"thấp nhất là **{worst_m}** ({fmt_pct(reg.loc[worst_m, 'Margin'])}) – "
            f"bán được hàng nhưng giữ lại ít lợi nhuận.")
insight(txt)

with st.expander("📋 Bảng tổng hợp theo khu vực (groupby)"):
    st.dataframe(reg.reset_index(), hide_index=True, width="stretch", column_config={
        "Region": "Khu vực",
        "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
        "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
        "Orders": st.column_config.NumberColumn("Số đơn", format="localized"),
        "Customers": st.column_config.NumberColumn("Số khách", format="localized"),
        "Margin": st.column_config.NumberColumn("Biên LN", format="percent"),
        "Share": st.column_config.ProgressColumn("Tỷ trọng DT", format="percent", min_value=0, max_value=1),
        "AOV": st.column_config.NumberColumn("Giá trị TB/đơn", format="dollar"),
    })

st.divider()

# ---------------------------------------------------------------- State level
st.subheader("🏙️ Chi tiết theo bang (State)")
st_df = (dff.groupby(["State", "Region"]).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
         .reset_index())
st_df["Margin"] = st_df["Profit"] / st_df["Sales"]
st_df["Code"] = st_df["State"].map(STATE_CODES)

c1, c2 = st.columns([1, 2])
metric = c1.radio("Chỉ số", ["Sales", "Profit"], horizontal=True,
                  format_func=lambda x: "Doanh thu" if x == "Sales" else "Lợi nhuận")
if len(st_df) > 5:
    n = c2.slider("Số bang hiển thị", 5, min(30, len(st_df)), min(15, len(st_df)))
else:
    n = len(st_df)

left, right = st.columns(2, gap="large")
with left:
    top_st = st_df.nlargest(n, metric).sort_values(metric)
    if metric == "Sales":
        fig_s = px.bar(top_st, x="Sales", y="State", orientation="h", color="Region",
                       color_discrete_map=REGION_COLORS, title=f"Top {n} bang theo doanh thu",
                       labels={"Sales": "Doanh thu ($)", "State": ""}, custom_data=["Profit"])
        fig_s.update_traces(hovertemplate="%{y}<br>Doanh thu: $%{x:,.0f}<br>"
                                          "Lợi nhuận: $%{customdata[0]:,.0f}<extra></extra>")
    else:
        top_st = pd.concat([st_df.nlargest(n // 2 + n % 2, "Profit"),
                            st_df.nsmallest(n // 2, "Profit")]).drop_duplicates("State")
        top_st = top_st.sort_values("Profit")
        top_st["Kết quả"] = top_st["Profit"].map(lambda v: "Lãi" if v >= 0 else "Lỗ")
        fig_s = px.bar(top_st, x="Profit", y="State", orientation="h", color="Kết quả",
                       color_discrete_map={"Lãi": POS_COLOR, "Lỗ": NEG_COLOR},
                       title=f"Các bang lãi nhiều nhất & lỗ nặng nhất ({len(top_st)} bang)",
                       labels={"Profit": "Lợi nhuận ($)", "State": ""})
        fig_s.update_traces(hovertemplate="%{y}: $%{x:,.0f}<extra></extra>")
    fig_s.update_xaxes(tickprefix="$", tickformat="~s")
    fig_s.update_layout(yaxis=dict(categoryorder="total ascending"))
    show_chart(round_bars(fig_s), max(420, 26 * len(top_st)))

with right:
    if metric == "Sales":
        fig_map = px.choropleth(st_df, locations="Code", locationmode="USA-states", scope="usa",
                                color="Sales", color_continuous_scale=SEQ_SCALE, hover_name="State",
                                hover_data={"Code": False, "Sales": ":$,.0f", "Profit": ":$,.0f"},
                                labels={"Sales": "Doanh thu"}, title="Bản đồ doanh thu theo bang")
    else:
        lim = st_df["Profit"].abs().max()
        fig_map = px.choropleth(st_df, locations="Code", locationmode="USA-states", scope="usa",
                                color="Profit", color_continuous_scale=DIV_SCALE,
                                range_color=(-lim, lim), hover_name="State",
                                hover_data={"Code": False, "Sales": ":$,.0f", "Profit": ":$,.0f"},
                                labels={"Profit": "Lợi nhuận"},
                                title="Bản đồ lợi nhuận theo bang (đỏ = lỗ, xanh = lãi)")
    fig_map.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)"),
                          coloraxis_colorbar=dict(tickprefix="$", tickformat="~s", title=""))
    show_chart(fig_map, max(420, 26 * len(top_st)))

loss = st_df[st_df["Profit"] < 0].sort_values("Profit")
top2 = st_df.nlargest(2, "Sales")
top2_share = top2["Sales"].sum() / st_df["Sales"].sum()
txt = (f"**{top2['State'].iloc[0]}**"
       + (f" và **{top2['State'].iloc[1]}**" if len(top2) > 1 else "")
       + f" chiếm **{fmt_pct(top2_share)}** doanh thu của {len(st_df)} bang đang xem.")
if not loss.empty:
    txt += (f" Có **{len(loss)} bang thua lỗ** (tổng lỗ {fmt_money(loss['Profit'].sum())}), nặng nhất là "
            f"**{loss['State'].iloc[0]}** ({fmt_money(loss['Profit'].iloc[0])}, biên "
            f"{fmt_pct(loss['Margin'].iloc[0])}).")
else:
    txt += " Không có bang nào thua lỗ trong bộ lọc hiện tại."
insight(txt)

if not loss.empty:
    with st.expander(f"⚠️ Danh sách {len(loss)} bang thua lỗ"):
        disc = (dff[dff["State"].isin(loss["State"])].groupby("State")["Discount"].mean()
                .rename("Avg Discount"))
        st.dataframe(loss.merge(disc, left_on="State", right_index=True)
                     [["State", "Region", "Sales", "Profit", "Margin", "Avg Discount"]],
                     hide_index=True, width="stretch", column_config={
                         "State": "Bang", "Region": "Khu vực",
                         "Sales": st.column_config.NumberColumn("Doanh thu", format="dollar"),
                         "Profit": st.column_config.NumberColumn("Lợi nhuận", format="dollar"),
                         "Margin": st.column_config.NumberColumn("Biên LN", format="percent"),
                         "Avg Discount": st.column_config.NumberColumn("Chiết khấu TB", format="percent"),
                     })
        avg_loss_disc = disc.mean()
        avg_other = dff[~dff["State"].isin(loss["State"])]["Discount"].mean()
        insight(f"Chiết khấu trung bình ở các bang lỗ là **{fmt_pct(avg_loss_disc)}**, so với "
                f"**{fmt_pct(avg_other)}** ở các bang còn lại – chiết khấu sâu là nguyên nhân chính "
                f"bào mòn lợi nhuận.")
