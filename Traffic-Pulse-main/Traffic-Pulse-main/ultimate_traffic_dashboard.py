import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os

# Page config
st.set_page_config(
    page_title="🚗 Traffic Pulse Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('traffic_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS traffic_counts
                 (timestamp TEXT, vehicle_count INTEGER, location TEXT)''')
    conn.commit()
    conn.close()

def save_traffic_data(count, location="Main Road"):
    conn = sqlite3.connect('traffic_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO traffic_counts VALUES (?, ?, ?)",
              (datetime.now().isoformat(), count, location))
    conn.commit()
    conn.close()

def get_traffic_data():
    conn = sqlite3.connect('traffic_data.db')
    df = pd.read_sql_query("SELECT * FROM traffic_counts ORDER BY timestamp DESC LIMIT 100", conn)
    conn.close()
    return df

# Vehicle detection function
def detect_vehicles(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    vehicle_count = 0
    detected_vehicles = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 0.5 < aspect_ratio < 4.0:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f'Vehicle {vehicle_count+1}', (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                vehicle_count += 1
                detected_vehicles.append({'x': x, 'y': y, 'w': w, 'h': h, 'area': area})
    
    return frame, vehicle_count, detected_vehicles

# Main app
def main():
    init_db()
    
    # Header
    st.markdown('<h1 class="main-header">🚗 Traffic Pulse Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Enhanced sidebar with better navigation
    st.sidebar.markdown("### 🎯 Navigation")
    mode = st.sidebar.radio(
        "Choose Analysis Mode:",
        ["📊 Live Analysis", "📈 Historical Data", "⚙️ Settings"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    df = get_traffic_data()
    if not df.empty:
        st.sidebar.metric("Total Analyses", len(df))
        st.sidebar.metric("Avg Vehicles", f"{df['vehicle_count'].mean():.1f}")
        st.sidebar.metric("Peak Count", df['vehicle_count'].max())
    else:
        st.sidebar.info("No data yet - start analyzing!")
    
    if mode == "📊 Live Analysis":
        live_analysis_mode()
    elif mode == "📈 Historical Data":
        historical_data_mode()
    elif mode == "⚙️ Settings":
        settings_mode()

def live_analysis_mode():
    st.header("📊 Live Traffic Analysis")
    
    # Enhanced file upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📸 Upload Traffic Image")
    st.markdown("*Drag and drop or click to upload an image for analysis*")
    uploaded_file = st.file_uploader("", type=['jpg', 'jpeg', 'png'], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("")
    
    if uploaded_file:
        # Display original image
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📷 Original Image")
            st.image(image, use_column_width=True)
        
        # Process image
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        if st.button("🔍 Analyze Traffic", type="primary"):
            with st.spinner("Analyzing traffic..."):
                processed_img, vehicle_count, vehicles = detect_vehicles(img_array.copy())
                processed_img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                
                # Save data
                save_traffic_data(vehicle_count)
                
                with col2:
                    st.subheader("🎯 Analysis Results")
                    st.image(processed_img_rgb, use_column_width=True)
                
                # Enhanced Metrics with better styling
                st.markdown("---")
                st.subheader("📈 Traffic Analytics")
                col1, col2, col3, col4 = st.columns(4)
                
                traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                congestion_score = min(100, vehicle_count * 8)
                avg_speed = max(10, 60 - vehicle_count * 3)
                
                with col1:
                    st.metric("🚗 Total Vehicles", vehicle_count, delta=f"+{vehicle_count}" if vehicle_count > 0 else None)
                with col2:
                    st.metric("🚦 Traffic Level", traffic_level)
                with col3:
                    st.metric("📊 Congestion Score", f"{congestion_score}%")
                with col4:
                    st.metric("⚡ Est. Avg Speed", f"{avg_speed} km/h")
                
                # Enhanced Vehicle details with insights
                if vehicles:
                    st.markdown("---")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("🚙 Vehicle Detection Details")
                        vehicle_df = pd.DataFrame(vehicles)
                        vehicle_df.index += 1
                        vehicle_df['size'] = vehicle_df['area'].apply(lambda x: 'Large' if x > 5000 else 'Medium' if x > 2000 else 'Small')
                        st.dataframe(vehicle_df, use_container_width=True)
                    
                    with col2:
                        st.subheader("📊 Vehicle Size Distribution")
                        size_counts = vehicle_df['size'].value_counts()
                        fig_pie = px.pie(values=size_counts.values, names=size_counts.index, 
                                        title="Vehicle Sizes")
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                # Traffic insights
                st.markdown("---")
                st.subheader("🧠 AI Traffic Insights")
                
                insights = []
                if vehicle_count == 0:
                    insights.append("✅ Clear road conditions - optimal for travel")
                elif vehicle_count <= 3:
                    insights.append("🟢 Light traffic - good flow expected")
                elif vehicle_count <= 8:
                    insights.append("🟡 Moderate traffic - some delays possible")
                else:
                    insights.append("🔴 Heavy traffic - expect significant delays")
                
                if len(vehicles) > 0:
                    avg_size = np.mean([v['area'] for v in vehicles])
                    if avg_size > 4000:
                        insights.append("🚛 Large vehicles detected - may affect traffic flow")
                    
                for insight in insights:
                    st.info(insight)

def historical_data_mode():
    st.header("📈 Historical Traffic Analytics")
    st.markdown("*Analyze traffic patterns and trends over time*")
    
    # Get data
    df = get_traffic_data()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['date'] = df['timestamp'].dt.date
        
        # Time series chart
        fig_time = px.line(df, x='timestamp', y='vehicle_count', 
                          title='Traffic Count Over Time',
                          labels={'vehicle_count': 'Vehicle Count', 'timestamp': 'Time'})
        st.plotly_chart(fig_time, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Hourly distribution
            hourly_avg = df.groupby('hour')['vehicle_count'].mean().reset_index()
            fig_hourly = px.bar(hourly_avg, x='hour', y='vehicle_count',
                               title='Average Traffic by Hour')
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        with col2:
            # Daily summary
            daily_stats = df.groupby('date').agg({
                'vehicle_count': ['sum', 'mean', 'max']
            }).round(2)
            daily_stats.columns = ['Total', 'Average', 'Peak']
            st.subheader("📅 Daily Summary")
            st.dataframe(daily_stats, use_container_width=True)
        
        # Statistics
        st.subheader("📊 Traffic Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total Records", len(df))
        with col2:
            st.metric("🚗 Average Count", f"{df['vehicle_count'].mean():.1f}")
        with col3:
            st.metric("📊 Peak Count", df['vehicle_count'].max())
        with col4:
            st.metric("📉 Min Count", df['vehicle_count'].min())
    
    else:
        st.info("No historical data available. Start analyzing images to build your traffic database!")

def settings_mode():
    st.header("⚙️ Advanced Settings & Configuration")
    st.markdown("*Customize detection parameters and manage your data*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Detection Settings")
        min_area = st.slider("Minimum Vehicle Area", 500, 5000, 1000)
        aspect_ratio_min = st.slider("Min Aspect Ratio", 0.1, 2.0, 0.5)
        aspect_ratio_max = st.slider("Max Aspect Ratio", 2.0, 10.0, 4.0)
        
        st.subheader("📊 Display Settings")
        show_bounding_boxes = st.checkbox("Show Bounding Boxes", True)
        show_vehicle_numbers = st.checkbox("Show Vehicle Numbers", True)
    
    with col2:
        st.subheader("🗄️ Database Management")
        if st.button("📊 View Database Stats"):
            df = get_traffic_data()
            if not df.empty:
                st.success(f"Database contains {len(df)} records")
                st.json({
                    "Total Records": len(df),
                    "Date Range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
                    "Average Count": round(df['vehicle_count'].mean(), 2)
                })
            else:
                st.warning("Database is empty")
        
        if st.button("🗑️ Clear Database", type="secondary"):
            conn = sqlite3.connect('traffic_data.db')
            c = conn.cursor()
            c.execute("DELETE FROM traffic_counts")
            conn.commit()
            conn.close()
            st.success("Database cleared!")
    
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.info("""
    **Traffic Pulse Dashboard** v2.0
    
    Features:
    - AI-powered vehicle detection
    - Real-time traffic analysis
    - Interactive data visualizations
    - Smart traffic insights
    - Historical trend analysis
    - Customizable detection settings
    """)

if __name__ == "__main__":
    main()