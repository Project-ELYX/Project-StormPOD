#!/usr/bin/env python3
"""
Enhanced StormPOD GUI
--------------------
Improved interface with data trends, alerts, and better visualization.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import sys
import os

# Add the stormpod package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stormpod'))
from sensor_manager import SensorManager

class EnhancedStormPODGUI:
    def __init__(self, root):
        self.manager = SensorManager()
        self.root = root
        self.root.title("StormPOD - Live Atmospheric Monitoring")
        self.root.geometry("1024x600")
        self.root.configure(bg="#0a0a0a")
        
        # Data storage for trends
        self.max_points = 300  # 5 minutes at 1Hz
        self.timestamps = deque(maxlen=self.max_points)
        self.temperature_data = deque(maxlen=self.max_points)
        self.pressure_data = deque(maxlen=self.max_points)
        self.wind_speed_data = deque(maxlen=self.max_points)
        
        # Alert system
        self.alert_active = False
        self.alert_flash_count = 0
        
        self.setup_ui()
        self.update_loop()
        
    def setup_ui(self):
        # Create main frames
        self.alert_frame = tk.Frame(self.root, bg="#0a0a0a", height=100)
        self.alert_frame.pack(fill="x", padx=10, pady=5)
        
        self.data_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.data_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Alert display
        self.alert_label = tk.Label(
            self.alert_frame, 
            text="", 
            font=("Arial", 24, "bold"), 
            fg="#ff0000", 
            bg="#0a0a0a"
        )
        self.alert_label.pack(pady=20)
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.data_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Main dashboard tab
        self.dashboard_frame = tk.Frame(self.notebook, bg="#0a0a0a")
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")
        
        # Trends tab
        self.trends_frame = tk.Frame(self.notebook, bg="#0a0a0a")
        self.notebook.add(self.trends_frame, text="📈 Trends")
        
        # Setup dashboard
        self.setup_dashboard()
        
        # Setup trends
        self.setup_trends()
        
    def setup_dashboard(self):
        # Left column - Environmental data
        left_frame = tk.Frame(self.dashboard_frame, bg="#0a0a0a")
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        # Environmental section
        env_label = tk.Label(
            left_frame, 
            text="🌡️ ENVIRONMENTAL", 
            font=("Arial", 16, "bold"), 
            fg="#00ff00", 
            bg="#0a0a0a"
        )
        env_label.pack(pady=(10, 5))
        
        self.temp_label = self.create_data_label(left_frame, "Temperature", "--°C", "#ff6b35")
        self.humid_label = self.create_data_label(left_frame, "Humidity", "--%", "#4fc3f7")
        self.press_label = self.create_data_label(left_frame, "Pressure", "-- hPa", "#66bb6a")
        
        # Wind section
        wind_label = tk.Label(
            left_frame, 
            text="💨 WIND CONDITIONS", 
            font=("Arial", 16, "bold"), 
            fg="#00ff00", 
            bg="#0a0a0a"
        )
        wind_label.pack(pady=(20, 5))
        
        self.wind_speed_label = self.create_data_label(left_frame, "Speed", "-- km/h", "#ff9800")
        self.wind_dir_label = self.create_data_label(left_frame, "Direction", "--°", "#9c27b0")
        
        # Right column - Location & Lightning
        right_frame = tk.Frame(self.dashboard_frame, bg="#0a0a0a")
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        # Location section
        loc_label = tk.Label(
            right_frame, 
            text="📍 LOCATION", 
            font=("Arial", 16, "bold"), 
            fg="#00ff00", 
            bg="#0a0a0a"
        )
        loc_label.pack(pady=(10, 5))
        
        self.gps_label = self.create_data_label(right_frame, "GPS", "No Fix", "#f44336")
        self.heading_label = self.create_data_label(right_frame, "Heading", "--°", "#2196f3")
        
        # Lightning section
        lightning_label = tk.Label(
            right_frame, 
            text="⚡ LIGHTNING DETECTION", 
            font=("Arial", 16, "bold"), 
            fg="#00ff00", 
            bg="#0a0a0a"
        )
        lightning_label.pack(pady=(20, 5))
        
        self.lightning_label = self.create_data_label(right_frame, "Status", "Monitoring", "#ffeb3b")
        
        # Status bar at bottom
        self.status_label = tk.Label(
            self.dashboard_frame,
            text="🔄 Initializing StormPOD...",
            font=("Arial", 10),
            fg="#ffffff",
            bg="#0a0a0a"
        )
        self.status_label.pack(side="bottom", pady=5)
        
    def create_data_label(self, parent, name, value, color):
        frame = tk.Frame(parent, bg="#0a0a0a")
        frame.pack(fill="x", pady=2)
        
        name_label = tk.Label(
            frame, 
            text=f"{name}:", 
            font=("Arial", 12), 
            fg="#ffffff", 
            bg="#0a0a0a",
            width=12,
            anchor="w"
        )
        name_label.pack(side="left")
        
        value_label = tk.Label(
            frame, 
            text=value, 
            font=("Arial", 12, "bold"), 
            fg=color, 
            bg="#0a0a0a"
        )
        value_label.pack(side="left")
        
        return value_label
        
    def setup_trends(self):
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(
            3, 1, figsize=(12, 8), facecolor='#0a0a0a'
        )
        
        # Style the plots
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#0a0a0a')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
        self.ax1.set_ylabel('Temperature (°C)', color='white')
        self.ax2.set_ylabel('Pressure (hPa)', color='white')
        self.ax3.set_ylabel('Wind Speed (km/h)', color='white')
        self.ax3.set_xlabel('Time', color='white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.trends_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def update_trends(self):
        current_time = datetime.now()
        self.timestamps.append(current_time)
        
        # Get latest data
        data = self.manager.get_latest()
        
        self.temperature_data.append(data.get("temp_C", 0))
        self.pressure_data.append(data.get("pressure_hPa", 1000))
        self.wind_speed_data.append(data.get("speed_kph", 0))
        
        if len(self.timestamps) > 1:
            # Clear and replot
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.clear()
                ax.set_facecolor('#0a0a0a')
                ax.tick_params(colors='white')
                
            # Temperature plot
            self.ax1.plot(self.timestamps, self.temperature_data, '#ff6b35', linewidth=2)
            self.ax1.set_ylabel('Temperature (°C)', color='white')
            self.ax1.grid(True, alpha=0.3)
            
            # Pressure plot
            self.ax2.plot(self.timestamps, self.pressure_data, '#66bb6a', linewidth=2)
            self.ax2.set_ylabel('Pressure (hPa)', color='white')
            self.ax2.grid(True, alpha=0.3)
            
            # Wind speed plot
            self.ax3.plot(self.timestamps, self.wind_speed_data, '#ff9800', linewidth=2)
            self.ax3.set_ylabel('Wind Speed (km/h)', color='white')
            self.ax3.set_xlabel('Time', color='white')
            self.ax3.grid(True, alpha=0.3)
            
            self.canvas.draw()
        
    def update_loop(self):
        try:
            # Poll sensors
            self.manager.poll_all()
            data = self.manager.get_latest()
            
            # Update dashboard
            self.update_dashboard(data)
            
            # Update trends
            self.update_trends()
            
            # Check for alerts
            self.check_alerts(data)
            
            # Update status
            self.status_label.config(text=f"🔄 Last update: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Update error: {e}")
            self.status_label.config(text=f"⚠️ Error: {e}")
            
        # Schedule next update
        self.root.after(1000, self.update_loop)
        
    def update_dashboard(self, data):
        # Environmental data
        temp = data.get("temp_C")
        if temp is not None:
            self.temp_label.config(text=f"{temp:.1f}°C")
        
        humidity = data.get("humidity_%")
        if humidity is not None:
            self.humid_label.config(text=f"{humidity:.1f}%")
            
        pressure = data.get("pressure_hPa") 
        if pressure is not None:
            self.press_label.config(text=f"{pressure:.1f} hPa")
            
        # Wind data
        wind_speed = data.get("speed_kph")
        if wind_speed is not None:
            self.wind_speed_label.config(text=f"{wind_speed:.1f} km/h")
            
        wind_dir = data.get("angle_deg")
        if wind_dir is not None:
            cardinal = self._deg_to_cardinal(wind_dir)
            self.wind_dir_label.config(text=f"{wind_dir:.0f}° {cardinal}")
            
        # GPS data
        if data.get("fix"):
            lat = data.get("lat", 0)
            lon = data.get("lon", 0)
            self.gps_label.config(text=f"{lat:.4f}, {lon:.4f}", fg="#66bb6a")
        else:
            self.gps_label.config(text="No Fix", fg="#f44336")
            
        heading = data.get("heading_deg")
        if heading is not None:
            cardinal = self._deg_to_cardinal(heading)
            self.heading_label.config(text=f"{heading:.0f}° {cardinal}")
            
    def check_alerts(self, data):
        # Reset alert state
        alert_text = ""
        alert_color = "#ff0000"
        
        # Lightning alerts
        if data.get("lightning"):
            distance = data.get("distance_km", "?")
            alert_text = f"⚡ LIGHTNING DETECTED - {distance} km"
            self.lightning_label.config(text=f"⚡ {distance} km", fg="#ff0000")
            self.alert_active = True
        elif data.get("noise"):
            alert_text = "🔊 ELECTROMAGNETIC NOISE DETECTED"
            self.lightning_label.config(text="🔊 Noise", fg="#ff9800")
        elif data.get("disturber"):
            alert_text = "⚠️ ELECTRICAL INTERFERENCE"  
            self.lightning_label.config(text="⚠️ Interference", fg="#ff9800")
        else:
            self.lightning_label.config(text="Monitoring", fg="#ffeb3b")
            
        # Severe weather conditions
        temp = data.get("temp_C", 0)
        wind_speed = data.get("speed_kph", 0)
        
        if temp < -20:
            alert_text = f"🥶 EXTREME COLD WARNING - {temp:.1f}°C"
        elif temp > 40:
            alert_text = f"🔥 EXTREME HEAT WARNING - {temp:.1f}°C"
        elif wind_speed > 60:
            alert_text = f"💨 HIGH WIND WARNING - {wind_speed:.1f} km/h"
            
        # Display alert
        if alert_text:
            self.alert_label.config(text=alert_text, fg=alert_color)
            self.alert_active = True
        else:
            self.alert_label.config(text="")
            self.alert_active = False
            
    def _deg_to_cardinal(self, deg):
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = int((deg + 22.5) / 45) % 8
        return dirs[ix]

if __name__ == "__main__":
    root = tk.Tk()
    
    # Try enhanced GUI first, fallback to basic
    try:
        app = EnhancedStormPODGUI(root)
        print("✅ Enhanced StormPOD GUI loaded")
    except ImportError as e:
        print(f"⚠️ Enhanced GUI failed, using basic: {e}")
        from stormpod.gui_main import StormPODGUI
        app = StormPODGUI(root)
        
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 StormPOD shutdown requested")
    except Exception as e:
        print(f"❌ StormPOD crashed: {e}")
        raise