import time
import psutil
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
import wmi
import tkinter as tk
from tkinter import ttk
from threading import Thread
import pythoncom
from dataclasses import dataclass, field

nvmlInit()

@dataclass
class SystemInfo:
    cpu: float = None
    memory: float = None
    gpu_used: float = None
    gpu_total: float = None
    hardware_info: dict = field(default_factory=dict)
    
system_info = SystemInfo()

def get_cpu_info() -> float:
    return psutil.cpu_percent()

def get_memory_info() -> float:
    mem_info = psutil.virtual_memory()
    return mem_info.percent

def get_gpu_info() -> tuple:
    handle = nvmlDeviceGetHandleByIndex(0)
    info = nvmlDeviceGetMemoryInfo(handle)
    return info.used, info.total

def get_hardware_info() -> dict:
    pythoncom.CoInitialize()
    w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    hardware_info = {sensor.Name: sensor.Value for sensor in w.Sensor()}
    pythoncom.CoUninitialize()
    return hardware_info

def fetch_data():
    while True:
        system_info.cpu = get_cpu_info()
        system_info.memory = get_memory_info()
        system_info.gpu_used, system_info.gpu_total = get_gpu_info()
        system_info.hardware_info = get_hardware_info()
        time.sleep(2)

class SystemMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Monitor")
        self.geometry("400x500")
        self.configure(bg='black')
        self.labels = {}
        self.create_widgets()
        self.after(1000, self.update_info)
        Thread(target=fetch_data, daemon=True).start()

    def create_widgets(self):
        for item in ['cpu', 'memory', 'gpu']:
            self.labels[item] = ttk.Label(self, text=f'{item.capitalize()} Utilization: ', background='black', foreground='white')
            self.labels[item].pack(fill='x')

        self.hardware_display = tk.Text(self, bg='black', fg='white')
        self.hardware_display.pack(fill='both', expand=True)

    def update_info(self):
        self.labels['cpu'].config(text=f'CPU Utilization: {round(system_info.cpu, 2) if system_info.cpu else 0.0} %')
        self.labels['memory'].config(text=f'Memory Usage: {round(system_info.memory, 2) if system_info.memory else 0.0} %')
        self.labels['gpu'].config(text=f'GPU Memory Used: {round(system_info.gpu_used / 1024**2, 2) if system_info.gpu_used else 0.0:.2f} MB / {round(system_info.gpu_total / 1024**2, 2) if system_info.gpu_total else 0.0:.2f} MB')

        current_position = self.hardware_display.yview()
        self.hardware_display.delete('1.0', tk.END)
        hardware_text = '\n'.join(f'{name}: {round(value, 2) if isinstance(value, float) else value}' for name, value in (system_info.hardware_info or {}).items())
        self.hardware_display.insert(tk.END, hardware_text)
        self.hardware_display.yview_moveto(current_position[0])
        self.after(1000, self.update_info)

def main():
    app = SystemMonitorApp()
    app.mainloop()

if __name__ == "__main__":
    main()