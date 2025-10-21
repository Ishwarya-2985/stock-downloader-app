import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="Stock Data Downloader", layout="centered")

st.title("📈 Stock Data to Excel Downloader")

# User Inputs
symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS):", "RELIANCE.NS")
date_str = st.text_input("Enter Date (YYYY-MM-DD):", "")

if st.button("Download Excel"):
    tz = pytz.timezone("Asia/Kolkata")

    # Handle date
    if not date_str.strip():
        target_date = (datetime.now(tz) - timedelta(days=1)).date()
    else:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    st.info(f"Fetching {symbol} 1-minute data for {target_date}")

    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)

    # Fetch data
    data = yf.download(
        tickers=symbol,
        start=start_dt,
        end=end_dt,
        interval="1m",
        progress=False
    )

    if data.empty:
        st.warning("⚠️ No data found for this date (yfinance may have limits).")
    else:
        df = data.reset_index()
        df.rename(columns={"Datetime": "timestamp"}, inplace=True)

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
        df["timestamp"] = df["timestamp"].dt.tz_convert(tz)

        df = df[["timestamp", "Open", "Close", "Volume"]]
        df.columns = ["timestamp", "open", "close", "volume"]
        df["time"] = df["timestamp"].dt.strftime("%H:%M")

        # Build full 1-min range
        full_range = pd.date_range(
            start=tz.localize(datetime.combine(target_date, datetime.min.time())),
            end=tz.localize(datetime.combine(target_date, datetime.max.time()).replace(hour=23, minute=59)),
            freq="T",
            tz=tz
        )
        full_df = pd.DataFrame({"timestamp": full_range, "time": full_range.strftime("%H:%M")})
        merged = pd.merge(full_df, df, on=["timestamp", "time"], how="left")
        merged["timestamp"] = merged["timestamp"].dt.tz_convert(None)

        # Save to Excel in memory
        output = BytesIO()
        merged.to_excel(output, index=False)
        output.seek(0)

        file_name = f"{symbol.replace('.', '_')}_{target_date}.xlsx"
        st.success("✅ Data ready! Click below to download.")
        st.download_button(
            label="📥 Download Excel File",
            data=output,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

