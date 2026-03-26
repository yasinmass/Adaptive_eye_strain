import streamlit as st
import pandas as pd
import time
import datetime

def render_dashboard(tracker, monitor):
    st.set_page_config(page_title="Eye Strain Dashboard", layout="wide")
    st.title("💻 Adaptive Eye Strain Dashboard")
    
    if "history" not in st.session_state:
        st.session_state.history = pd.DataFrame(columns=["Time", "Blink Rate", "Strain Level Numeric"])
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()

    placeholder = st.empty()
    
    # Fast polling loop to refresh UI state from the background thread
    while tracker.running:
        with placeholder.container():
            if tracker.state == "CALIBRATING":
                st.warning("⚠️ System is currently calibrating... Please keep your eyes open naturally and look at the camera for 10 seconds.")
                st.info("Metrics will appear after calibration.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Blinks", tracker.blink_count)
                with col2:
                    st.metric("Blink Rate (bpm)", monitor.blink_rate)
                with col3:
                    st.metric("Screen Time (min)", f"{monitor.screen_time:.1f}")
                with col4:
                    strain = monitor.current_strain
                    color = "green" if strain == "Low" else "orange" if strain == "Medium" else "red"
                    st.markdown(f"### Current Strain: <span style='color:{color}'>{strain}</span>", unsafe_allow_html=True)

                # Store history and process charts ~1 time per second
                current_time = time.time()
                if current_time - st.session_state.last_update >= 1:
                    strain_mapping = {"Low": 1, "Medium": 2, "High": 3}
                    num_strain = strain_mapping.get(monitor.current_strain, 1)

                    new_row = pd.DataFrame([{
                        "Time": datetime.datetime.now().strftime("%H:%M:%S"),
                        "Blink Rate": monitor.blink_rate,
                        "Strain Level Numeric": num_strain
                    }])
                    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
                    st.session_state.last_update = current_time
                    
                    # Keep at most 60 history ticks
                    if len(st.session_state.history) > 60:
                        st.session_state.history = st.session_state.history.iloc[-60:]

                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.subheader("Blink Rate Over Time")
                    if not st.session_state.history.empty:
                        st.line_chart(st.session_state.history["Blink Rate"].tolist())
                        
                with col_chart2:
                    st.subheader("Strain Level (1=Low, 2=Medium, 3=High)")
                    if not st.session_state.history.empty:
                        st.line_chart(st.session_state.history["Strain Level Numeric"].tolist())

        # Update rate for streamlit rendering
        time.sleep(0.5)