import time
import psutil
from pynvml import *
import wmi
import tkinter as tk
from threading import Thread
import pythoncom  # Required for COM library initialization in threads

# Initialize NVML for GPU information
nvmlInit()

# Initialize global variables
latest_cpu = latest_memory = latest_gpu_used = latest_gpu_total = None
latest_hardware_info = {}

def get_cpu_info():
    return psutil.cpu_percent()

def get_memory_info():
    mem_info = psutil.virtual_memory()
    return mem_info.percent

def get_gpu_info():
    handle = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(handle)
    return info.used, info.total

def get_hardware_info():
    pythoncom.CoInitialize()  # Initialize COM library in the new thread
    w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    sensor_infos = w.Sensor()
    hardware_info = {}
    for sensor in sensor_infos:
        hardware_info[sensor.Name] = sensor.Value  # Capture all sensor data
    pythoncom.CoUninitialize()  # Uninitialize the COM library
    return hardware_info

def fetch_data():
    global latest_cpu, latest_memory, latest_gpu_used, latest_gpu_total, latest_hardware_info
    while True:
        latest_cpu = get_cpu_info()
        latest_memory = get_memory_info()
        latest_gpu_used, latest_gpu_total = get_gpu_info()
        latest_hardware_info = get_hardware_info()
        time.sleep(2)  # Update interval: 2 seconds

class SystemMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Monitor")
        self.geometry("400x500")
        self.labels = {}
        self.create_widgets()
        self.after(1000, self.update_info)  # Schedule the first update

        # Start the data fetching in a separate thread
        Thread(target=fetch_data, daemon=True).start()

    def create_widgets(self):
        self.labels['cpu'] = tk.Label(self, text='CPU Utilization: ')
        self.labels['cpu'].pack(fill='x')

        self.labels['memory'] = tk.Label(self, text='Memory Usage: ')
        self.labels['memory'].pack(fill='x')

        self.labels['gpu'] = tk.Label(self, text='GPU Memory Used: ')
        self.labels['gpu'].pack(fill='x')

        self.hardware_display = tk.Text(self)
        self.hardware_display.pack(fill='both', expand=True)

    def update_info(self):
        global latest_cpu, latest_memory, latest_gpu_used, latest_gpu_total, latest_hardware_info
        self.labels['cpu'].config(text=f'CPU Utilization: {round(latest_cpu, 2)} %')
        self.labels['memory'].config(text=f'Memory Usage: {round(latest_memory, 2)} %')
        self.labels['gpu'].config(text=f'GPU Memory Used: {round(latest_gpu_used / 1024**2, 2):.2f} MB / {round(latest_gpu_total / 1024**2, 2):.2f} MB')

    # Update the text widget with all hardware readings
        current_position = self.hardware_display.yview()  # Save current scroll position
        self.hardware_display.delete('1.0', tk.END)

    # Round the value to the nearest hundredth before displaying
        hardware_text = '\n'.join(f'{name}: {round(value, 2) if isinstance(value, float) else value}' for name, value in latest_hardware_info.items())
        self.hardware_display.insert(tk.END, hardware_text)
        self.hardware_display.yview_moveto(current_position[0])  # Restore scroll position

    # Schedule the next update
        self.after(1000, self.update_info)

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.mainloop()