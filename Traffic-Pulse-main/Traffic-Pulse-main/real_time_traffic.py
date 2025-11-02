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
import threading
import time
import base64
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
import av
import requests

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

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.vehicle_count = 0
        self.last_update = time.time()
    
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Process every 5th frame to improve performance
        current_time = time.time()
        if current_time - self.last_update > 0.5:  # Update every 0.5 seconds
            processed_img, vehicle_count, _ = detect_vehicles(img.copy())
            self.vehicle_count = vehicle_count
            self.last_update = current_time
            return av.VideoFrame.from_ndarray(processed_img, format="bgr24")
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def webcam_live_analysis():
    st.subheader("📹 Live Webcam Analysis")
    st.markdown("*Real-time vehicle detection using your webcam*")
    
    # WebRTC configuration
    rtc_configuration = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        webrtc_ctx = webrtc_streamer(
            key="traffic-detection",
            video_processor_factory=VideoProcessor,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )
    
    with col2:
        st.subheader("📊 Live Metrics")
        metrics_placeholder = st.empty()
        
        if webrtc_ctx.video_processor:
            while webrtc_ctx.state.playing:
                with metrics_placeholder.container():
                    vehicle_count = webrtc_ctx.video_processor.vehicle_count
                    st.metric("🚗 Live Vehicle Count", vehicle_count)
                    
                    traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                    st.metric("🚦 Traffic Level", traffic_level)
                    
                    # Save data periodically
                    if vehicle_count > 0:
                        save_traffic_data(vehicle_count, "Live Webcam")
                
                time.sleep(1)
    
    st.info("💡 **Tips:** Ensure good lighting and position camera to capture traffic clearly")

