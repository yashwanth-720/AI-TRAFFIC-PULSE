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

# Optimized vehicle detection function
def detect_vehicles(frame):
    # Resize frame for faster processing if too large
    height, width = frame.shape[:2]
    if width > 640:
        scale = 640 / width
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Reduced blur for faster processing
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Use simpler contour approximation for speed
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    vehicle_count = 0
    detected_vehicles = []
    
    # Limit contour processing for performance
    for i, contour in enumerate(contours[:30]):  # Process max 30 contours
        area = cv2.contourArea(contour)
        if 800 < area < 50000:  # Adjusted area range
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 0.3 < aspect_ratio < 5.0:  # Wider aspect ratio range
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                # Simplified text rendering
                cv2.putText(frame, f'V{vehicle_count+1}', (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                vehicle_count += 1
                detected_vehicles.append({'x': x, 'y': y, 'w': w, 'h': h, 'area': area})
    
    return frame, vehicle_count, detected_vehicles

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.vehicle_count = 0
        self.last_update = time.time()
        self.frame_count = 0
        self.skip_frames = 20  # Process every 20th frame
    
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Resize frame for faster processing
        height, width = img.shape[:2]
        if width > 480:
            scale = 480 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        self.frame_count += 1
        current_time = time.time()
        
        # Process less frequently for better performance
        if self.frame_count % self.skip_frames == 0 and current_time - self.last_update > 3.0:
            try:
                processed_img, vehicle_count, _ = detect_vehicles(img.copy())
                self.vehicle_count = vehicle_count
                self.last_update = current_time
                # Resize back if needed
                if processed_img.shape[1] != width:
                    processed_img = cv2.resize(processed_img, (width, height))
                return av.VideoFrame.from_ndarray(processed_img, format="bgr24")
            except:
                pass
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def webcam_live_analysis():
    st.subheader("📹 Live Webcam Analysis")
    st.markdown("*Optimized real-time vehicle detection*")
    
    # Optimized WebRTC configuration
    rtc_configuration = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        webrtc_ctx = webrtc_streamer(
            key="traffic-detection",
            video_processor_factory=VideoProcessor,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 480},
                    "height": {"ideal": 360},
                    "frameRate": {"ideal": 10, "max": 15}
                },
                "audio": False
            },
            async_processing=True,
        )
    
    with col2:
        st.subheader("📊 Live Metrics")
        metrics_placeholder = st.empty()
        
        if webrtc_ctx.video_processor:
            update_count = 0
            while webrtc_ctx.state.playing:
                update_count += 1
                # Update metrics less frequently
                if update_count % 5 == 0:
                    with metrics_placeholder.container():
                        vehicle_count = webrtc_ctx.video_processor.vehicle_count
                        st.metric("🚗 Live Vehicle Count", vehicle_count)
                        
                        traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                        st.metric("🚦 Traffic Level", traffic_level)
                        
                        # Save data less frequently
                        if vehicle_count > 0 and update_count % 15 == 0:
                            save_traffic_data(vehicle_count, "Live Webcam")
                
                time.sleep(3)  # Reduced update frequency
    
    st.info("💡 **Optimized for performance:** Lower resolution, reduced processing frequency")

