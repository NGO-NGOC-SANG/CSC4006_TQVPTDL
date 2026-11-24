"""Tiện ích dùng chung cho dashboard Superstore Sales.

- load_data(): đọc CSV (latin-1), chuyển ngày sang datetime, thêm cột phái sinh. Có @st.cache_data.
- sidebar_filters(): bộ lọc sidebar dùng chung (thời gian, Region, Category, Segment),
  giữ nguyên lựa chọn khi chuyển page.
- Bảng màu cố định theo thực thể + template Plotly + hàm định dạng / insight.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "superstore.csv"

# ----------------------------------------------------------------------------
# Màu sắc: màu đi theo thực thể (không theo thứ hạng) để mọi page nhất quán
# ----------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
REGION_COLORS = {"West": SERIES[0], "East": SERIES[1], "Central": SERIES[2], "South": SERIES[3]}
CATEGORY_COLORS = {"Technology": SERIES[0], "Furniture": SERIES[1], "Office Supplies": SERIES[2]}
SEGMENT_COLORS = {"Consumer": SERIES[0], "Corporate": SERIES[1], "Home Office": SERIES[2]}
SHIPMODE_COLORS = {"Standard Class": SERIES[0], "Second Class": SERIES[1],
                   "First Class": SERIES[2], "Same Day": SERIES[3]}
COLOR_MAPS = {"Region": REGION_COLORS, "Category": CATEGORY_COLORS,
              "Segment": SEGMENT_COLORS, "Ship Mode": SHIPMODE_COLORS}
MEASURE_COLORS = {"Sales": "#2a78d6", "Profit": "#1baf7a"}
POS_COLOR, NEG_COLOR = "#2a78d6", "#e34948"  # cặp phân kỳ: lãi (xanh) / lỗ (đỏ)
SEQ_SCALE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIV_SCALE = [[0, "#e34948"], [0.5, "#f0efec"], [1, "#2a78d6"]]

# Nhãn tiếng Việt cho các cột
VN = {
    "Sales": "Doanh thu ($)", "Profit": "Lợi nhuận ($)", "Quantity": "Số lượng",
    "Discount": "Chiết khấu", "Margin": "Biên lợi nhuận", "Region": "Khu vực",
    "State": "Bang", "City": "Thành phố", "Category": "Danh mục", "Sub-Category": "Danh mục con",
    "Segment": "Phân khúc", "Ship Mode": "Hình thức giao", "Product Name": "Sản phẩm",
    "Order Date": "Ngày đặt", "Month": "Tháng", "Year": "Năm", "Orders": "Số đơn hàng",
    "Ship Days": "Số ngày giao",
}

# Không đặt màu chữ / lưới cố định: để template "streamlit" tự đổi theo light/dark theme.
# Tiêu đề neo ở mép trên, legend nằm ngay trên vùng vẽ, margin top đủ rộng để hai phần không chồng nhau.
pio.templates["superstore"] = go.layout.Template(
    layout=dict(
        colorway=SERIES,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
        margin=dict(l=10, r=10, t=95, b=10),
        bargap=0.25,
        title=dict(font=dict(size=16), y=0.98, yanchor="top", yref="container", x=0, xanchor="left"),
    )
)
pio.templates.default = "streamlit+superstore"


def theme_type() -> str | None:
    """'light' / 'dark' theo giao diện người dùng; None nếu trình duyệt chưa báo (lượt chạy đầu)."""
    try:
        return st.context.theme.type
    except Exception:
        return None


def surface() -> str:
    """Màu nền biểu đồ theo theme – dùng cho đường phân cách giữa các khối màu.

    Chưa biết theme -> xám bán trong suốt, nhìn ổn trên cả nền sáng lẫn tối.
    """
    return {"dark": "#0e1117", "light": "#ffffff"}.get(theme_type(), "rgba(128,128,128,0.35)")


def contrast_text(fill_hex: str) -> str:
    """Chữ đen hoặc trắng tùy độ sáng của màu nền ô (WCAG relative luminance)."""
    h = fill_hex.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#0b0b0b" if lum > 0.22 else "#ffffff"


# ----------------------------------------------------------------------------
# Dữ liệu
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Đang tải dữ liệu...")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, encoding="latin-1")
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Quarter"] = df["Order Date"].dt.to_period("Q").astype(str)
    df["Month Num"] = df["Order Date"].dt.month
    df["Ship Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Margin"] = df["Profit"] / df["Sales"]
    return df


@dataclass
class Filters:
    start: date
    end: date
    regions: list[str]
    categories: list[str]
    segments: list[str]
    ship_modes: list[str] | None = None
    sub_categories: list[str] | None = None
    extra: dict = field(default_factory=dict)

    def describe(self) -> str:
        return (f"{self.start:%d/%m/%Y} – {self.end:%d/%m/%Y} · "
                f"{len(self.regions)} khu vực · {len(self.categories)} danh mục · "
                f"{len(self.segments)} phân khúc")


def apply_filters(df: pd.DataFrame, f: Filters, ignore_date: bool = False) -> pd.DataFrame:
    mask = (df["Region"].isin(f.regions) & df["Category"].isin(f.categories)
            & df["Segment"].isin(f.segments))
    if f.ship_modes is not None:
        mask &= df["Ship Mode"].isin(f.ship_modes)
    if f.sub_categories is not None:
        mask &= df["Sub-Category"].isin(f.sub_categories)
    if not ignore_date:
        mask &= df["Order Date"].between(pd.Timestamp(f.start), pd.Timestamp(f.end))
    return df[mask]


def _keep(*keys: str) -> None:
    """Giữ trạng thái widget khi chuyển page (tránh Streamlit xoá state của widget)."""
    for k in keys:
        if k in st.session_state:
            st.session_state[k] = st.session_state[k]


def _reset_filters(df: pd.DataFrame) -> None:
    st.session_state["f_dates"] = (df["Order Date"].min().date(), df["Order Date"].max().date())
    st.session_state["f_region"] = sorted(df["Region"].unique())
    st.session_state["f_category"] = sorted(df["Category"].unique())
    st.session_state["f_segment"] = sorted(df["Segment"].unique())
    st.session_state["f_shipmode"] = sorted(df["Ship Mode"].unique())
    st.session_state["f_subcat"] = sorted(df["Sub-Category"].unique())


def sidebar_filters(df: pd.DataFrame, advanced: bool = False) -> Filters:
    """Vẽ bộ lọc sidebar dùng chung và trả về Filters.

    advanced=True: thêm bộ lọc Hình thức giao hàng & Danh mục con (dùng ở Page 5).
    """
    keys = ["f_dates", "f_region", "f_category", "f_segment", "f_shipmode", "f_subcat"]
    _keep(*keys)
    if "f_dates" not in st.session_state:
        _reset_filters(df)

    dmin, dmax = df["Order Date"].min().date(), df["Order Date"].max().date()
    sb = st.sidebar
    sb.header("🔎 Bộ lọc dữ liệu")
    sb.caption("Bộ lọc áp dụng cho mọi trang và được giữ khi chuyển trang.")

    dates = sb.date_input("📅 Khoảng thời gian (ngày đặt hàng)", min_value=dmin, max_value=dmax,
                          key="f_dates", format="DD/MM/YYYY")
    if isinstance(dates, (tuple, list)):
        start = dates[0] if len(dates) > 0 else dmin
        end = dates[1] if len(dates) > 1 else dmax
    else:
        start, end = dates, dmax

    regions = sb.multiselect("🗺️ Khu vực (Region)", sorted(df["Region"].unique()), key="f_region")
    categories = sb.multiselect("📦 Danh mục (Category)", sorted(df["Category"].unique()), key="f_category")
    segments = sb.multiselect("👥 Phân khúc khách hàng (Segment)", sorted(df["Segment"].unique()),
                              key="f_segment")

    ship_modes = sub_cats = None
    if advanced:
        with sb.expander("⚙️ Bộ lọc nâng cao", expanded=False):
            ship_modes = st.multiselect("🚚 Hình thức giao hàng", sorted(df["Ship Mode"].unique()),
                                        key="f_shipmode")
            sub_options = sorted(df.loc[df["Category"].isin(categories), "Sub-Category"].unique())
            st.session_state["f_subcat"] = [s for s in st.session_state.get("f_subcat", [])
                                            if s in sub_options] or sub_options
            sub_cats = st.multiselect("🏷️ Danh mục con", sub_options, key="f_subcat")

    sb.button("↺ Đặt lại bộ lọc", on_click=_reset_filters, args=(df,), width="stretch")

    f = Filters(start, end, regions, categories, segments, ship_modes, sub_cats)
    missing = [name for name, v in [("Khu vực", regions), ("Danh mục", categories),
                                    ("Phân khúc", segments), ("Hình thức giao", ship_modes),
                                    ("Danh mục con", sub_cats)] if v is not None and len(v) == 0]
    if missing:
        st.warning(f"⚠️ Hãy chọn ít nhất một giá trị cho: **{', '.join(missing)}** ở thanh bên trái.")
        st.stop()
    if start > end:
        st.warning("⚠️ Ngày bắt đầu phải trước ngày kết thúc.")
        st.stop()
    sb.divider()
    sb.caption("Nguồn: Superstore Sales (Kaggle) · 9.994 dòng giao dịch 2014–2017")
    return f


def get_filtered(advanced: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, Filters]:
    """Trả về (toàn bộ dữ liệu, dữ liệu đã lọc, filters). Dừng page nếu rỗng."""
    df = load_data()
    f = sidebar_filters(df, advanced=advanced)
    dff = apply_filters(df, f)
    if dff.empty:
        st.info("Không có dữ liệu phù hợp với bộ lọc hiện tại. Hãy nới rộng bộ lọc.")
        st.stop()
    return df, dff, f


# ----------------------------------------------------------------------------
# Định dạng & hiển thị
# ----------------------------------------------------------------------------
def fmt_money(x: float, decimals: int = 1) -> str:
    sign = "-" if x < 0 else ""
    a = abs(x)
    if a >= 1e6:
        return f"{sign}${a / 1e6:.{decimals + 1}f}M"
    if a >= 1e3:
        return f"{sign}${a / 1e3:.{decimals}f}K"
    return f"{sign}${a:,.0f}"


def fmt_pct(x: float, decimals: int = 1, signed: bool = False) -> str:
    return f"{x * 100:+.{decimals}f}%" if signed else f"{x * 100:.{decimals}f}%"


def fmt_int(x: float) -> str:
    return f"{int(x):,}".replace(",", ".")


def _md_to_html(text: str) -> str:
    """Chuyển **đậm** / *nghiêng* (markdown) sang thẻ HTML vì nội dung nằm trong <div>."""
    text = html.escape(text, quote=False).replace("$", "&#36;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)


def insight(text: str) -> None:
    """Khối nhận xét ngắn dưới biểu đồ. Màu nền bán trong suốt, chữ kế thừa theme (light/dark)."""
    st.markdown(
        f"<div style='border-left:4px solid #2a78d6;background:rgba(42,120,214,0.12);"
        f"padding:0.6rem 0.9rem;border-radius:4px;margin:-0.4rem 0 1.2rem 0;font-size:0.95rem'>"
        f"💡 <b>Nhận xét:</b> {_md_to_html(text)}</div>",
        unsafe_allow_html=True,
    )


NAV_PAGES = [
    ("app.py", "Trang chủ", "🏠"),
    ("pages/1_Tong_quan.py", "Tổng quan kinh doanh", "📈"),
    ("pages/2_Xu_huong.py", "Xu hướng thời gian", "📅"),
    ("pages/3_Khu_vuc.py", "Phân tích khu vực", "🗺️"),
    ("pages/4_San_pham.py", "Phân tích sản phẩm", "📦"),
    ("pages/5_Trai_nghiem.py", "Khám phá & trải nghiệm", "🧩"),
]

_CSS = """<style>
/* Nền & viền bán trong suốt: đọc được ở cả light và dark theme, chữ giữ màu của theme */
[data-testid="stMetric"] {background:rgba(128,128,128,0.08);
    border:1px solid rgba(128,128,128,0.25);border-radius:8px;padding:0.8rem 1rem;}
