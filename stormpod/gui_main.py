import tkinter as tk
from sensor_manager import SensorManager

UPDATE_INTERVAL_MS = 2000

class StormPODGUI:
    def __init__(self, root):
        self.manager = SensorManager()
        self.root = root
        self.root.title("StormPOD - Live Atmospheric Dashboard")
        self.root.geometry("1024x600")
        self.root.configure(bg="black")

        # Font
        self.font = ("Inconsolata", 22)
        self.font_large = ("Inconsolata", 32)

        # Lightning Alerts
        self.alert_label = tk.Label(root, text="", font=self.font_large, fg="red", bg="black")
        self.alert_label.pack(pady=10)

        # Heading
        self.heading_label = tk.Label(root, text="Heading: --", font=self.font, fg="white", bg="black")
        self.heading_label.pack(pady=5)

        # Wind
        self.wind_label = tk.Label(root, text="Wind: --", font=self.font, fg="white", bg="black")
        self.wind_label.pack(pady=5)

        # Atmos
        self.temp_label = tk.Label(root, text="Temp: --", font=self.font, fg="white", bg="black")
        self.temp_label.pack(pady=5)

        self.humid_label = tk.Label(root, text="Humidity: --", font=self.font, fg="white", bg="black")
        self.humid_label.pack(pady=5)

        self.press_label = tk.Label(root, text="Pressure: --", font=self.font, fg="white", bg="black")
        self.press_label.pack(pady=5)

        # Wind Dir (Angle)
        self.angle_label = tk.Label(root, text="Wind Dir: --", font=self.font, fg="white", bg="black")
        self.angle_label.pack(pady=5)

        self.update_loop()

    def update_loop(self):
        self.manager.poll_all()
        data = self.manager.get_latest()

        # Lightning
        if data.get("lightning"):
            km = data.get("distance_km", "?")
            self.alert_label.config(text=f"⚡ Lightning ~{km} km")
        elif data.get("noise"):
            self.alert_label.config(text="🔊 Noise Spike")
        elif data.get("disturber"):
            self.alert_label.config(text="⚠️ Disturber Rejected")
        else:
            self.alert_label.config(text="")

        # Heading
        heading = data.get("heading_deg")
        if heading is not None:
            self.heading_label.config(text=f"Heading: {heading:.1f}° {self._deg_to_cardinal(heading)}")
        else:
            self.heading_label.config(text="Heading: --")

        # Wind Speed + Raw
        wind_raw = data.get("wind_raw")
        if wind_raw is not None:
            volts = (wind_raw / 1023.0) * 3.3
            speed_kph = round((volts / 1.0) * 32.4, 1)  # Adafruit 1733 approx
            self.wind_label.config(text=f"Wind: {speed_kph} km/h ({volts:.2f} V)")
        else:
            self.wind_label.config(text="Wind: --")

        # Atmos
        t = data.get("temp_C")
        h = data.get("humidity_%")
        p = data.get("pressure_hPa")
        self.temp_label.config(text=f"Temp: {t:.1f} °C" if t is not None else "Temp: --")
        self.humid_label.config(text=f"Humidity: {h:.1f} %" if h is not None else "Humidity: --")
        self.press_label.config(text=f"Pressure: {p:.1f} hPa" if p is not None else "Pressure: --")

        # Wind Direction (AS5600)
        angle = data.get("angle_deg")
        if angle is not None:
            self.angle_label.config(text=f"Wind Dir: {angle:.1f}° {self._deg_to_cardinal(angle)}")
        else:
            self.angle_label.config(text="Wind Dir: --")

        self.root.after(UPDATE_INTERVAL_MS, self.update_loop)

    def _deg_to_cardinal(self, deg):
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = int((deg + 22.5) / 45) % 8
        return dirs[ix]

if __name__ == "__main__":
    root = tk.Tk()
    app = StormPODGUI(root)
    root.mainloop()
