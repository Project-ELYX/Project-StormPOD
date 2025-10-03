#!/usr/bin/env python3
"""
StormPOD Main Application
------------------------
Run this to start the StormPOD weather monitoring system.
"""

import sys
import os

# Add the stormpod package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stormpod'))

import tkinter as tk
from gui_main import StormPODGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = StormPODGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🛑 StormPOD shutdown requested")
    except Exception as e:
        print(f"❌ StormPOD crashed: {e}")
        raise