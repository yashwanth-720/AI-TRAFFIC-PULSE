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
import random
import folium
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="🚗 AI-powered Traffic Pulse",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS with Modern Dashboard Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .main-header {
        font-size: 4rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 5px rgba(102, 126, 234, 0.5)); }
        to { filter: drop-shadow(0 0 20px rgba(118, 75, 162, 0.8)); }
    }
    
    .dashboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 25px 50px rgba(102, 126, 234, 0.4);
    }
    
    .route-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        border-left: 5px solid #fff;
        transition: all 0.3s ease;
    }
    
    .route-card:hover {
        transform: translateX(5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    }
    
    .ai-insight {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(255, 107, 107, 0.3);
        border-left: 5px solid #fff;
    }
    
    .metric-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem;
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(1.05);
    }
    
    .sidebar-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .upload-section {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        transition: all 0.3s ease;
        margin: 2rem 0;
    }
    
    .upload-section:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        transform: scale(1.02);
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-green { background-color: #2ecc71; }
    .status-yellow { background-color: #f39c12; }
    .status-red { background-color: #e74c3c; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border-top: 4px solid #667eea;
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .nav-pills {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 25px;
        padding: 0.5rem;
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('traffic_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS traffic_counts
                 (timestamp TEXT, vehicle_count INTEGER, location TEXT, lat REAL, lng REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS route_suggestions
                 (timestamp TEXT, origin TEXT, destination TEXT, suggested_route TEXT, traffic_level TEXT, estimated_time INTEGER)''')
    conn.commit()
    conn.close()

def save_traffic_data(count, location="Main Road", lat=None, lng=None):
    conn = sqlite3.connect('traffic_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO traffic_counts VALUES (?, ?, ?, ?, ?)",
              (datetime.now().isoformat(), count, location, lat, lng))
    conn.commit()
    conn.close()

def save_route_suggestion(origin, destination, route, traffic_level, est_time):
    conn = sqlite3.connect('traffic_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO route_suggestions VALUES (?, ?, ?, ?, ?, ?)",
              (datetime.now().isoformat(), origin, destination, route, traffic_level, est_time))
    conn.commit()
    conn.close()

def get_traffic_data():
    conn = sqlite3.connect('traffic_data.db')
    df = pd.read_sql_query("SELECT * FROM traffic_counts ORDER BY timestamp DESC LIMIT 100", conn)
    conn.close()
    return df

# AI Route Optimization Engine
class AIRouteOptimizer:
    def __init__(self):
        self.routes_db = {
            "Downtown to Airport": {
                "primary": {"route": "Highway 101 → Airport Blvd", "distance": 25, "normal_time": 30},
                "alternate1": {"route": "Main St → Industrial Ave → Airport", "distance": 28, "normal_time": 35},
                "alternate2": {"route": "Riverside Dr → Express Lane", "distance": 22, "normal_time": 28}
            },
            "City Center to Mall": {
                "primary": {"route": "Central Ave → Mall Drive", "distance": 15, "normal_time": 20},
                "alternate1": {"route": "Park St → Shopping Blvd", "distance": 18, "normal_time": 25},
                "alternate2": {"route": "Metro Route via Subway", "distance": 12, "normal_time": 30}
            },
            "Residential to Business District": {
                "primary": {"route": "Oak St → Business Pkwy", "distance": 12, "normal_time": 18},
                "alternate1": {"route": "Elm Ave → Corporate Dr", "distance": 14, "normal_time": 22},
                "alternate2": {"route": "Pine Rd → Commerce St", "distance": 16, "normal_time": 25}
            }
        }
    
    def analyze_traffic_impact(self, vehicle_count):
        if vehicle_count > 15:
            return {"level": "Heavy", "delay_factor": 2.5, "color": "🔴"}
        elif vehicle_count > 8:
            return {"level": "Moderate", "delay_factor": 1.8, "color": "🟡"}
        elif vehicle_count > 3:
            return {"level": "Light", "delay_factor": 1.2, "color": "🟢"}
        else:
            return {"level": "Clear", "delay_factor": 1.0, "color": "✅"}
    
    def get_ai_route_suggestions(self, origin, destination, current_traffic):
        route_key = f"{origin} to {destination}"
        if route_key not in self.routes_db:
            route_key = list(self.routes_db.keys())[0]  # Default route
        
        routes = self.routes_db[route_key]
        traffic_analysis = self.analyze_traffic_impact(current_traffic)
        
        suggestions = []
        for route_type, route_info in routes.items():
            # AI calculates estimated time based on traffic
            base_time = route_info["normal_time"]
            traffic_delay = base_time * (traffic_analysis["delay_factor"] - 1)
            estimated_time = int(base_time + traffic_delay)
            
            # AI priority scoring
            if route_type == "primary" and traffic_analysis["level"] in ["Heavy", "Moderate"]:
                priority = "Not Recommended"
                score = 2
            elif route_type == "alternate1":
                priority = "Recommended" if traffic_analysis["level"] != "Clear" else "Alternative"
                score = 1
            else:
                priority = "Best Alternative" if traffic_analysis["level"] == "Heavy" else "Option"
                score = 3 if traffic_analysis["level"] == "Heavy" else 4
            
            suggestions.append({
                "route": route_info["route"],
                "distance": route_info["distance"],
                "estimated_time": estimated_time,
                "priority": priority,
                "score": score,
                "traffic_impact": f"+{int(traffic_delay)} min delay" if traffic_delay > 0 else "No delay"
            })
        
        # Sort by AI score (lower is better)
        suggestions.sort(key=lambda x: x["score"])
        return suggestions, traffic_analysis

# Optimized vehicle detection
def detect_vehicles(frame):
    height, width = frame.shape[:2]
    if width > 640:
        scale = 640 / width
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    vehicle_count = 0
    detected_vehicles = []
    
    for i, contour in enumerate(contours[:30]):
        area = cv2.contourArea(contour)
        if 800 < area < 50000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 0.3 < aspect_ratio < 5.0:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
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
        self.skip_frames = 20
    
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        height, width = img.shape[:2]
        if width > 480:
            scale = 480 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        self.frame_count += 1
        current_time = time.time()
        
        if self.frame_count % self.skip_frames == 0 and current_time - self.last_update > 3.0:
            try:
                processed_img, vehicle_count, _ = detect_vehicles(img.copy())
                self.vehicle_count = vehicle_count
                self.last_update = current_time
                if processed_img.shape[1] != width:
                    processed_img = cv2.resize(processed_img, (width, height))
                return av.VideoFrame.from_ndarray(processed_img, format="bgr24")
            except:
                pass
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def display_ai_route_suggestions(vehicle_count, location="Current Location"):
    st.markdown("---")
    st.subheader("🤖 AI Route Optimizer")
    
    ai_optimizer = AIRouteOptimizer()
    
    # Route selection
    col1, col2 = st.columns(2)
    with col1:
        origin = st.selectbox("📍 From:", ["Downtown", "City Center", "Residential Area", "Airport", "Mall"])
    with col2:
        destination = st.selectbox("📍 To:", ["Airport", "Mall", "Business District", "Downtown", "Suburbs"])
    
    if origin != destination:
        suggestions, traffic_analysis = ai_optimizer.get_ai_route_suggestions(origin, destination, vehicle_count)
        
        # Enhanced Traffic Status with modern design
        st.markdown(f"""
        <div class="dashboard-card">
            <h4>🚦 AI Traffic Analysis Dashboard</h4>
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0;">
                <div>
                    <h3>{traffic_analysis['color']} {traffic_analysis['level']} Traffic</h3>
                    <p>Impact Factor: <strong>{traffic_analysis['delay_factor']}x</strong> normal time</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; font-size: 3rem;">{vehicle_count}</h2>
                    <p style="margin: 0;">Vehicles Detected</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # AI Route Suggestions
        st.subheader("🛣️ AI-Powered Route Suggestions")
        
        for i, suggestion in enumerate(suggestions):
            priority_color = {
                "Best Alternative": "🟢",
                "Recommended": "🟡", 
                "Not Recommended": "🔴",
                "Alternative": "🔵",
                "Option": "⚪"
            }
            
            color = priority_color.get(suggestion["priority"], "⚪")
            
            st.markdown(f"""
            <div class="route-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>{color} Route {i+1}: {suggestion['priority']}</h4>
                        <p><strong>📍 Path:</strong> {suggestion['route']}</p>
                        <p><strong>📏 Distance:</strong> {suggestion['distance']} km</p>
                    </div>
                    <div style="text-align: right;">
                        <h3 style="margin: 0; font-size: 2rem;">{suggestion['estimated_time']}</h3>
                        <p style="margin: 0;">minutes</p>
                        <small>{suggestion['traffic_impact']}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Save best route suggestion
        best_route = suggestions[0]
        save_route_suggestion(origin, destination, best_route['route'], 
                            traffic_analysis['level'], best_route['estimated_time'])
        
        # AI Insights
        st.subheader("🧠 AI Traffic Insights")
        
        insights = []
        if vehicle_count > 15:
            insights.extend([
                "🚨 Heavy congestion detected - avoid main routes",
                "🛣️ Consider alternate routes or delay travel",
                "⏰ Peak traffic hours - expect 2.5x longer travel time"
            ])
        elif vehicle_count > 8:
            insights.extend([
                "⚠️ Moderate traffic - alternate routes recommended", 
                "🕐 Travel time increased by 80%",
                "🚗 Consider carpooling or public transport"
            ])
        elif vehicle_count > 3:
            insights.extend([
                "✅ Light traffic - good time to travel",
                "🛣️ Main routes are viable options",
                "⏱️ Minimal delays expected"
            ])
        else:
            insights.extend([
                "🎉 Clear roads - optimal travel conditions",
                "🚀 Fastest routes available",
                "💚 Perfect time for travel"
            ])
        
        for i, insight in enumerate(insights):
            st.markdown(f"""
            <div class="ai-insight">
                <h5>💡 AI Insight #{i+1}</h5>
                <p>{insight}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Traffic Map Visualization
        display_traffic_map(vehicle_count, origin, destination)

def display_traffic_map(vehicle_count, origin, destination):
    st.subheader("🗺️ Live Traffic Map")
    
    # Create a simple traffic map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)
    
    # Simulate traffic data points
    traffic_points = [
        {"lat": 40.7128, "lng": -74.0060, "traffic": vehicle_count, "location": origin},
        {"lat": 40.7589, "lng": -73.9851, "traffic": max(0, vehicle_count-5), "location": "Route Point 1"},
        {"lat": 40.7282, "lng": -73.7949, "traffic": max(0, vehicle_count-8), "location": destination}
    ]
    
    for point in traffic_points:
        color = "red" if point["traffic"] > 10 else "orange" if point["traffic"] > 5 else "green"
        folium.CircleMarker(
            location=[point["lat"], point["lng"]],
            radius=10 + point["traffic"],
            popup=f"{point['location']}: {point['traffic']} vehicles",
            color=color,
            fill=True,
            fillColor=color
        ).add_to(m)
    
    # Display map
    map_data = st_folium(m, width=700, height=400)

def webcam_live_analysis():
    st.subheader("📹 Live Webcam Analysis with AI Route Optimization")
    
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
                if update_count % 5 == 0:
                    with metrics_placeholder.container():
                        vehicle_count = webrtc_ctx.video_processor.vehicle_count
                        st.metric("🚗 Live Vehicle Count", vehicle_count)
                        
                        traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                        st.metric("🚦 Traffic Level", traffic_level)
                        
                        if vehicle_count > 0 and update_count % 15 == 0:
                            save_traffic_data(vehicle_count, "Live Webcam")
                
                time.sleep(3)
    
    # AI Route Suggestions based on live data
    if webrtc_ctx.video_processor and webrtc_ctx.video_processor.vehicle_count > 0:
        display_ai_route_suggestions(webrtc_ctx.video_processor.vehicle_count, "Live Webcam Location")

def ip_camera_analysis():
    st.subheader("🎥 IP Camera Analysis with AI Route Optimization")
    
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
        
        if st.button("🎬 Start AI Analysis"):
            try:
                # Optimized camera connection
                if isinstance(camera_url, int):
                    cap = cv2.VideoCapture(camera_url, cv2.CAP_DSHOW)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                    cap.set(cv2.CAP_PROP_FPS, 10)
                else:
                    cap = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
                
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    st.success("✅ IP Camera connected successfully!")
                    
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    
                    frame_count = 0
                    last_analysis = time.time()
                    current_vehicle_count = 0
                    
                    stop_stream = st.button("⏹️ Stop Stream")
                    
                    for _ in range(150):  # Analyze for limited time
                        if stop_stream:
                            break
                            
                        ret, frame = cap.read()
                        if ret:
                            frame_count += 1
                            current_time = time.time()
                            
                            frame = cv2.resize(frame, (480, 360))
                            
                            if frame_count % 50 == 0 or current_time - last_analysis > 4.0:
                                try:
                                    processed_frame, vehicle_count, vehicles = detect_vehicles(frame.copy())
                                    processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                                    
                                    frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                                    
                                    with metrics_placeholder.container():
                                        st.metric("🚗 Vehicle Count", vehicle_count)
                                        traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                        st.metric("🚦 Traffic Level", traffic_level)
                                    
                                    current_vehicle_count = vehicle_count
                                    save_traffic_data(vehicle_count, "IP Camera")
                                    last_analysis = current_time
                                except:
                                    pass
                            else:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                frame_placeholder.image(frame_rgb, use_column_width=True)
                            
                            if frame_count % 3 != 0:
                                continue
                        else:
                            st.error("❌ Failed to read from camera")
                            break
                    
                    cap.release()
                    
                    # Show AI route suggestions after analysis
                    if current_vehicle_count > 0:
                        display_ai_route_suggestions(current_vehicle_count, "IP Camera Location")
                        
                else:
                    st.error("❌ Could not connect to camera.")
            except Exception as e:
                st.error(f"❌ Camera error: {str(e)}")
    
    with col2:
        st.markdown("### 🎥 Supported Formats:")
        st.markdown("""
        - **HTTP:** .mjpg, .jpg streams
        - **RTSP:** Live camera streams  
        - **USB:** Local USB cameras
        """)
        
        st.markdown("### 🤖 AI Features:")
        st.markdown("""
        - **Smart Route Analysis**
        - **Professional Camera Support**
        - **Real-time Traffic Assessment**
        - **Alternative Route Suggestions** 
        - **Travel Time Predictions**
        """)

def mobile_camera_analysis():
    st.subheader("📱 Mobile Camera Analysis with Smart Routing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mobile_ip = st.text_input("📱 Mobile IP Address", placeholder="192.168.1.100:8080")
        
        if mobile_ip and st.button("🔗 Connect & Analyze"):
            try:
                mobile_url = f"http://{mobile_ip}/video"
                cap = cv2.VideoCapture(mobile_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    st.success("✅ Connected to mobile camera!")
                    
                    frame_placeholder = st.empty()
                    metrics_placeholder = st.empty()
                    
                    frame_count = 0
                    last_analysis = time.time()
                    current_vehicle_count = 0
                    
                    for _ in range(100):  # Analyze for limited time
                        ret, frame = cap.read()
                        if ret:
                            frame_count += 1
                            current_time = time.time()
                            
                            frame = cv2.resize(frame, (480, 360))
                            
                            if frame_count % 60 == 0 or current_time - last_analysis > 5.0:
                                try:
                                    processed_frame, vehicle_count, vehicles = detect_vehicles(frame.copy())
                                    processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                                    
                                    frame_placeholder.image(processed_frame_rgb, use_column_width=True)
                                    
                                    with metrics_placeholder.container():
                                        st.metric("🚗 Vehicle Count", vehicle_count)
                                        traffic_level = "🔴 High" if vehicle_count > 10 else "🟡 Medium" if vehicle_count > 5 else "🟢 Low"
                                        st.metric("🚦 Traffic Level", traffic_level)
                                    
                                    current_vehicle_count = vehicle_count
                                    save_traffic_data(vehicle_count, "Mobile Camera")
                                    last_analysis = current_time
                                except:
                                    pass
                            else:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                frame_placeholder.image(frame_rgb, use_column_width=True)
                        else:
                            break
                    
                    cap.release()
                    
                    # Show AI route suggestions after analysis
                    if current_vehicle_count > 0:
                        display_ai_route_suggestions(current_vehicle_count, "Mobile Camera Location")
                        
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    with col2:
        st.markdown("### 🤖 AI Features:")
        st.markdown("""
        - **Smart Route Analysis**
        - **Real-time Traffic Assessment** 
        - **Alternative Route Suggestions**
        - **Travel Time Predictions**
        - **Traffic Pattern Learning**
        """)

def file_analysis_mode():
    st.subheader("📁 File Analysis with AI Route Optimization")
    
    uploaded_files = st.file_uploader(
        "Choose files...", 
        type=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded!")
        
        for i, uploaded_file in enumerate(uploaded_files):
            st.markdown(f"---")
            st.subheader(f"📄 File {i+1}: {uploaded_file.name}")
            
            if uploaded_file.type.startswith('image/'):
                image = Image.open(uploaded_file)
                img_array = np.array(image)
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(image, caption="Original", use_column_width=True)
                
                with st.spinner("🔍 AI Analyzing..."):
                    processed_img, vehicle_count, vehicles = detect_vehicles(img_array.copy())
                    processed_img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                    
                    with col2:
                        st.image(processed_img_rgb, caption="AI Analysis", use_column_width=True)
                    
                    st.metric("🚗 Vehicles Detected", vehicle_count)
                    save_traffic_data(vehicle_count, f"Image: {uploaded_file.name}")
                    
                    # AI Route Suggestions for this analysis
                    display_ai_route_suggestions(vehicle_count, f"Location: {uploaded_file.name}")

def main():
    init_db()
    
    # Main container with modern design
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Enhanced Header with dashboard info
    st.markdown('<h1 class="main-header">🤖 AI-powered Traffic Pulse</h1>', unsafe_allow_html=True)
    
    # Dashboard Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📁 File Analysis</h3>
            <p>Upload & analyze traffic images/videos with AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📹 Live Webcam</h3>
            <p>Real-time traffic monitoring with smart routing</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📱 Mobile Camera</h3>
            <p>Use smartphone as traffic sensor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>🎥 IP Camera</h3>
            <p>Professional camera integration</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Sidebar with modern design
    st.sidebar.markdown("""
    <div class="sidebar-card">
        <h3>🎯 AI Navigation Dashboard</h3>
        <p>Select your preferred analysis mode</p>
    </div>
    """, unsafe_allow_html=True)
    
    mode = st.sidebar.radio(
        "🚀 Choose Analysis Mode:",
        ["📁 File Analysis", "📹 Webcam Live", "📱 Mobile Camera", "🎥 IP Camera", "🗺️ Route Planner"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Live Dashboard Stats
    df = get_traffic_data()
    if not df.empty:
        st.sidebar.markdown("""
        <div class="sidebar-card">
            <h4>📊 Live Dashboard Stats</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.metric("🔥 Total Analyses", len(df))
        st.sidebar.metric("🚗 Avg Vehicles", f"{df['vehicle_count'].mean():.1f}")
        st.sidebar.metric("📈 Peak Count", df['vehicle_count'].max())
        
        # Traffic status indicator
        latest_count = df['vehicle_count'].iloc[0] if len(df) > 0 else 0
        if latest_count > 10:
            status_class = "status-red"
            status_text = "Heavy Traffic"
        elif latest_count > 5:
            status_class = "status-yellow" 
            status_text = "Moderate Traffic"
        else:
            status_class = "status-green"
            status_text = "Light Traffic"
            
        st.sidebar.markdown(f"""
        <div class="sidebar-card">
            <h4>🚦 Current Status</h4>
            <p><span class="status-indicator {status_class}"></span>{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("""
    <div class="sidebar-card">
        <h4>🤖 AI Features</h4>
        <ul style="list-style: none; padding: 0;">
            <li>✅ Smart Route Optimization</li>
            <li>✅ Real-time Traffic Analysis</li>
            <li>✅ Alternative Route Suggestions</li>
            <li>✅ AI-Powered Insights</li>
            <li>✅ Travel Time Predictions</li>
            <li>✅ Interactive Traffic Maps</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if mode == "📁 File Analysis":
        file_analysis_mode()
    elif mode == "📹 Webcam Live":
        webcam_live_analysis()
    elif mode == "📱 Mobile Camera":
        mobile_camera_analysis()
    elif mode == "🎥 IP Camera":
        ip_camera_analysis()
    elif mode == "🗺️ Route Planner":
        st.subheader("🗺️ AI Route Planner")
        st.markdown("*Plan your route with AI-powered traffic analysis*")
        
        # Manual route planning
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("📍 Starting Point:", placeholder="Enter your location")
        with col2:
            destination = st.text_input("📍 Destination:", placeholder="Where are you going?")
        
        traffic_level = st.slider("🚦 Current Traffic Level (vehicles):", 0, 25, 8)
        
        if origin and destination and st.button("🤖 Get AI Route Suggestions"):
            display_ai_route_suggestions(traffic_level, f"{origin} → {destination}")

    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
        <p>🤖 AI-powered Traffic Pulse Dashboard | Built with Streamlit & OpenCV</p>
        <p>Smart Traffic Analysis • Route Optimization • Real-time Monitoring</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()