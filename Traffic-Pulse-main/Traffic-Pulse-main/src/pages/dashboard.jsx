import React, { useState, useEffect } from "react";
import { TrafficData, TrafficAlert } from "@/entities/all";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Car, 
  Truck, 
  Bike, 
  Bus, 
  Activity, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  MapPin,
  Clock
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar } from "recharts";
import { format } from "date-fns";

import LiveMetrics from "../components/dashboard/LiveMetrics";
import TrafficMap from "../components/dashboard/TrafficMap";
import ActiveAlerts from "../components/dashboard/ActiveAlerts";
import VehicleBreakdown from "../components/dashboard/VehicleBreakdown";
import TrafficDetection from "../components/TrafficDetection";

export default function Dashboard() {
  const [trafficData, setTrafficData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Simulate real-time data updates
  useEffect(() => {
    loadInitialData();
    
    // Update time every second
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    // Simulate real-time traffic data updates every 10 seconds
    const dataInterval = setInterval(() => {
      generateLiveTrafficUpdate();
    }, 10000);

    return () => {
      clearInterval(timeInterval);
      clearInterval(dataInterval);
    };
  }, []);

  const loadInitialData = async () => {
    try {
      const [trafficResponse, alertsResponse] = await Promise.all([
        TrafficData.list('-timestamp', 20),
        TrafficAlert.list('-created_date', 10)
      ]);
      
      setTrafficData(trafficResponse);
      setAlerts(alertsResponse.filter(alert => alert.status === 'active'));
      setIsLoading(false);
    } catch (error) {
      console.error("Error loading dashboard data:", error);
      setIsLoading(false);
    }
  };

  const generateLiveTrafficUpdate = async () => {
    // Simulate new traffic data
    const locations = [
      "Downtown Junction", "Highway 101", "Main Street Bridge", 
      "Airport Road", "Business District", "Shopping Plaza"
    ];
    
    const location = locations[Math.floor(Math.random() * locations.length)];
    const carCount = Math.floor(Math.random() * 50) + 10;
    const truckCount = Math.floor(Math.random() * 10) + 1;
    const bikeCount = Math.floor(Math.random() * 15) + 2;
    const busCount = Math.floor(Math.random() * 5) + 1;
    const totalVehicles = carCount + truckCount + bikeCount + busCount;
    
    const densityLevels = ["light", "moderate", "heavy"];
    const density = densityLevels[Math.floor(totalVehicles / 20)];
    
    const newData = {
      location_name: location,
      latitude: 40.7128 + (Math.random() - 0.5) * 0.1,
      longitude: -74.0060 + (Math.random() - 0.5) * 0.1,
      timestamp: new Date().toISOString(),
      car_count: carCount,
      truck_count: truckCount,
      bike_count: bikeCount,
      bus_count: busCount,
      total_vehicles: totalVehicles,
      traffic_density: density,
      average_speed: Math.floor(Math.random() * 40) + 15,
      camera_id: `CAM_${Math.floor(Math.random() * 100)}`
    };

    try {
      await TrafficData.create(newData);
      // Refresh data
      const updatedData = await TrafficData.list('-timestamp', 20);
      setTrafficData(updatedData);
    } catch (error) {
      console.error("Error updating traffic data:", error);
    }
  };

  const getTotalVehicles = () => {
    return trafficData.reduce((sum, data) => sum + (data.total_vehicles || 0), 0);
  };

  const getAverageSpeed = () => {
    const validSpeeds = trafficData.filter(data => data.average_speed > 0);
    if (validSpeeds.length === 0) return 0;
    return Math.round(validSpeeds.reduce((sum, data) => sum + data.average_speed, 0) / validSpeeds.length);
  };

  const getTrafficTrend = () => {
    if (trafficData.length < 2) return 0;
    const recent = trafficData.slice(0, 5).reduce((sum, d) => sum + d.total_vehicles, 0);
    const previous = trafficData.slice(5, 10).reduce((sum, d) => sum + d.total_vehicles, 0);
    return ((recent - previous) / previous * 100).toFixed(1);
  };

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
              Traffic Control Center
            </h1>
            <div className="flex items-center gap-2 mt-2">
              <Clock className="w-4 h-4 text-slate-500" />
              <p className="text-slate-600">
                Last updated: {format(currentTime, "MMM d, yyyy 'at' HH:mm:ss")}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-emerald-700">System Online</span>
          </div>
        </div>

        {/* Live Metrics */}
        <LiveMetrics 
          totalVehicles={getTotalVehicles()}
          averageSpeed={getAverageSpeed()}
          activeAlerts={alerts.length}
          trafficTrend={getTrafficTrend()}
          isLoading={isLoading}
        />

        {/* Main Dashboard Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Traffic Map */}
          <div className="lg:col-span-2">
            <TrafficMap 
              trafficData={trafficData}
              isLoading={isLoading}
            />
          </div>

          {/* Vehicle Breakdown */}
          <div className="space-y-6">
            <VehicleBreakdown 
              trafficData={trafficData}
              isLoading={isLoading}
            />
            
            <ActiveAlerts 
              alerts={alerts}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Traffic Detection */}
        <TrafficDetection />

        {/* Recent Activity */}
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-slate-700" />
              Recent Traffic Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {trafficData.slice(0, 8).map((data, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-slate-50/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <MapPin className="w-4 h-4 text-slate-500" />
                    <div>
                      <p className="font-medium text-slate-900">{data.location_name}</p>
                      <p className="text-sm text-slate-600">
                        {data.total_vehicles} vehicles • {data.average_speed} km/h avg
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant={data.traffic_density === 'heavy' ? 'destructive' : 
                               data.traffic_density === 'moderate' ? 'default' : 'secondary'}
                      className="mb-1"
                    >
                      {data.traffic_density}
                    </Badge>
                    <p className="text-xs text-slate-500">
                      {format(new Date(data.timestamp), 'HH:mm')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}