def mobile_camera_analysis():
    st.subheader("📱 Mobile Camera Analysis")
    st.markdown("*Ultra-optimized mobile streaming*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mobile_ip = st.text_input("📱 Mobile IP Address", placeholder="192.168.1.100:8080")
        
        stream_format = st.selectbox("📹 Stream Format:", 
                                   ["MJPEG (/video)", "Snapshot (/shot.jpg)"])
        
        if mobile_ip and st.button("🔗 Connect to Mobile Camera"):
            try:
                # Clean IP input
                mobile_ip = mobile_ip.strip()
                if stream_format == "MJPEG (/video)":
                    mobile_url = f"http://{mobile_ip}/video"
                else:
                    mobile_url = f"http://{mobile_ip}/shot.jpg"
                
                st.info(f"Connecting to: {mobile_url}")
                
                # Test connection first
                try:
                    response = requests.get(mobile_url, timeout=3)
                    if response.status_code == 200:
                        st.success("✅ Connection test successful!")
                    else:
                        st.warning(f"⚠️ HTTP Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection test failed: {str(e)}")
                    return
                
                # Optimized camera connection
                cap = cv2.VideoCapture(mobile_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, 8)
                
                if cap.isOpened():
                    st.success("✅ Connected to mobile camera!")
                    
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    
                    frame_count = 0
                    last_analysis = time.time()
                    last_display = time.time()
                    
                    stop_button = st.button("⏹️ Stop Stream")
                    
                    while not stop_button:
                        ret, frame = cap.read()
                        if ret:
                            frame_count += 1
                            current_time = time.time()
                            
                            # Resize frame immediately
                            frame = cv2.resize(frame, (480, 360))
                            
                            # Display frame every 0.2 seconds (5 FPS display)
                            if current_time - last_display > 0.2:
                                # Analyze every 60th frame or every 5 seconds
                                if frame_count % 60 == 0 or current_time - last_analysis > 5.0:
                                    try:
                                        processed_frame, vehicle_count, vehicles = detect_vehicles(frame.copy())
                                        processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                                        
                                        frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                                        
                                        with metrics_placeholder.container():
                                            st.metric("🚗 Vehicle Count", vehicle_count)
                                            traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                            st.metric("🚦 Traffic Level", traffic_level)
                                        
                                        if vehicle_count > 0:
                                            save_traffic_data(vehicle_count, "Mobile Camera")
                                        last_analysis = current_time
                                    except Exception as e:
                                        st.error(f"Analysis error: {str(e)}")
                                else:
                                    # Show raw frame without analysis
                                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    frame_placeholder.image(frame_rgb, use_column_width=True)
                                
                                last_display = current_time
                            
                            # Skip frames to reduce processing load
                            if frame_count % 5 != 0:
                                continue
                        else:
                            st.error("❌ Failed to read from mobile camera")
                            break
                    
                    cap.release()
                else:
                    st.error("❌ Could not connect to mobile camera.")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    with col2:
        st.markdown("### 📱 Recommended Apps:")
        st.markdown("""
        **Android:**
        - IP Webcam (Free)
        - DroidCam
        
        **iOS:**
        - EpocCam
        - iVCam
        """)
        
        st.markdown("### ⚡ Performance Tips:")
        st.markdown("""
        - Use lower resolution in app
        - Reduce frame rate to 8-10 FPS
        - Close other apps on phone
        - Use 2.4GHz WiFi for stability
        """)

def ip_camera_analysis():
    st.subheader("🎥 IP Camera Analysis")
    st.markdown("*Optimized for professional cameras*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        camera_type = st.selectbox("📹 Camera Type:", ["USB Camera", "IP Camera (HTTP)", "RTSP Stream"])
        
        if camera_type == "IP Camera (HTTP)":
            camera_url = st.text_input("🔗 Camera URL:", placeholder="http://192.168.1.100/video.mjpg")
        elif camera_type == "RTSP Stream":
            camera_url = st.text_input("🔗 RTSP URL:", placeholder="rtsp://username:password@192.168.1.100:554/stream")
        else:
            camera_index = st.number_input("📹 USB Camera Index:", min_value=0, max_value=10, value=0)
            camera_url = camera_index
        
        if st.button("🎬 Start Optimized Stream"):
            try:
                # Optimized camera connection
                if isinstance(camera_url, int):
                    cap = cv2.VideoCapture(camera_url, cv2.CAP_DSHOW)  # DirectShow for Windows
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                    cap.set(cv2.CAP_PROP_FPS, 10)
                else:
                    cap = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
                
                # Set buffer size to reduce latency
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    st.success("✅ Camera connected successfully!")
                    
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    
                    frame_count = 0
                    last_analysis = time.time()
                    last_display = time.time()
                    
                    stop_stream = st.button("⏹️ Stop Stream")
                    
                    while not stop_stream:
                        ret, frame = cap.read()
                        if ret:
                            frame_count += 1
                            current_time = time.time()
                            
                            # Resize for consistent performance
                            frame = cv2.resize(frame, (480, 360))
                            
                            # Display at 6 FPS to reduce lag
                            if current_time - last_display > 0.167:
                                # Analyze every 50th frame or every 4 seconds
                                if frame_count % 50 == 0 or current_time - last_analysis > 4.0:
                                    try:
                                        processed_frame, vehicle_count, vehicles = detect_vehicles(frame.copy())
                                        processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                                        
                                        frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                                        
                                        with metrics_placeholder.container():
                                            st.metric("🚗 Vehicle Count", vehicle_count)
                                            traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                            st.metric("🚦 Traffic Level", traffic_level)
                                        
                                        if vehicle_count > 0:
                                            save_traffic_data(vehicle_count, "IP Camera")
                                        last_analysis = current_time
                                    except Exception as e:
                                        st.error(f"Analysis error: {str(e)}")
                                else:
                                    # Show raw frame
                                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    frame_placeholder.image(frame_rgb, use_column_width=True)
                                
                                last_display = current_time
                            
                            # Skip frames for better performance
                            if frame_count % 3 != 0:
                                continue
                        else:
                            st.error("❌ Failed to read from camera")
                            break
                    
                    cap.release()
                else:
                    st.error("❌ Could not connect to camera.")
            except Exception as e:
                st.error(f"❌ Camera error: {str(e)}")
    
    with col2:
        st.markdown("### ⚡ Optimization Features:")
        st.markdown("""
        - **Reduced Resolution:** 480x360 for speed
        - **Lower Frame Rate:** 6-10 FPS display
        - **Smart Analysis:** Every 4-5 seconds
        - **Buffer Management:** Minimal latency
        """)

def file_analysis_mode():
    st.subheader("📁 File Analysis")
    st.markdown("*Drag and drop images or videos*")
    
    # File upload
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📎 Drop Files Here")
    uploaded_files = st.file_uploader(
        "Choose files...", 
        type=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded!")
        
        for i, uploaded_file in enumerate(uploaded_files):
            st.markdown(f"---")
            st.subheader(f"📄 File {i+1}: {uploaded_file.name}")
            
            if uploaded_file.type.startswith('image/'):
                # Process image
                image = Image.open(uploaded_file)
                img_array = np.array(image)
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(image, caption="Original", use_column_width=True)
                
                with st.spinner("🔍 Analyzing..."):
                    processed_img, vehicle_count, vehicles = detect_vehicles(img_array.copy())
                    processed_img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                    
                    with col2:
                        st.image(processed_img_rgb, caption="Analysis", use_column_width=True)
                    
                    st.metric("🚗 Vehicles Detected", vehicle_count)
                    save_traffic_data(vehicle_count, f"Image: {uploaded_file.name}")

def main():
    init_db()
    
    # Header
    st.markdown('<h1 class="main-header">🚗 Traffic Pulse Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("### 🎯 Navigation")
    mode = st.sidebar.radio(
        "Choose Mode:",
        ["📁 File Analysis", "📹 Webcam Live", "📱 Mobile Camera", "🎥 IP Camera"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Performance Mode")
    st.sidebar.info("Optimized for low latency and smooth streaming")
    
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