def mobile_camera_analysis():
    st.subheader("📱 Mobile Camera Analysis")
    st.markdown("*Use your mobile device as a traffic monitoring camera*")
    
    # Instructions for mobile setup
    st.markdown("""
    ### 📋 Setup Instructions:
    1. **Install IP Webcam app** on your mobile device
    2. **Connect to same WiFi** as your computer
    3. **Start IP Webcam** and note the IP address
    4. **Enter the IP address** below
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mobile_ip = st.text_input("📱 Mobile IP Address (e.g., 192.168.1.100:8080)", 
                                 placeholder="192.168.1.100:8080")
        
        if mobile_ip and st.button("🔗 Connect to Mobile Camera"):
            try:
                mobile_url = f"http://{mobile_ip}/video"
                cap = cv2.VideoCapture(mobile_url)
                
                if cap.isOpened():
                    st.success("✅ Connected to mobile camera!")
                    
                    # Live stream processing
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    
                    stop_button = st.button("⏹️ Stop Stream")
                    
                    while not stop_button:
                        ret, frame = cap.read()
                        if ret:
                            processed_frame, vehicle_count, vehicles = detect_vehicles(frame)
                            processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                            
                            frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                            
                            with metrics_placeholder.container():
                                st.metric("🚗 Vehicle Count", vehicle_count)
                                traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                st.metric("🚦 Traffic Level", traffic_level)
                            
                            save_traffic_data(vehicle_count, "Mobile Camera")
                            time.sleep(0.1)
                        else:
                            st.error("❌ Failed to read from mobile camera")
                            break
                    
                    cap.release()
                else:
                    st.error("❌ Could not connect to mobile camera. Check IP address and network.")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    with col2:
        st.markdown("### 📱 Recommended Apps:")
        st.markdown("""
        **Android:**
        - IP Webcam
        - DroidCam
        - Open Camera
        
        **iOS:**
        - EpocCam
        - iVCam
        - Camo
        """)
        
        st.markdown("### 🔧 Troubleshooting:")
        st.markdown("""
        - Ensure same WiFi network
        - Check firewall settings
        - Try different port numbers
        - Restart mobile app
        """)

def ip_camera_analysis():
    st.subheader("🎥 IP Camera Analysis")
    st.markdown("*Connect to IP cameras or RTSP streams for traffic monitoring*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        camera_type = st.selectbox("📹 Camera Type:", ["IP Camera (HTTP)", "RTSP Stream", "USB Camera"])
        
        if camera_type == "IP Camera (HTTP)":
            camera_url = st.text_input("🔗 Camera URL:", placeholder="http://192.168.1.100/video.mjpg")
        elif camera_type == "RTSP Stream":
            camera_url = st.text_input("🔗 RTSP URL:", placeholder="rtsp://username:password@192.168.1.100:554/stream")
        else:
            camera_index = st.number_input("📹 USB Camera Index:", min_value=0, max_value=10, value=0)
            camera_url = camera_index
        
        if st.button("🎬 Start Camera Stream"):
            try:
                cap = cv2.VideoCapture(camera_url)
                
                if cap.isOpened():
                    st.success("✅ Camera connected successfully!")
                    
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    stop_stream = st.button("⏹️ Stop Stream")
                    
                    while not stop_stream:
                        ret, frame = cap.read()
                        if ret:
                            processed_frame, vehicle_count, vehicles = detect_vehicles(frame)
                            processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                            
                            frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                            
                            with metrics_placeholder.container():
                                st.metric("🚗 Vehicle Count", vehicle_count)
                                traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                st.metric("🚦 Traffic Level", traffic_level)
                            
                            save_traffic_data(vehicle_count, "IP Camera")
                            time.sleep(0.1)
                        else:
                            st.error("❌ Failed to read from camera")
                            break
                    
                    cap.release()
                else:
                    st.error("❌ Could not connect to camera. Check URL and credentials.")
            except Exception as e:
                st.error(f"❌ Camera error: {str(e)}")
    
    with col2:
        st.markdown("### 🎥 Supported Formats:")
        st.markdown("""
        - **HTTP:** .mjpg, .jpg streams
        - **RTSP:** Live camera streams
        - **USB:** Local USB cameras
        """)
        
        st.markdown("### 🔐 Authentication:")
        st.markdown("""
        Include credentials in URL:
        `rtsp://user:pass@ip:port/stream`
        """)

def file_analysis_mode():
    st.subheader("📁 File Analysis")
    st.markdown("*Drag and drop images or videos for traffic analysis*")
    
    # File upload with drag and drop
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📎 Drop Files Here")
    uploaded_files = st.file_uploader(
        "Choose files...", 
        type=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov', 'mkv'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        
        for i, uploaded_file in enumerate(uploaded_files):
            st.markdown(f"---")
            st.subheader(f"📄 File {i+1}: {uploaded_file.name}")
            
            file_type = uploaded_file.type
            
            if file_type.startswith('image/'):
                process_image_file(uploaded_file)
            elif file_type.startswith('video/'):
                process_video_file(uploaded_file)
            else:
                st.error(f"❌ Unsupported file type: {file_type}")

def process_image_file(uploaded_file):
    col1, col2 = st.columns(2)
    
    # Display original image
    image = Image.open(uploaded_file)
    
    with col1:
        st.markdown("#### 📷 Original Image")
        st.image(image, use_column_width=True)
    
    # Process image
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    with st.spinner("🔍 Analyzing image..."):
        processed_img, vehicle_count, vehicles = detect_vehicles(img_array.copy())
        processed_img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
        
        # Save data
        save_traffic_data(vehicle_count, f"Image: {uploaded_file.name}")
        
        with col2:
            st.markdown("#### 🎯 Analysis Results")
            st.image(processed_img_rgb, use_column_width=True)
        
        display_traffic_metrics(vehicle_count, vehicles)

def process_video_file(uploaded_file):
    # Save uploaded video temporarily
    temp_video_path = f"temp_{uploaded_file.name}"
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.read())
    
    st.markdown("#### 🎬 Video Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Video player
        st.video(temp_video_path)
    
    with col2:
        st.markdown("#### ⚙️ Analysis Options")
        
        frame_skip = st.slider("Frame Skip (for faster processing)", 1, 30, 5)
        max_frames = st.slider("Max Frames to Analyze", 10, 500, 100)
        
        if st.button(f"🔍 Analyze Video: {uploaded_file.name}", type="primary"):
            analyze_video_file(temp_video_path, frame_skip, max_frames, uploaded_file.name)
    
    # Clean up temp file
    try:
        os.remove(temp_video_path)
    except:
        pass

def analyze_video_file(video_path, frame_skip, max_frames, filename):
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error("❌ Could not open video file")
        return
    
    # Get video info
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    st.info(f"📊 Video Info: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Results containers
    results_container = st.container()
    
    frame_count = 0
    analyzed_frames = 0
    vehicle_counts = []
    timestamps = []
    
    # Analysis loop
    while cap.isOpened() and analyzed_frames < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            # Analyze frame
            processed_frame, vehicle_count, vehicles = detect_vehicles(frame.copy())
            
            vehicle_counts.append(vehicle_count)
            timestamps.append(frame_count / fps if fps > 0 else analyzed_frames)
            
            analyzed_frames += 1
            
            # Update progress
            progress = min(analyzed_frames / max_frames, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Analyzing frame {analyzed_frames}/{max_frames} - Found {vehicle_count} vehicles")
            
            # Save data
            save_traffic_data(vehicle_count, f"Video: {filename} (Frame {frame_count})")
        
        frame_count += 1
    
    cap.release()
    
    # Display results
    with results_container:
        st.markdown("---")
        st.subheader("📈 Video Analysis Results")
        
        if vehicle_counts:
            # Create DataFrame for analysis
            df_video = pd.DataFrame({
                'timestamp': timestamps,
                'vehicle_count': vehicle_counts
            })
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎬 Frames Analyzed", analyzed_frames)
            with col2:
                st.metric("🚗 Avg Vehicles", f"{np.mean(vehicle_counts):.1f}")
            with col3:
                st.metric("📊 Peak Count", max(vehicle_counts))
            with col4:
                st.metric("📉 Min Count", min(vehicle_counts))
            
            # Time series chart
            fig = px.line(df_video, x='timestamp', y='vehicle_count',
                         title=f'Vehicle Count Over Time - {filename}',
                         labels={'timestamp': 'Time (seconds)', 'vehicle_count': 'Vehicle Count'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Traffic Statistics")
                stats_df = pd.DataFrame({
                    'Metric': ['Average', 'Maximum', 'Minimum', 'Std Dev'],
                    'Value': [
                        f"{np.mean(vehicle_counts):.2f}",
                        f"{max(vehicle_counts)}",
                        f"{min(vehicle_counts)}",
                        f"{np.std(vehicle_counts):.2f}"
                    ]
                })
                st.dataframe(stats_df, use_container_width=True)
            
            with col2:
                st.markdown("#### 🎯 Traffic Insights")
                avg_count = np.mean(vehicle_counts)
                if avg_count > 10:
                    st.error("🔴 Heavy traffic detected throughout video")
                elif avg_count > 5:
                    st.warning("🟡 Moderate traffic levels observed")
                else:
                    st.success("🟢 Light traffic conditions")
                
                # Peak traffic times
                peak_idx = np.argmax(vehicle_counts)
                peak_time = timestamps[peak_idx]
                st.info(f"📈 Peak traffic at {peak_time:.1f}s with {max(vehicle_counts)} vehicles")
        else:
            st.warning("⚠️ No vehicles detected in the analyzed frames")

def display_traffic_metrics(vehicle_count, vehicles):
    # Enhanced Metrics with better styling
    st.markdown("---")
    st.subheader("📊 Traffic Analytics")
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

def main():
    init_db()
    
    # Header
    st.markdown('<h1 class="main-header">🚗 Traffic Pulse Dashboard</h1>', unsafe_allow_html=True)
    
    # Enhanced sidebar with better navigation
    st.sidebar.markdown("### 🎯 Navigation")
    mode = st.sidebar.radio(
        "Choose Analysis Mode:",
        ["📁 File Analysis", "📹 Webcam Live", "📱 Mobile Camera", "🎥 IP Camera"],
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
    
    if mode == "📁 File Analysis":
        file_analysis_mode()
    elif mode == "📹 Webcam Live":
        webcam_live_analysis()
    elif mode == "📱 Mobile Camera":
        mobile_camera_analysis()
    elif mode == "🎥 IP Camera":
        ip_camera_analysis()

if __name__ == "__main__":
    main()