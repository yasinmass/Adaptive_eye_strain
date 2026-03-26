import streamlit as st
import time

st.set_page_config(page_title="Eye Strain Dashboard", layout="wide")

# Initialize session state
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "blinks" not in st.session_state:
    st.session_state.blinks = 0
if "strain_level" not in st.session_state:
    st.session_state.strain_level = "Low"

# Sidebar info
st.sidebar.title("Eye Strain Protection System")
st.sidebar.write("Monitor your eye health while using screens.")

# Main metrics
st.title("💻 Adaptive Eye Strain Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.metric("Total Blinks", st.session_state.blinks)
    st.metric("Screen Time (min)", int((time.time() - st.session_state.start_time)/60))

with col2:
    st.metric("Current Strain Level", st.session_state.strain_level)

# Optional: Live updating graph
import pandas as pd
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Time", "Blink Count", "Strain Level"])

# Add new data point
st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([{
    "Time": int(time.time() - st.session_state.start_time),
    "Blink Count": st.session_state.blinks,
    "Strain Level": st.session_state.strain_level
}])], ignore_index=True)

st.line_chart(st.session_state.history[["Time", "Blink Count"]])

# Strain level history
st.bar_chart(st.session_state.history["Strain Level"].map({"Low": 1, "Medium": 2, "High": 3}))