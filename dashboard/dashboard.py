import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Konfigurasi tampilan halaman
st.set_page_config(
    page_title="Olist E-Commerce Analytics Dashboard",
    page_icon="🛒",
    layout="wide"
)

sns.set_style("whitegrid")


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "main_data.csv")
    df = pd.read_csv(file_path)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    return df


df = load_data()

# ==================== SIDEBAR FILTER ====================
with st.sidebar:
    st.title("🛒 Olist E-Commerce")
    st.markdown("**Dashboard Analisis Transaksi, Ulasan Negatif & Segmentasi Pelanggan**")
    st.divider()

    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()

    date_range = st.date_input(
        label="Rentang Tanggal Pembelian",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    available_categories = sorted(df["product_category_name_english"].dropna().unique().tolist())
    selected_categories = st.multiselect(
        label="Filter Kategori Produk (Opsional)",
        options=available_categories,
        default=[],
        placeholder="Semua kategori ditampilkan"
    )

    st.divider()
    st.caption("Dataset: Brazilian E-Commerce Public Dataset by Olist")

# Terapkan filter tanggal & kategori
filtered_df = df[
    (df["order_purchase_timestamp"].dt.date >= start_date) &
    (df["order_purchase_timestamp"].dt.date <= end_date)
].copy()

if selected_categories:
    filtered_df = filtered_df[filtered_df["product_category_name_english"].isin(selected_categories)]

# ==================== HEADER & METRIK UTAMA ====================
st.title("📊 Dashboard Analisis Data E-Commerce Olist")
st.markdown(f"Periode Data: **{start_date.strftime('%d %b %Y')}** — **{end_date.strftime('%d %b %Y')}**")

orders_unique = filtered_df.drop_duplicates(subset=["order_id"])
delivered_unique = orders_unique[
    (orders_unique["order_status"] == "delivered") &
    (orders_unique["order_delivered_customer_date"].notna())
]
reviews_unique = filtered_df.dropna(subset=["review_id"]).drop_duplicates(subset=["review_id"])
neg_review_rate = (
    (reviews_unique["review_score"].isin([1, 2]).mean() * 100)
    if len(reviews_unique) > 0 else 0.0
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Pesanan", f"{len(orders_unique):,}")
with col2:
    st.metric("Pelanggan Unik (Delivered)", f"{delivered_unique['customer_unique_id'].nunique():,}")
with col3:
    avg_val = delivered_unique["total_order_value"].mean() if len(delivered_unique) > 0 else 0.0
    st.metric("Rata-Rata Nilai Pesanan", f"R$ {avg_val:,.2f}")
with col4:
    st.metric("Proporsi Ulasan Negatif (1–2)", f"{neg_review_rate:.2f}%")

st.divider()

# ==================== VISUALISASI 1: TREN PESANAN BULANAN ====================
st.subheader("1. Tren Volume Pesanan Bulanan & Pertumbuhan (Month-over-Month)")

if len(orders_unique) > 0:
    orders_trend = orders_unique.copy()
    orders_trend["year_month"] = orders_trend["order_purchase_timestamp"].dt.to_period("M").astype(str)
    monthly_orders = (
        orders_trend.groupby("year_month", as_index=False)
        .agg(total_orders=("order_id", "nunique"))
        .sort_values("year_month")
    )
    monthly_orders["mom_growth_pct"] = (monthly_orders["total_orders"].pct_change() * 100).round(2)

    fig1, ax1 = plt.subplots(figsize=(12, 4.8))
    ax1.plot(
        monthly_orders["year_month"],
        monthly_orders["total_orders"],
        marker="o",
        linewidth=2.5,
        color="#2563EB",
        markersize=7
    )

    peak_idx = monthly_orders["total_orders"].idxmax()
    peak_row = monthly_orders.loc[peak_idx]
    ax1.scatter([peak_row["year_month"]], [peak_row["total_orders"]], color="#DC2626", s=130, zorder=5)

    for _, row in monthly_orders.iterrows():
        is_peak = row["year_month"] == peak_row["year_month"]
        ax1.text(
            row["year_month"],
            row["total_orders"] + (monthly_orders["total_orders"].max() * 0.035),
            f"{int(row['total_orders']):,}",
            ha="center",
            fontsize=8.5,
            fontweight="bold" if is_peak else "normal",
            color="#DC2626" if is_peak else "#1E293B"
        )

    ax1.set_ylim(0, monthly_orders["total_orders"].max() * 1.18)
    ax1.set_title("Pergerakan Jumlah Pesanan Bulanan", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Bulan", fontsize=10)
    ax1.set_ylabel("Jumlah Pesanan", fontsize=10)
    plt.xticks(rotation=45)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    sns.despine()
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    with st.expander("Lihat Tabel Rincian Pesanan Bulanan & MoM Growth"):
        st.dataframe(monthly_orders, use_container_width=True, hide_index=True)
else:
    st.warning("Tidak ada data pesanan untuk rentang tanggal dan filter yang dipilih.")

st.divider()

# ==================== VISUALISASI 2: ULASAN NEGATIF & KETERLAMBATAN ====================
st.subheader("2. Kategori Produk dengan Ulasan Negatif Terbanyak & Tingkat Keterlambatan")

delivered_cat_df = filtered_df[
    (filtered_df["order_status"] == "delivered") &
    (filtered_df["order_delivered_customer_date"].notna())
].copy()

neg_reviews_df = delivered_cat_df[delivered_cat_df["review_score"].isin([1, 2])].drop_duplicates(
    subset=["product_category_name_english", "review_id"]
)

if len(neg_reviews_df) > 0:
    top_n = st.slider("Pilih Jumlah Kategori Teratas", min_value=3, max_value=10, value=5)

    top_neg_categories = (
        neg_reviews_df.groupby("product_category_name_english", as_index=False)
        .agg(
            jumlah_ulasan_negatif=("review_id", "count"),
            jumlah_pesanan_terlambat=("is_late", "sum"),
            persentase_terlambat=("is_late", lambda x: round(x.mean() * 100, 2))
        )
        .sort_values("jumlah_ulasan_negatif", ascending=False)
        .head(top_n)
    )

    plot_df = top_neg_categories.iloc[::-1]

    fig2, axes = plt.subplots(1, 2, figsize=(14, 5.2))

    colors_1 = ["#DC2626" if idx == plot_df.index[-1] else "#94A3B8" for idx in plot_df.index]
    bars1 = axes[0].barh(
        plot_df["product_category_name_english"],
        plot_df["jumlah_ulasan_negatif"],
        color=colors_1,
        height=0.6
    )
    axes[0].set_title(f"Top {top_n} Kategori Ulasan Negatif Terbanyak", fontsize=11.5, fontweight="bold", pad=10)
    axes[0].set_xlabel("Jumlah Ulasan Negatif (Skor 1 & 2)", fontsize=10)
    axes[0].set_ylabel("Kategori Produk", fontsize=10)
    axes[0].set_xlim(0, plot_df["jumlah_ulasan_negatif"].max() * 1.18)
    axes[0].grid(axis="x", linestyle="--", alpha=0.4)

    for bar in bars1:
        width = bar.get_width()
        axes[0].text(
            width + (plot_df["jumlah_ulasan_negatif"].max() * 0.015),
            bar.get_y() + bar.get_height() / 2,
            f"{int(width):,}",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#1E293B"
        )

    colors_2 = ["#D97706" if pct > 40 else "#94A3B8" for pct in plot_df["persentase_terlambat"]]
    bars2 = axes[1].barh(
        plot_df["product_category_name_english"],
        plot_df["persentase_terlambat"],
        color=colors_2,
        height=0.6
    )
    axes[1].set_title("Persentase Keterlambatan pada Pesanan Berulasan Negatif", fontsize=11.5, fontweight="bold", pad=10)
    axes[1].set_xlabel("Persentase Terlambat (%)", fontsize=10)
    axes[1].set_xlim(0, max(plot_df["persentase_terlambat"].max() * 1.22, 10))
    axes[1].grid(axis="x", linestyle="--", alpha=0.4)

    for bar in bars2:
        width = bar.get_width()
        axes[1].text(
            width + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.2f}%",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#1E293B"
        )

    sns.despine()
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    with st.expander("Lihat Tabel Rincian Ulasan Negatif & Keterlambatan"):
        st.dataframe(top_neg_categories, use_container_width=True, hide_index=True)
else:
    st.warning("Tidak ada data ulasan negatif untuk filter yang dipilih.")

st.divider()

# ==================== VISUALISASI 3: SEGMENTASI RFM ====================
st.subheader("3. Segmentasi Pelanggan Berdasarkan RFM Analysis (Recency, Frequency, Monetary)")

rfm_orders = delivered_unique.copy()
if len(rfm_orders) > 0:
    recent_date = rfm_orders["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm_df = rfm_orders.groupby("customer_unique_id", as_index=False).agg(
        max_order_timestamp=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("total_order_value", "sum")
    )
    rfm_df["recency"] = (recent_date - rfm_df["max_order_timestamp"]).dt.days
else:
    rfm_df = pd.DataFrame()

if len(rfm_df) >= 5:
    rfm_df["r_score"] = pd.qcut(rfm_df["recency"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm_df["f_score"] = pd.qcut(rfm_df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm_df["m_score"] = pd.qcut(rfm_df["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm_df["rfm_score"] = rfm_df["r_score"] + rfm_df["f_score"] + rfm_df["m_score"]

    def assign_rfm_segment(score):
        if score >= 13:
            return "Champions"
        elif score >= 10:
            return "Loyal Customers"
        elif score >= 7:
            return "Need Attention"
        else:
            return "At Risk / Lost"

    rfm_df["segment"] = rfm_df["rfm_score"].apply(assign_rfm_segment)

    segment_summary = (
        rfm_df.groupby("segment", as_index=False)
        .agg(
            jumlah_pelanggan=("customer_unique_id", "count"),
            rata_rata_recency=("recency", "mean"),
            rata_rata_frequency=("frequency", "mean"),
            rata_rata_monetary=("monetary", "mean")
        )
        .sort_values("jumlah_pelanggan", ascending=False)
    )
    segment_summary["persentase_pelanggan"] = (segment_summary["jumlah_pelanggan"] / len(rfm_df) * 100).round(2)
    segment_summary[["rata_rata_recency", "rata_rata_frequency", "rata_rata_monetary"]] = segment_summary[
        ["rata_rata_recency", "rata_rata_frequency", "rata_rata_monetary"]
    ].round(2)

    plot_seg = segment_summary.iloc[::-1]

    fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5.0))

    colors_seg = ["#2563EB" if seg == "Champions" else "#94A3B8" for seg in plot_seg["segment"]]
    bars_seg1 = axes3[0].barh(plot_seg["segment"], plot_seg["jumlah_pelanggan"], color=colors_seg, height=0.55)
    axes3[0].set_title("Distribusi Jumlah Pelanggan per Segmen RFM", fontsize=11.5, fontweight="bold", pad=10)
    axes3[0].set_xlabel("Jumlah Pelanggan Unik", fontsize=10)
    axes3[0].set_ylabel("Segmen Pelanggan", fontsize=10)
    axes3[0].set_xlim(0, plot_seg["jumlah_pelanggan"].max() * 1.32)
    axes3[0].grid(axis="x", linestyle="--", alpha=0.4)

    for bar, pct in zip(bars_seg1, plot_seg["persentase_pelanggan"]):
        width = bar.get_width()
        axes3[0].text(
            width + (plot_seg["jumlah_pelanggan"].max() * 0.015),
            bar.get_y() + bar.get_height() / 2,
            f"{int(width):,} ({pct:.1f}%)",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#1E293B"
        )

    colors_mon = ["#16A34A" if seg == "Champions" else "#94A3B8" for seg in plot_seg["segment"]]
    bars_seg2 = axes3[1].barh(plot_seg["segment"], plot_seg["rata_rata_monetary"], color=colors_mon, height=0.55)
    axes3[1].set_title("Rata-Rata Pengeluaran (Monetary) per Segmen", fontsize=11.5, fontweight="bold", pad=10)
    axes3[1].set_xlabel("Rata-Rata Pengeluaran (BRL / R$)", fontsize=10)
    axes3[1].set_xlim(0, plot_seg["rata_rata_monetary"].max() * 1.28)
    axes3[1].grid(axis="x", linestyle="--", alpha=0.4)

    for bar in bars_seg2:
        width = bar.get_width()
        axes3[1].text(
            width + (plot_seg["rata_rata_monetary"].max() * 0.015),
            bar.get_y() + bar.get_height() / 2,
            f"R$ {width:,.2f}",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#1E293B"
        )

    sns.despine()
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

    with st.expander("Lihat Tabel Ringkasan Metrik RFM per Segmen"):
        st.dataframe(segment_summary, use_container_width=True, hide_index=True)
else:
    st.warning("Jumlah pelanggan tidak mencukupi untuk perhitungan segmen RFM pada rentang filter ini.")

st.caption("Copyright © 2026 - Proyek Analisis Data E-Commerce Olist`")