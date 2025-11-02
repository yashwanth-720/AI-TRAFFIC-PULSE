🚦 Traffic Pulse Real-Time Vehicle Classification and Traffic Analysis

💡 About The Project Traffic Pulse is a real-time traffic analysis system designed to address urban congestion problems. The system captures live video feeds, classifies and counts the number of vehicles, and identifies their types (e.g., cars, bikes, trucks). By comparing this real-time vehicle population with historical data, it provides actionable insights into traffic density.

The primary purpose of Traffic Pulse is to empower users to make informed decisions about their daily commute. By pinning live camera footage, users can directly observe traffic conditions on their planned routes. This project is still in active development, with a focus on creating a robust and accurate classification model.

🚀 Features Real-time Video Processing: Analyzes live video feeds to provide up-to-the-minute traffic information.

Vehicle Classification: Distinguishes between different types of vehicles, such as cars, bikes, and trucks.

Vehicle Counting: Accurately counts the number of vehicles in the live feed.

Database Integration: Stores vehicle population data for comparison with historical trends.

Traffic Trend Analysis: Compares current traffic density with normal day averages to highlight unusual congestion.

User Alerts: Educates users about traffic conditions, helping them choose alternative routes to avoid congested areas.

🛠️ Built With Python: The primary programming language used for development.

OpenCV: Used for real-time video capture and processing.

TensorFlow/PyTorch: for vehicle classification.

MySQL/PostgreSQL: for storing and managing vehicle data.

🤝 Contribution This project is a collaborative effort by our team. We welcome contributions and suggestions to improve its accuracy and functionality.

Team Members:

Anshul H(Team Lead)

Hasnain Mohammed Shariff(Teammate 2)

Yashwanth P(Teammate 3)

Mohammed Hassan(Teammate 4)

-->How to run:

1. Navigate to Project Directory
cd "path of the file
"

Copy
bash
2. Create Virtual Environment (Recommended)
python -m venv venv
venv\Scripts\activate

Copy
3. Install Dependencies
pip install --upgrade pip
pip install -r Requirements.txt

Copy
bash
4. Run the Project (Choose One Option)
Option A: Quick Start with Batch File

start_servers.bat

Copy
bash
Option B: Manual Streamlit App

streamlit run streamlit_app.py

Copy
bash
Option C: Ultimate Dashboard

streamlit run ultimate_traffic_dashboard.py --server.port=8501

Copy
bash
Option D: Command Line Vehicle Tracking

python main.py

Copy
bash
5. Access the Application
Ultimate Dashboard: http://localhost:8501

API Server: http://localhost:8082

API Documentation: http://localhost:8082/docs

6. For Development/Testing
python api_server.py  # Start API server separately

Copy









Traffic Pulse is a real-time system that analyzes live video feeds to classify and count vehicles. It compares current traffic density with historical data to identify congestion. This project aims to help users avoid traffic by providing real-time insights and enabling them to choose alternative routes.