[data-testid="stMetricValue"] {font-size:1.7rem;}
.block-container {padding-top:2rem;}
</style>"""


def setup_page(title: str) -> None:
    """Gọi đầu tiên ở mọi page: cấu hình trang, CSS dùng chung và menu điều hướng tiếng Việt.

    Thư mục pages/ khiến Streamlit chạy từng file page độc lập (không qua app.py),
    nên cấu hình chung phải nằm ở đây. Menu tự sinh bị ẩn trong .streamlit/config.toml.
    """
    st.set_page_config(page_title=f"{title} · Superstore Dashboard", page_icon="📊", layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 📊 Superstore Dashboard")
        for path, label, icon in NAV_PAGES:
            st.page_link(path, label=label, icon=icon)
        st.divider()


def page_header(title: str, question: str, f: Filters | None = None) -> None:
    st.title(title)
    st.markdown(f"> *Câu hỏi của khách hàng:* **“{question}”**")
    if f is not None:
        st.caption(f"Đang xem: {f.describe()}")


def show_chart(fig: go.Figure, height: int | None = None) -> None:
    if height:
        fig.update_layout(height=height)
    # Không cắt nhãn số nằm ngoài cột (textposition="outside")
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
    # Tiêu đề biểu đồ đã nói rõ nội dung -> bỏ dòng tiêu đề legend (vd. "Chỉ số") cho gọn
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def round_bars(fig: go.Figure) -> go.Figure:
    try:
        fig.update_traces(marker_cornerradius=4, selector=dict(type="bar"))
    except ValueError:
        pass
    return fig


STATE_CODES = {
    "Alabama": "AL", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL",
    "Georgia": "GA", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}
