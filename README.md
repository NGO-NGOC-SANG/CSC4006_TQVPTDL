# 📊 Dashboard Phân tích Doanh số Superstore

Bài tập lớn môn **Trực quan và phân tích dữ liệu**. Dashboard Streamlit giúp theo dõi tình hình kinh doanh, phân tích xu hướng doanh thu, so sánh hiệu quả giữa các khu vực và sản phẩm của chuỗi bán lẻ Superstore.

## Dữ liệu

- Nguồn: [Kaggle – Superstore Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
- Quy mô: 9.994 dòng × 21 cột, mỗi dòng là một sản phẩm trong một đơn hàng
- File: [`data/superstore.csv`](data/superstore.csv)

## Cấu trúc dự án

```
├── app.py               # Trang chủ dashboard
├── pages/
│   ├── 1_Tong_quan.py   # KPI, tổng hợp theo danh mục & phân khúc
│   ├── 2_Xu_huong.py    # Doanh thu/lợi nhuận theo thời gian, mùa vụ
│   ├── 3_Khu_vuc.py     # So sánh Region/State, bản đồ
│   ├── 4_San_pham.py    # Top sản phẩm, danh mục con lãi/lỗ
│   └── 5_Trai_nghiem.py # Khám phá, tra cứu & tải dữ liệu
├── utils.py             # Hàm dùng chung (tải dữ liệu, định dạng, menu)
├── eda.ipynb            # Notebook phân tích khám phá (EDA)
├── data/superstore.csv
└── báo cáo/             # Báo cáo LaTeX + PDF
```

## Cài đặt & chạy

Yêu cầu Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Trên Windows có thể chạy nhanh bằng `run_dashboard.bat`.

## Ảnh minh họa

![Trang chủ](báo%20cáo/hinh/p0_home.jpg)
![Tổng quan](báo%20cáo/hinh/p1_a.jpg)
![Xu hướng](báo%20cáo/hinh/p2_a.jpg)
![Khu vực](báo%20cáo/hinh/p3_a.jpg)
![Sản phẩm](báo%20cáo/hinh/p4_a.jpg)

## Báo cáo

Xem bản PDF tại [`báo cáo/báo cáo.pdf`](báo%20cáo/báo%20cáo.pdf).
