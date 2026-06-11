# =====================================================================
# DBMS Mini Project: Renewable Energy Generation Tracking System
# Programming Language: Python 3
# GUI Framework: Tkinter & ttk
# Database: MySQL (with SQLite Auto-Fallback for safe college presentations)
# Design Concept: Premium Glassmorphism, 3D Hover-Lifts, Collapsible Sidebar,
#                 Animated Vector Charts, Reactive Focus Inputs, Light Theme.
# =====================================================================

import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Enable Windows DPI awareness for native, ultra-sharp fonts and canvas vector charts
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Try to import mysql connector, but handle failure gracefully
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# =====================================================================
# 1. DATABASE MANAGER (Resilient Connection Logic)
# =====================================================================
class DBManager:
    def __init__(self, workspace_dir="."):
        self.workspace_dir = workspace_dir
        self.db_path = os.path.join(workspace_dir, "renewable_energy.db")
        self.is_mysql = False
        self.conn = None
        self.connect()

    def connect(self):
        """Attempts to connect to MySQL; falls back to SQLite if offline."""
        if MYSQL_AVAILABLE:
            try:
                # First connect without database to ensure DB exists
                self.conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password=""
                )
                cursor = self.conn.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS renewable_energy_db")
                self.conn.commit()
                cursor.close()
                self.conn.close()

                # Reconnect to the database
                self.conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="renewable_energy_db"
                )
                self.is_mysql = True
                self.create_mysql_schema()
                self.seed_dummy_data()
                print("Connected to MySQL successfully!")
                return
            except Exception as e:
                print(f"MySQL connection failed: {e}. Falling back to SQLite...")
        else:
            print("MySQL Connector not installed. Falling back to SQLite...")

        # SQLite Fallback Mode
        self.is_mysql = False
        new_db = not os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;") # Enable Cascade Deletes in SQLite
        
        self.create_sqlite_schema()
        if new_db:
            self.seed_dummy_data()
        print("Connected to local SQLite database successfully!")

    def create_mysql_schema(self):
        """Creates tables, triggers, and stored procedures in MySQL."""
        cursor = self.conn.cursor()
        
        # Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id VARCHAR(50) PRIMARY KEY,
                device_name VARCHAR(100) NOT NULL,
                device_type ENUM('Solar', 'Wind', 'Hydro') NOT NULL,
                location VARCHAR(150) NOT NULL,
                installation_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'Active'
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                reading_id INT AUTO_INCREMENT PRIMARY KEY,
                device_id VARCHAR(50) NOT NULL,
                voltage DECIMAL(10,2) NOT NULL,
                current DECIMAL(10,2) NOT NULL,
                power DECIMAL(10,2) NOT NULL,
                reading_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
            );
        """)
        
        # Re-create Triggers (MySQL)
        try:
            cursor.execute("DROP TRIGGER IF EXISTS before_reading_insert;")
            cursor.execute("""
                CREATE TRIGGER before_reading_insert
                BEFORE INSERT ON energy_readings
                FOR EACH ROW
                BEGIN
                    SET NEW.power = NEW.voltage * NEW.current;
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS before_reading_update;")
            cursor.execute("""
                CREATE TRIGGER before_reading_update
                BEFORE UPDATE ON energy_readings
                FOR EACH ROW
                BEGIN
                    SET NEW.power = NEW.voltage * NEW.current;
                END;
            """)
        except Exception as trigger_err:
            print(f"Trigger creation skipped/failed: {trigger_err}")

        # Re-create Stored Procedures (MySQL)
        try:
            cursor.execute("DROP PROCEDURE IF EXISTS GetMonthlyEnergyReport;")
            cursor.execute("""
                CREATE PROCEDURE GetMonthlyEnergyReport(IN report_year INT)
                BEGIN
                    SELECT 
                        MONTHNAME(r.reading_time) AS Month,
                        d.device_type AS Device_Type,
                        COUNT(r.reading_id) AS Total_Readings,
                        ROUND(SUM(r.power), 2) AS Total_Power_Generated_W,
                        ROUND(AVG(r.voltage), 2) AS Avg_Voltage_V,
                        ROUND(AVG(r.current), 2) AS Avg_Current_A
                    FROM energy_readings r
                    JOIN devices d ON r.device_id = d.device_id
                    WHERE YEAR(r.reading_time) = report_year
                    GROUP BY MONTH(r.reading_time), d.device_type, MONTHNAME(r.reading_time)
                    ORDER BY MONTH(r.reading_time), d.device_type;
                END;
            """)
            
            cursor.execute("DROP PROCEDURE IF EXISTS GetDeviceWiseStats;")
            cursor.execute("""
                CREATE PROCEDURE GetDeviceWiseStats()
                BEGIN
                    SELECT 
                        d.device_id AS Device_ID,
                        d.device_name AS Device_Name,
                        d.device_type AS Device_Type,
                        d.location AS Location,
                        COUNT(r.reading_id) AS Total_Readings,
                        ROUND(COALESCE(SUM(r.power), 0), 2) AS Total_Power_W,
                        ROUND(COALESCE(AVG(r.power), 0), 2) AS Avg_Power_W
                    FROM devices d
                    LEFT JOIN energy_readings r ON d.device_id = r.device_id
                    GROUP BY d.device_id, d.device_name, d.device_type, d.location
                    ORDER BY Total_Power_W DESC;
                END;
            """)
        except Exception as proc_err:
            print(f"Stored Procedures creation skipped/failed: {proc_err}")
            
        self.conn.commit()
        cursor.close()

    def create_sqlite_schema(self):
        """Creates tables and trigger emulation in SQLite."""
        cursor = self.conn.cursor()
        
        # Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT NOT NULL,
                device_type TEXT CHECK(device_type IN ('Solar', 'Wind', 'Hydro')) NOT NULL,
                location TEXT NOT NULL,
                installation_date TEXT NOT NULL,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Maintenance'))
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                voltage REAL NOT NULL,
                current REAL NOT NULL,
                power REAL,
                reading_time TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
            );
        """)
        
        # Create Triggers (SQLite - Removed 'sqlite_' reserved prefix)
        cursor.execute("DROP TRIGGER IF EXISTS calculate_power_insert;")
        cursor.execute("""
            CREATE TRIGGER calculate_power_insert
            AFTER INSERT ON energy_readings
            BEGIN
                UPDATE energy_readings 
                SET power = voltage * current 
                WHERE reading_id = new.reading_id;
            END;
        """)
        
        cursor.execute("DROP TRIGGER IF EXISTS calculate_power_update;")
        cursor.execute("""
            CREATE TRIGGER calculate_power_update
            AFTER UPDATE ON energy_readings
            BEGIN
                UPDATE energy_readings 
                SET power = voltage * current 
                WHERE reading_id = new.reading_id;
            END;
        """)
        
        self.conn.commit()
        cursor.close()

    def seed_dummy_data(self):
        """Seeds databases with initial mock records for presentation preview."""
        devices = self.get_all_devices()
        if len(devices) > 0:
            return

        cursor = self.conn.cursor()
        
        sample_devices = [
            ('SOL-001', 'Solar Panel Array Alpha', 'Solar', 'Rooftop Block A', '2025-01-15', 'Active'),
            ('SOL-002', 'Solar Tracker Beta', 'Solar', 'South Campus Field', '2025-03-10', 'Active'),
            ('WND-001', 'Wind Turbine Helix-1', 'Wind', 'East Windy Ridge', '2024-11-20', 'Active'),
            ('WND-002', 'Wind Turbine Helix-2', 'Wind', 'East Windy Ridge', '2025-02-18', 'Maintenance'),
            ('HYD-001', 'Hydro Micro-Turbine H1', 'Hydro', 'Campus Stream Fall', '2025-04-05', 'Active')
        ]
        
        for dev in sample_devices:
            if self.is_mysql:
                cursor.execute("""
                    INSERT IGNORE INTO devices (device_id, device_name, device_type, location, installation_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, dev)
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO devices (device_id, device_name, device_type, location, installation_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, dev)

        sample_readings = [
            # Jan
            ('SOL-001', 220.5, 4.2, '2026-01-10 12:00:00'),
            ('WND-001', 110.2, 8.5, '2026-01-10 14:00:00'),
            # Feb
            ('SOL-001', 222.0, 5.0, '2026-02-15 12:30:00'),
            ('WND-001', 108.5, 9.2, '2026-02-15 15:00:00'),
            ('SOL-002', 215.8, 3.8, '2026-02-16 11:00:00'),
            # Mar
            ('SOL-001', 218.0, 4.8, '2026-03-20 13:00:00'),
            ('WND-001', 112.4, 7.8, '2026-03-20 16:30:00'),
            ('SOL-002', 220.0, 5.2, '2026-03-21 11:30:00'),
            ('WND-002', 110.0, 6.0, '2026-03-22 10:00:00'),
            # Apr
            ('SOL-001', 224.2, 5.5, '2026-04-25 12:00:00'),
            ('SOL-002', 225.0, 6.1, '2026-04-25 13:00:00'),
            ('WND-001', 115.0, 10.5, '2026-04-26 14:30:00'),
            ('HYD-001', 230.0, 8.0, '2026-04-28 09:00:00'),
            # May (Today)
            ('SOL-001', 221.0, 4.9, '2026-05-24 10:00:00'),
            ('SOL-002', 223.5, 5.4, '2026-05-24 11:00:00'),
            ('WND-001', 113.8, 9.0, '2026-05-24 12:30:00'),
            ('HYD-001', 228.4, 7.5, '2026-05-24 14:00:00')
        ]
        
        for rd in sample_readings:
            if self.is_mysql:
                cursor.execute("""
                    INSERT INTO energy_readings (device_id, voltage, current, power, reading_time)
                    VALUES (%s, %s, %s, 0.0, %s)
                """, rd)
            else:
                cursor.execute("""
                    INSERT INTO energy_readings (device_id, voltage, current, power, reading_time)
                    VALUES (?, ?, ?, 0.0, ?)
                """, rd)

        self.conn.commit()
        cursor.close()

    # CRUD & QUERY API
    def add_device(self, device_id, name, dev_type, location, inst_date):
        cursor = self.conn.cursor()
        try:
            if self.is_mysql:
                cursor.execute("""
                    INSERT INTO devices (device_id, device_name, device_type, location, installation_date, status)
                    VALUES (%s, %s, %s, %s, %s, 'Active')
                """, (device_id, name, dev_type, location, inst_date))
            else:
                cursor.execute("""
                    INSERT INTO devices (device_id, device_name, device_type, location, installation_date, status)
                    VALUES (?, ?, ?, ?, ?, 'Active')
                """, (device_id, name, dev_type, location, inst_date))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add device: {e}")
            return False
        finally:
            cursor.close()

    def get_all_devices(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT device_id, device_name, device_type, location, installation_date, status FROM devices ORDER BY device_id")
        rows = cursor.fetchall()
        cursor.close()
        return [{'device_id': r[0], 'device_name': r[1], 'device_type': r[2], 'location': r[3], 'installation_date': str(r[4]), 'status': r[5]} for r in rows]

    def update_device(self, device_id, name, dev_type, location, status):
        cursor = self.conn.cursor()
        try:
            if self.is_mysql:
                cursor.execute("""
                    UPDATE devices SET device_name=%s, device_type=%s, location=%s, status=%s WHERE device_id=%s
                """, (name, dev_type, location, status, device_id))
            else:
                cursor.execute("""
                    UPDATE devices SET device_name=?, device_type=?, location=?, status=? WHERE device_id=?
                """, (name, dev_type, location, status, device_id))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update device: {e}")
            return False
        finally:
            cursor.close()

    def delete_device(self, device_id):
        cursor = self.conn.cursor()
        try:
            if self.is_mysql:
                cursor.execute("DELETE FROM devices WHERE device_id=%s", (device_id,))
            else:
                cursor.execute("DELETE FROM devices WHERE device_id=?", (device_id,))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete device: {e}")
            return False
        finally:
            cursor.close()

    def add_reading(self, device_id, voltage, current, reading_time=None):
        cursor = self.conn.cursor()
        try:
            if not reading_time:
                reading_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.is_mysql:
                cursor.execute("""
                    INSERT INTO energy_readings (device_id, voltage, current, power, reading_time)
                    VALUES (%s, %s, %s, 0.0, %s)
                """, (device_id, voltage, current, reading_time))
            else:
                cursor.execute("""
                    INSERT INTO energy_readings (device_id, voltage, current, power, reading_time)
                    VALUES (?, ?, ?, 0.0, ?)
                """, (device_id, voltage, current, reading_time))
            self.conn.commit()
            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to log reading: {e}")
            return False
        finally:
            cursor.close()

    def get_recent_readings(self, limit=7):
        cursor = self.conn.cursor()
        query = """
            SELECT r.reading_id, r.device_id, d.device_name, d.device_type, r.voltage, r.current, r.power, r.reading_time
            FROM energy_readings r
            JOIN devices d ON r.device_id = d.device_id
            ORDER BY r.reading_time DESC, r.reading_id DESC
            LIMIT %s
        """ if self.is_mysql else """
            SELECT r.reading_id, r.device_id, d.device_name, d.device_type, r.voltage, r.current, r.power, r.reading_time
            FROM energy_readings r
            JOIN devices d ON r.device_id = d.device_id
            ORDER BY r.reading_time DESC, r.reading_id DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        
        return [{
            'reading_id': r[0],
            'device_id': r[1],
            'device_name': r[2],
            'device_type': r[3],
            'voltage': float(r[4]),
            'current': float(r[5]),
            'power': float(r[6]) if r[6] is not None else float(r[4]) * float(r[5]),
            'reading_time': str(r[7])
        } for r in rows]

    def get_dashboard_kpis(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM devices")
        total_devices = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'Active'")
        active_devices = cursor.fetchone()[0]
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if self.is_mysql:
            cursor.execute("SELECT SUM(power) FROM energy_readings WHERE DATE(reading_time) = %s", (today,))
        else:
            cursor.execute("SELECT SUM(power) FROM energy_readings WHERE date(reading_time) = ?", (today,))
        total_today_power = cursor.fetchone()[0]
        total_today_power = float(total_today_power) if total_today_power else 0.0

        cursor.close()
        return {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'total_today_power': round(total_today_power, 1)
        }

    def get_device_wise_stats(self):
        if self.is_mysql:
            cursor = self.conn.cursor()
            try:
                cursor.callproc('GetDeviceWiseStats')
                results = []
                for result in cursor.stored_results():
                    results.extend(result.fetchall())
                cursor.close()
                return [{
                    'Device_ID': r[0], 'Device_Name': r[1], 'Device_Type': r[2], 
                    'Location': r[3], 'Total_Readings': r[4], 
                    'Total_Power_W': float(r[5]), 'Avg_Power_W': float(r[6])
                } for r in results]
            except Exception as e:
                print(f"MySQL stats procedure failed: {e}")
                cursor.close()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                d.device_id, d.device_name, d.device_type, d.location,
                COUNT(r.reading_id) as total_readings,
                ROUND(COALESCE(SUM(r.power), 0), 2) as total_power,
                ROUND(COALESCE(AVG(r.power), 0), 2) as avg_power
            FROM devices d
            LEFT JOIN energy_readings r ON d.device_id = r.device_id
            GROUP BY d.device_id
            ORDER BY total_power DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [{
            'Device_ID': r[0], 'Device_Name': r[1], 'Device_Type': r[2], 
            'Location': r[3], 'Total_Readings': r[4], 
            'Total_Power_W': float(r[5]), 'Avg_Power_W': float(r[6])
        } for r in rows]

    def get_monthly_energy_report(self, year=2026):
        if self.is_mysql:
            cursor = self.conn.cursor()
            try:
                cursor.callproc('GetMonthlyEnergyReport', [year])
                results = []
                for result in cursor.stored_results():
                    results.extend(result.fetchall())
                cursor.close()
                return [{
                    'Month': r[0], 'Device_Type': r[1], 'Total_Readings': r[2], 
                    'Total_Power_W': float(r[3]), 'Avg_Voltage_V': float(r[4]), 'Avg_Current_A': float(r[5])
                } for r in results]
            except Exception as e:
                print(f"MySQL monthly procedure failed: {e}")
                cursor.close()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%m', r.reading_time) AS month_num,
                d.device_type,
                COUNT(r.reading_id),
                SUM(r.power),
                AVG(r.voltage),
                AVG(r.current)
            FROM energy_readings r
            JOIN devices d ON r.device_id = d.device_id
            WHERE strftime('%Y', r.reading_time) = ?
            GROUP BY month_num, d.device_type
            ORDER BY month_num, d.device_type
        """, (str(year),))
        rows = cursor.fetchall()
        cursor.close()

        months_map = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        return [{
            'Month': months_map.get(r[0], r[0]),
            'Device_Type': r[1],
            'Total_Readings': r[2],
            'Total_Power_W': round(float(r[3]), 2) if r[3] else 0.0,
            'Avg_Voltage_V': round(float(r[4]), 2) if r[4] else 0.0,
            'Avg_Current_A': round(float(r[5]), 2) if r[5] else 0.0
        } for r in rows]

    def query_readings_report(self, device_id=None, device_type=None, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        query = """
            SELECT r.reading_id, r.device_id, d.device_name, d.device_type, r.voltage, r.current, r.power, r.reading_time
            FROM energy_readings r
            JOIN devices d ON r.device_id = d.device_id
            WHERE 1=1
        """
        params = []
        if device_id and device_id != "All Devices":
            query += " AND r.device_id = %s" if self.is_mysql else " AND r.device_id = ?"
            params.append(device_id)
        if device_type and device_type != "All Types":
            query += " AND d.device_type = %s" if self.is_mysql else " AND d.device_type = ?"
            params.append(device_type)
        if start_date:
            query += " AND DATE(r.reading_time) >= %s" if self.is_mysql else " AND DATE(r.reading_time) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(r.reading_time) <= %s" if self.is_mysql else " AND DATE(r.reading_time) <= ?"
            params.append(end_date)
            
        query += " ORDER BY r.reading_time DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        
        return [{
            'reading_id': r[0], 'device_id': r[1], 'device_name': r[2], 'device_type': r[3],
            'voltage': float(r[4]), 'current': float(r[5]),
            'power': float(r[6]) if r[6] is not None else float(r[4]) * float(r[5]),
            'reading_time': str(r[7])
        } for r in rows]


# =====================================================================
# 2. PREMIUM UI WIDGETS (Glassmorphic Rounded Cards & Active Inputs)
# =====================================================================

class GlassCard(tk.Canvas):
    """Premium container utilizing mathematical rounded rectangles and high-performance static layouts."""
    def __init__(self, parent, bg="#F8FAFC", card_bg="#FFFFFF", border_color="#E2E8F0", radius=16, shadow_color="#E8ECEF", **kwargs):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.bg = bg
        self.card_bg = card_bg
        self.border_color = border_color
        self.radius = radius
        self.shadow_color = shadow_color
        
        self.frame = tk.Frame(self, bg=card_bg)
        self.window_id = self.create_window(0, 0, window=self.frame, anchor="nw")
        
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.draw_card()

    def on_enter(self, event):
        pass

    def on_leave(self, event):
        pass

    def update_hover_recursive(self):
        pass

    def draw_card(self):
        self.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 20 or h < 20: return
        
        r = self.radius
        
        # Beautiful static glassmorphic style with premium soft shadow and clean border
        if self.shadow_color:
            self.draw_rounded_rect(3, 4, w-2, h-2, r, fill=self.shadow_color, outline="")
        self.draw_rounded_rect(0, 0, w-3, h-3, r, fill=self.card_bg, outline=self.border_color)
        
        # Smoothly move and resize the existing window item without layout-thrashing recreation
        self.coords(self.window_id, r, r)
        self.itemconfig(self.window_id, width=w-2*r-3, height=h-2*r-3)

    def draw_rounded_rect(self, x1, y1, x2, y2, r, fill="", outline="", width=1):
        # Arcs
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=fill, outline="", style="pieslice", tags="bg")
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=fill, outline="", style="pieslice", tags="bg")
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=fill, outline="", style="pieslice", tags="bg")
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=fill, outline="", style="pieslice", tags="bg")
        # Rectangles
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline="", width=0, tags="bg")
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline="", width=0, tags="bg")
        
        if outline:
            self.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width, tags="bg")
            self.create_line(x1+r, y2, x2-r, y2, fill=outline, width=width, tags="bg")
            self.create_line(x1, y1+r, x1, y2-r, fill=outline, width=width, tags="bg")
            self.create_line(x2, y1+r, x2, y2-r, fill=outline, width=width, tags="bg")


class ModernButton(tk.Button):
    """Sleek flat action button supporting interactive colors and click events."""
    def __init__(self, parent, text, command, bg_color="#10B981", fg_color="#FFFFFF", hover_color="#059669", **kwargs):
        super().__init__(
            parent, text=text, command=command, bg=bg_color, fg=fg_color, 
            activebackground=hover_color, activeforeground=fg_color,
            font=("Segoe UI Semibold", 9), bd=0, relief="flat", cursor="hand2",
            padx=16, pady=8, **kwargs
        )
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))


def make_modern_input(parent, label_text, var, placeholder=""):
    """Helper creating reactive inputs that glow emerald when active."""
    frame = tk.Frame(parent, bg="#FFFFFF")
    
    lbl = tk.Label(frame, text=label_text, font=("Segoe UI Semibold", 9), fg="#64748B", bg="#FFFFFF", anchor="w")
    lbl.pack(fill="x", pady=(3, 1))
    
    border_frame = tk.Frame(frame, bg="#E2E8F0", bd=0, padx=1, pady=1)
    border_frame.pack(fill="x")
    
    ent = tk.Entry(border_frame, textvariable=var, font=("Segoe UI", 10), bg="#F8FAFC", fg="#0F172A", bd=0, relief="flat")
    ent.pack(fill="x", ipady=3, padx=8, pady=2)
    
    def on_focus_in(e):
        border_frame.config(bg="#10B981") # Glowing green border
        ent.config(bg="#FFFFFF")
        
    def on_focus_out(e):
        border_frame.config(bg="#E2E8F0") # Slate baseline
        ent.config(bg="#F8FAFC")
        
    ent.bind("<FocusIn>", on_focus_in)
    ent.bind("<FocusOut>", on_focus_out)
    
    return frame, ent


def make_badge(parent, text, type_key):
    """Outputs styled state pills (e.g. Active, Maintenance, Technology icons)."""
    color_map = {
        "Active": ("#D1FAE5", "#065F46"),      # Soft emerald green
        "Inactive": ("#F3F4F6", "#374151"),    # Soft slate gray
        "Maintenance": ("#FEF3C7", "#92400E"), # Soft amber orange
        "Solar": ("#ECFDF5", "#047857"),
        "Wind": ("#EFF6FF", "#1D4ED8"),
        "Hydro": ("#FFFBEB", "#B45309")
    }
    bg, fg = color_map.get(type_key, ("#F3F4F6", "#374151"))
    
    frame = tk.Frame(parent, bg=bg, padx=8, pady=3, bd=0)
    lbl = tk.Label(frame, text=text, font=("Segoe UI Semibold", 8), fg=fg, bg=bg)
    lbl.pack()
    return frame


# =====================================================================
# 3. ANIMATED VECTOR GRAPHICS (Left-to-Right traces and column growth)
# =====================================================================

class CanvasLineChart(tk.Canvas):
    """Renders visual telemetry path lines with left-to-right trace animations."""
    def __init__(self, parent, width=480, height=220, bg="#FFFFFF", line_color="#10B981", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.line_color = line_color
        self.width = width
        self.height = height

    def plot_data(self, data, x_labels, title="Energy Generation Trend (Watts)"):
        self.delete("all")
        
        if not data:
            self.create_text(self.width/2, self.height/2, text="No readings logged for today", font=("Segoe UI", 10, "italic"), fill="#64748B")
            return

        self.create_text(self.width/2, 15, text=title, font=("Segoe UI Semibold", 10), fill="#0F172A")
        
        self.margin_left = 40
        self.margin_right = 20
        self.margin_top = 40
        self.margin_bottom = 30
        
        self.plot_w = self.width - self.margin_left - self.margin_right
        self.plot_h = self.height - self.margin_top - self.margin_bottom
        
        max_val = max(data) if max(data) > 0 else 100
        max_val = ((max_val // 50) + 1) * 50 if max_val > 50 else ((max_val // 10) + 1) * 10
        min_val = 0
        val_range = max_val - min_val
        
        # Grid lines
        ticks = 4
        for i in range(ticks + 1):
            val = min_val + (val_range / ticks) * i
            y = self.margin_top + self.plot_h - (self.plot_h / ticks) * i
            self.create_line(self.margin_left, y, self.width - self.margin_right, y, fill="#F1F5F9", width=1)
            self.create_text(self.margin_left - 8, y, text=f"{int(val)}W", font=("Segoe UI Semibold", 7), fill="#94A3B8", anchor="e")

        # Map Coordinates
        self.points = []
        n_points = len(data)
        dx = self.plot_w / (n_points - 1) if n_points > 1 else self.plot_w
        
        for idx, val in enumerate(data):
            x = self.margin_left + idx * dx if n_points > 1 else self.margin_left + self.plot_w/2
            y = self.margin_top + self.plot_h - ((val - min_val) / val_range) * self.plot_h
            self.points.append((x, y))
            
            # X Labels
            if n_points <= 7 or idx % (n_points // 5 + 1) == 0:
                lbl = x_labels[idx]
                if len(lbl) > 8: lbl = lbl[:6] + ".."
                self.create_text(x, self.height - self.margin_bottom + 12, text=lbl, font=("Segoe UI Semibold", 7), fill="#94A3B8", anchor="n")

        # Baseline axis
        self.create_line(self.margin_left, self.margin_top + self.plot_h, self.width - self.margin_right, self.margin_top + self.plot_h, fill="#E2E8F0", width=1.5)
        
        # Start Trace Animation
        self.animate_index = 2
        self.animate_data = data
        self.animate_line()

    def animate_line(self):
        self.delete("chart_line")
        self.delete("chart_area")
        
        if len(self.points) < 2: return
        
        coords = []
        for i in range(self.animate_index):
            coords.extend(self.points[i])
            
        # Draw gradient area
        area_coords = [self.points[0][0], self.margin_top + self.plot_h]
        for i in range(self.animate_index):
            area_coords.extend(self.points[i])
        area_coords.extend([self.points[self.animate_index - 1][0], self.margin_top + self.plot_h])
        
        self.create_polygon(area_coords, fill="#ECFDF5" if self.line_color == "#10B981" else "#EFF6FF", outline="", tags="chart_area")
        self.create_line(coords, fill=self.line_color, width=3, smooth=True, tags="chart_line")
        
        if self.animate_index < len(self.points):
            self.animate_index += 1
            self.after(20, self.animate_line)
        else:
            # Draw point highlights once trace finishes
            self.draw_points()

    def draw_points(self):
        for idx, p in enumerate(self.points):
            self.create_oval(p[0]-4, p[1]-4, p[0]+4, p[1]+4, fill="#FFFFFF", outline=self.line_color, width=2)
            val = self.animate_data[idx]
            
            hover_oval = self.create_oval(p[0]-6, p[1]-6, p[0]+6, p[1]+6, fill="", outline="")
            self.tag_bind(hover_oval, "<Enter>", lambda e, val=val, p=p: self.show_tooltip(val, p))
            self.tag_bind(hover_oval, "<Leave>", lambda e: self.hide_tooltip())

    def show_tooltip(self, val, pos):
        self.config(cursor="hand2")
        self.delete("tooltip")
        x, y = pos
        self.create_rectangle(x - 22, y - 25, x + 22, y - 5, fill="#0F172A", outline="", tags="tooltip")
        self.create_text(x, y - 15, text=f"{val:.1f}W", fill="#FFFFFF", font=("Segoe UI Semibold", 8), tags="tooltip")

    def hide_tooltip(self):
        self.config(cursor="")
        self.delete("tooltip")


class CanvasBarChart(tk.Canvas):
    """Renders visual aggregate statistics that rise smoothly from 0 on load."""
    def __init__(self, parent, width=480, height=220, bg="#FFFFFF", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height

    def plot_bars(self, values, categories, title="Energy Generated by Device Type (Wh)"):
        self.delete("all")
        
        if not values:
            self.create_text(self.width/2, self.height/2, text="No analytical telemetry logged yet", font=("Segoe UI", 10, "italic"), fill="#64748B")
            return

        self.create_text(self.width/2, 15, text=title, font=("Segoe UI Semibold", 10), fill="#0F172A")
        
        self.margin_left = 45
        self.margin_right = 20
        self.margin_top = 40
        self.margin_bottom = 30
        
        self.plot_w = self.width - self.margin_left - self.margin_right
        self.plot_h = self.height - self.margin_top - self.margin_bottom
        
        max_val = max(values) if max(values) > 0 else 100
        max_val = ((max_val // 100) + 1) * 100 if max_val > 100 else ((max_val // 10) + 1) * 10
        min_val = 0
        val_range = max_val - min_val
        
        # Grid lines
        ticks = 4
        for i in range(ticks + 1):
            val = min_val + (val_range / ticks) * i
            y = self.margin_top + self.plot_h - (self.plot_h / ticks) * i
            self.create_line(self.margin_left, y, self.width - self.margin_right, y, fill="#F1F5F9", width=1)
            self.create_text(self.margin_left - 8, y, text=f"{int(val)}", font=("Segoe UI Semibold", 7), fill="#94A3B8", anchor="e")

        # Map Bar Parameters
        self.bars_data = []
        n_bars = len(values)
        bar_gap = 15
        total_gaps = bar_gap * (n_bars + 1)
        bar_w = (self.plot_w - total_gaps) / n_bars
        
        colors = ["#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899"]
        
        for idx, val in enumerate(values):
            x1 = self.margin_left + bar_gap + idx * (bar_w + bar_gap)
            y_target = self.margin_top + self.plot_h - ((val - min_val) / val_range) * self.plot_h
            x2 = x1 + bar_w
            baseline_y = self.margin_top + self.plot_h
            
            color = colors[idx % len(colors)]
            hover_color = self.lighten_color(color)
            
            self.bars_data.append((x1, y_target, x2, baseline_y, color, hover_color, val, categories[idx]))

        self.create_line(self.margin_left, self.margin_top + self.plot_h, self.width - self.margin_right, self.margin_top + self.plot_h, fill="#E2E8F0", width=1.5)
        
        # Start Grow Animation
        self.animate_step = 0
        self.animate_bars()

    def animate_bars(self):
        self.delete("chart_bars")
        self.delete("chart_labels")
        
        progress = self.animate_step / 15.0 # 15 frames grow path
        
        for idx, (x1, y_target, x2, baseline_y, color, hover_color, val, cat) in enumerate(self.bars_data):
            total_height = baseline_y - y_target
            current_y = baseline_y - (total_height * progress)
            
            bar_tag = f"bar_{idx}"
            self.create_rectangle(x1, current_y, x2, baseline_y, fill=color, outline="", tags=("chart_bars", bar_tag))
            
            if self.animate_step >= 15:
                # Value label
                self.create_text((x1+x2)/2, y_target - 8, text=f"{int(val)}", font=("Segoe UI Semibold", 8), fill="#0F172A", tags="chart_labels")
                # Category label
                self.create_text((x1+x2)/2, self.height - self.margin_bottom + 12, text=cat, font=("Segoe UI Semibold", 7), fill="#94A3B8", anchor="n", tags="chart_labels")
                
                # Dynamic bar hover binds
                self.tag_bind(bar_tag, "<Enter>", lambda e, tag=bar_tag, hc=hover_color: self.itemconfig(tag, fill=hc))
                self.tag_bind(bar_tag, "<Leave>", lambda e, tag=bar_tag, c=color: self.itemconfig(tag, fill=c))
                
        if self.animate_step < 15:
            self.animate_step += 1
            self.after(15, self.animate_bars)

    def lighten_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        light_rgb = tuple(min(255, int(c + (255 - c) * 0.4)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*light_rgb)


# =====================================================================
# 4. MAIN COLLAPSIBLE SIDEBAR STRUCTURE
# =====================================================================

class RenewableEnergyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("EcoStream - Renewable Energy generation tracker")
        self.geometry("1024x660")
        self.minsize(980, 600)
        self.configure(bg="#F8FAFC")
        
        self.db = DBManager(workspace_dir=".")
        
        # Clean ttk structures
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview", font=("Segoe UI", 9), rowheight=30, 
            background="#FFFFFF", fieldbackground="#FFFFFF", borderwidth=0
        )
        self.style.map("Treeview", 
            background=[("selected", "#D1FAE5"), ("active", "#F1F5F9")],
            foreground=[("selected", "#065F46")]
        )
        self.style.configure(
            "Treeview.Heading", font=("Segoe UI Semibold", 9), 
            background="#F8FAFC", foreground="#64748B", borderwidth=0
        )
        
        # Primary grid division (Sidebar left, Pages right)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.sidebar_expanded = True
        
        self.create_sidebar()
        self.create_main_container()
        
        self.show_page("dashboard")

    def create_sidebar(self):
        """Creates collapsible white sidebar container with dynamic sliding width."""
        self.sidebar_frame = tk.Frame(self, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1, width=220)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        
        # Toggle and Header Frame
        header_box = tk.Frame(self.sidebar_frame, bg="#FFFFFF")
        header_box.pack(fill="x", padx=15, pady=(20, 15))
        
        # Sliding Logo
        self.logo_lbl = tk.Label(header_box, text="⚡ EcoStream", font=("Segoe UI", 16, "bold"), fg="#10B981", bg="#FFFFFF")
        self.logo_lbl.pack(side="left")
        
        # Hamburger toggle button
        self.btn_toggle = tk.Button(
            header_box, text="☰", font=("Segoe UI Semibold", 12), 
            fg="#64748B", bg="#FFFFFF", activebackground="#F1F5F9", 
            bd=0, relief="flat", cursor="hand2", command=self.toggle_sidebar
        )
        self.btn_toggle.pack(side="right")
        
        # Subtitle wrapper
        self.sub_lbl = tk.Label(self.sidebar_frame, text="Generation Telemetry Dashboard", font=("Segoe UI Light", 8), fg="#94A3B8", bg="#FFFFFF")
        self.sub_lbl.pack(anchor="w", padx=20, pady=(0, 20))
        
        self.nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("add_device", "➕", "Register Device"),
            ("add_reading", "⚡", "Log Telemetry"),
            ("reports", "📈", "Reports & Charts"),
            ("device_admin", "⚙️", "Device Admin")
        ]
        
        self.nav_buttons = {}
        
        for key, icon, name in self.nav_items:
            btn_frame = tk.Frame(self.sidebar_frame, bg="#FFFFFF", height=44)
            btn_frame.pack(fill="x", padx=12, pady=3)
            btn_frame.pack_propagate(False)
            
            # Selection indicator
            indicator = tk.Frame(btn_frame, bg="#FFFFFF", width=4)
            indicator.pack(side="left", fill="y")
            
            btn = tk.Button(
                btn_frame, text=f"{icon}   {name}", font=("Segoe UI Semibold", 9), 
                fg="#64748B", bg="#FFFFFF", activebackground="#F1F5F9", 
                activeforeground="#10B981", bd=0, relief="flat", anchor="w", 
                padx=15, cursor="hand2", command=lambda k=key: self.show_page(k)
            )
            btn.pack(side="right", fill="both", expand=True)
            
            self.nav_buttons[key] = {
                'frame': btn_frame,
                'btn': btn,
                'indicator': indicator,
                'icon': icon,
                'name': name
            }
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#F8FAFC"))
            btn.bind("<Leave>", lambda e, b=btn, k=key: self.reset_nav_leave(k, b))

        self.credit_lbl = tk.Label(
            self.sidebar_frame, text="DBMS Mini-Project v2.0", 
            font=("Segoe UI Semibold", 7), fg="#94A3B8", bg="#FFFFFF"
        )
        self.credit_lbl.pack(side="bottom", pady=15)

    def toggle_sidebar(self):
        """Triggers the collapsible width slide transition."""
        self.sidebar_expanded = not self.sidebar_expanded
        self.logo_lbl.pack_forget()
        self.sub_lbl.pack_forget()
        self.credit_lbl.pack_forget()
        self.animate_sidebar()

    def animate_sidebar(self):
        curr_w = self.sidebar_frame.winfo_width()
        target_w = 220 if self.sidebar_expanded else 65
        diff = target_w - curr_w
        
        if abs(diff) > 2:
            step = 25 if diff > 0 else -25
            new_w = curr_w + step
            if (diff > 0 and new_w > target_w) or (diff < 0 and new_w < target_w):
                new_w = target_w
            self.sidebar_frame.config(width=new_w)
            self.after(12, self.animate_sidebar)
        else:
            self.sidebar_frame.config(width=target_w)
            self.complete_sidebar_layout()

    def complete_sidebar_layout(self):
        if self.sidebar_expanded:
            self.logo_lbl.config(text="⚡ EcoStream")
            self.logo_lbl.pack(side="left")
            self.sub_lbl.pack(anchor="w", padx=20, pady=(0, 20))
            self.credit_lbl.config(text="DBMS Mini-Project v2.0")
            self.credit_lbl.pack(side="bottom", pady=15)
            
            for key, widgets in self.nav_buttons.items():
                widgets['btn'].config(text=f"{widgets['icon']}   {widgets['name']}", anchor="w", padx=15)
        else:
            self.logo_lbl.config(text="⚡")
            self.logo_lbl.pack(side="left")
            self.credit_lbl.config(text="v2.0")
            self.credit_lbl.pack(side="bottom", pady=15)
            
            for key, widgets in self.nav_buttons.items():
                widgets['btn'].config(text=widgets['icon'], anchor="center", padx=0)
                
        self.show_page(getattr(self, "current_page_key", "dashboard"))

    def reset_nav_leave(self, key, btn):
        if getattr(self, "current_page_key", "") == key:
            btn.config(bg="#ECFDF5")
        else:
            btn.config(bg="#FFFFFF")

    def create_main_container(self):
        self.main_container = tk.Frame(self, bg="#F8FAFC")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=1)
        
        # Header Section
        self.header_frame = tk.Frame(self.main_container, bg="#F8FAFC", height=70)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 0))
        self.header_frame.columnconfigure(0, weight=1)
        
        self.title_var = tk.StringVar(value="Renewable Energy Dashboard")
        self.header_lbl = tk.Label(
            self.header_frame, textvariable=self.title_var, 
            font=("Segoe UI", 18, "bold"), fg="#0F172A", bg="#F8FAFC", anchor="w"
        )
        self.header_lbl.grid(row=0, column=0, sticky="w")
        
        self.db_status_frame = tk.Frame(self.header_frame, bg="#ECFDF5", padx=12, pady=6, highlightbackground="#D1FAE5", highlightthickness=1)
        self.db_status_frame.grid(row=0, column=1, sticky="e")
        
        self.db_status_lbl = tk.Label(
            self.db_status_frame, 
            text="● Live Database Mode (MySQL)" if self.db.is_mysql else "● Sandbox Mode (SQLite Fallback)",
            font=("Segoe UI Semibold", 8), 
            fg="#047857" if self.db.is_mysql else "#D97706",
            bg="#ECFDF5" if self.db.is_mysql else "#FEF3C7"
        )
        self.db_status_lbl.pack()
        self.db_status_frame.config(
            bg="#ECFDF5" if self.db.is_mysql else "#FEF3C7",
            highlightbackground="#D1FAE5" if self.db.is_mysql else "#FDE68A"
        )
        
        sep = tk.Frame(self.main_container, bg="#E2E8F0", height=1)
        sep.grid(row=0, column=0, sticky="ew", padx=30, pady=(68, 0))

        self.page_container = tk.Frame(self.main_container, bg="#F8FAFC")
        self.page_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)

    def show_page(self, key):
        self.current_page_key = key
        
        title_map = {
            "dashboard": "Renewable Energy Dashboard",
            "add_device": "Register Generation Device",
            "add_reading": "Telemetry Readings Log",
            "reports": "Analytical Reports & Trends",
            "device_admin": "Device System Administrator"
        }
        self.title_var.set(title_map.get(key, "EcoStream"))
        
        for k, widgets in self.nav_buttons.items():
            if k == key:
                widgets['frame'].config(bg="#ECFDF5")
                widgets['btn'].config(bg="#ECFDF5", fg="#10B981")
                widgets['indicator'].config(bg="#10B981")
            else:
                widgets['frame'].config(bg="#FFFFFF")
                widgets['btn'].config(bg="#FFFFFF", fg="#64748B")
                widgets['indicator'].config(bg="#FFFFFF")
                
        for p in self.page_container.winfo_children():
            p.destroy()
            
        if key == "dashboard":
            frame = DashboardPage(self.page_container, self)
        elif key == "add_device":
            frame = AddDevicePage(self.page_container, self)
        elif key == "add_reading":
            frame = AddReadingPage(self.page_container, self)
        elif key == "reports":
            frame = ReportsPage(self.page_container, self)
        elif key == "device_admin":
            frame = DeviceAdminPage(self.page_container, self)
            
        frame.pack(fill="both", expand=True)


# =====================================================================
# 5. REDESIGNED DASHBOARD PAGE (3D Hover cards and custom lines)
# =====================================================================

class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F8FAFC")
        self.controller = controller
        self.db = controller.db
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        kpis = self.db.get_dashboard_kpis()
        
        # 1. Stat KPI Cards Section
        kpis_frame = tk.Frame(self, bg="#F8FAFC")
        kpis_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        for i in range(3):
            kpis_frame.columnconfigure(i, weight=1)
            
        # KPI 1: Total Devices
        c1 = GlassCard(kpis_frame, height=110)
        c1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.setup_kpi_card(c1, "Total Devices Registered", str(kpis['total_devices']), "⚙️", "#3B82F6")
        
        # KPI 2: Active Generators
        c2 = GlassCard(kpis_frame, height=110)
        c2.grid(row=0, column=1, padx=5, sticky="nsew")
        self.setup_kpi_card(c2, "Active System Generators", f"{kpis['active_devices']} / {kpis['total_devices']}", "🌱", "#10B981")
        
        # KPI 3: Today's Power
        c3 = GlassCard(kpis_frame, height=110)
        c3.grid(row=0, column=2, padx=(10, 0), sticky="nsew")
        self.setup_kpi_card(c3, "Total Generation Today", f"{kpis['total_today_power']} W", "⚡", "#F59E0B")

        # 2. Charts and Lists Panels
        bottom_frame = tk.Frame(self, bg="#F8FAFC")
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        bottom_frame.columnconfigure(0, weight=3)
        bottom_frame.columnconfigure(1, weight=2)
        bottom_frame.rowconfigure(0, weight=1)
        
        # Left Panel: Trend Chart
        chart_card = GlassCard(bottom_frame, height=310)
        chart_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        self.trend_chart = CanvasLineChart(chart_card.frame, width=420, height=230)
        self.trend_chart.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right Panel: Recent Readings
        readings_card = GlassCard(bottom_frame, height=310)
        readings_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        lbl_card_title = tk.Label(readings_card.frame, text="Recent Telemetry logs", font=("Segoe UI Semibold", 10), fg="#0F172A", bg="#FFFFFF")
        lbl_card_title.pack(anchor="w", padx=5, pady=(5, 10))
        
        self.list_frame = tk.Frame(readings_card.frame, bg="#FFFFFF")
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.populate_recent_readings()
        self.plot_dashboard_chart()
        
        # Tracing recursive hovers
        c1.update_hover_recursive()
        c2.update_hover_recursive()
        c3.update_hover_recursive()
        chart_card.update_hover_recursive()
        readings_card.update_hover_recursive()

    def setup_kpi_card(self, card, title, value, icon, color):
        content = card.frame
        content.columnconfigure(0, weight=1)
        
        # Layout details
        lbl_title = tk.Label(content, text=title, font=("Segoe UI Semibold", 9), fg="#64748B", bg="#FFFFFF")
        lbl_title.grid(row=0, column=0, sticky="w", pady=(5, 0))
        
        lbl_val = tk.Label(content, text=value, font=("Segoe UI", 18, "bold"), fg="#0F172A", bg="#FFFFFF")
        lbl_val.grid(row=1, column=0, sticky="w", pady=(4, 0))
        
        lbl_icon = tk.Label(content, text=icon, font=("Segoe UI", 26), fg=color, bg="#FFFFFF")
        lbl_icon.grid(row=0, column=1, rowspan=2, padx=(10, 5), sticky="e")

    def populate_recent_readings(self):
        readings = self.db.get_recent_readings(limit=5)
        
        if not readings:
            lbl = tk.Label(self.list_frame, text="No telemetry readings logged yet.", font=("Segoe UI", 9, "italic"), fg="#64748B", bg="#FFFFFF")
            lbl.pack(pady=30)
            return

        for idx, r in enumerate(readings):
            item = tk.Frame(self.list_frame, bg="#FFFFFF")
            item.pack(fill="x", pady=4)
            
            badge = make_badge(item, r['device_type'], r['device_type'])
            badge.pack(side="left", padx=(0, 8))
            
            lbl_info = tk.Label(item, text=f"{r['device_id']}", font=("Segoe UI Semibold", 9), fg="#0F172A", bg="#FFFFFF")
            lbl_info.pack(side="left")
            
            time_str = r['reading_time'].split(" ")[1][:5] if " " in r['reading_time'] else r['reading_time'][:5]
            
            lbl_data = tk.Label(item, text=f"{r['power']:.1f} W @ {time_str}", font=("Segoe UI Semibold", 9), fg="#10B981", bg="#FFFFFF")
            lbl_data.pack(side="right")
            
            if idx < len(readings) - 1:
                div = tk.Frame(self.list_frame, bg="#F1F5F9", height=1)
                div.pack(fill="x", pady=3)

    def plot_dashboard_chart(self):
        readings = self.db.get_recent_readings(limit=10)
        readings.reverse()
        
        data = [r['power'] for r in readings]
        x_labels = []
        for r in readings:
            t = r['reading_time']
            time_part = t.split(" ")[1][:5] if " " in t else t
            x_labels.append(time_part)
            
        self.trend_chart.plot_data(data, x_labels)


# =====================================================================
# 6. REDESIGNED ADD DEVICE PAGE (Validated card centered)
# =====================================================================

class AddDevicePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F8FAFC")
        self.controller = controller
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        
        form_card = GlassCard(self, width=420, height=540)
        form_card.grid(row=0, column=1, pady=20, sticky="nsew")
        
        body = form_card.frame
        
        lbl_head = tk.Label(body, text="Register New Generator Unit", font=("Segoe UI Bold", 11), fg="#0F172A", bg="#FFFFFF")
        lbl_head.pack(anchor="w", pady=(0, 10))
        
        self.dev_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.loc_var = tk.StringVar()
        self.date_var = tk.StringVar()
        
        # Fields mapping
        f1, self.ent_id = make_modern_input(body, "Device ID (Primary Key)*", self.dev_id_var)
        f1.pack(fill="x", pady=2)
        
        f2, self.ent_name = make_modern_input(body, "Device Name*", self.name_var)
        f2.pack(fill="x", pady=2)
        
        # Technological option dropdown
        lbl_opt = tk.Label(body, text="Generation Technology Type*", font=("Segoe UI Semibold", 9), fg="#64748B", bg="#FFFFFF", anchor="w")
        lbl_opt.pack(fill="x", pady=(2, 1))
        
        self.type_options = ["Solar", "Wind", "Hydro"]
        self.type_var.set(self.type_options[0])
        self.opt_menu = ttk.OptionMenu(body, self.type_var, self.type_options[0], *self.type_options)
        self.opt_menu.config(width=35)
        self.opt_menu.pack(fill="x", ipady=1, pady=(0, 4))
        
        f3, self.ent_loc = make_modern_input(body, "Location Area*", self.loc_var)
        f3.pack(fill="x", pady=2)
        
        f4, self.ent_date = make_modern_input(body, "Installation Date*", self.date_var)
        f4.pack(fill="x", pady=2)
        self.date_var.set(datetime.date.today().strftime("%Y-%m-%d"))
 
        submit_btn = ModernButton(
            body, text="💾 Register Generator Device", 
            command=self.submit_device, bg_color="#10B981", hover_color="#059669"
        )
        submit_btn.pack(fill="x", pady=(10, 2))
        
        form_card.update_hover_recursive()

    def submit_device(self):
        dev_id = self.dev_id_var.get().strip().upper()
        name = self.name_var.get().strip()
        dev_type = self.type_var.get()
        location = self.loc_var.get().strip()
        date_str = self.date_var.get().strip()
        
        if not dev_id or not name or not location or not date_str:
            messagebox.showwarning("Validation Error", "All fields marked with (*) are required!")
            return
        if len(dev_id) < 3:
            messagebox.showwarning("Validation Error", "Device ID must be at least 3 characters!")
            return
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Validation Error", "Installation Date must be YYYY-MM-DD!")
            return
            
        success = self.controller.db.add_device(dev_id, name, dev_type, location, date_str)
        if success:
            messagebox.showinfo("Success", f"Device {dev_id} has been registered successfully!")
            self.controller.show_page("dashboard")


# =====================================================================
# 7. REDESIGNED ADD READING PAGE (Live Power Obverser centered)
# =====================================================================

class AddReadingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F8FAFC")
        self.controller = controller
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        
        form_card = GlassCard(self, width=420, height=540)
        form_card.grid(row=0, column=1, pady=20, sticky="nsew")
        
        body = form_card.frame
        
        lbl_head = tk.Label(body, text="Record Telemetry Signals", font=("Segoe UI Bold", 11), fg="#0F172A", bg="#FFFFFF")
        lbl_head.pack(anchor="w", pady=(0, 10))
        
        self.devices = self.controller.db.get_all_devices()
        
        if not self.devices:
            err_lbl = tk.Label(
                body, text="⚠️ No devices registered.\nPlease create a device in the 'Register Device' page first.", 
                font=("Segoe UI Semibold", 9), fg="#EF4444", bg="#FFFFFF", justify="center"
            )
            err_lbl.pack(pady=20)
            
            btn_go = ModernButton(body, text="➕ Go to Register Device", command=lambda: self.controller.show_page("add_device"), bg_color="#3B82F6", hover_color="#2563EB")
            btn_go.pack(pady=10)
            return

        self.selected_device_var = tk.StringVar()
        device_options = [f"{d['device_id']} - {d['device_name']} ({d['device_type']})" for d in self.devices]
        self.selected_device_var.set(device_options[0])

        lbl_dev = tk.Label(body, text="Select Parent Generator Unit*", font=("Segoe UI Semibold", 9), fg="#64748B", bg="#FFFFFF", anchor="w")
        lbl_dev.pack(fill="x", pady=(2, 1))
        
        dev_opt = ttk.OptionMenu(body, self.selected_device_var, device_options[0], *device_options)
        dev_opt.config(width=35)
        dev_opt.pack(fill="x", ipady=1, pady=(0, 4))

        self.voltage_var = tk.StringVar()
        self.voltage_var.trace_add("write", self.calculate_live_power)
        f1, self.volt_ent = make_modern_input(body, "Voltage (Volts)*", self.voltage_var)
        f1.pack(fill="x", pady=2)
        
        self.current_var = tk.StringVar()
        self.current_var.trace_add("write", self.calculate_live_power)
        f2, self.curr_ent = make_modern_input(body, "Current (Amps)*", self.current_var)
        f2.pack(fill="x", pady=2)

        # Real-time power telemetry observer
        self.power_calc_frame = tk.Frame(body, bg="#EFF6FF", bd=0, highlightbackground="#BFDBFE", highlightthickness=1)
        self.power_calc_frame.pack(fill="x", pady=(8, 8), ipady=2)
        self.power_calc_frame.columnconfigure(0, weight=1)
        
        self.power_title_lbl = tk.Label(
            self.power_calc_frame, text="⚡ Real-time Telemetry Power (Trigger Observer)",
            font=("Segoe UI Semibold", 8), fg="#2563EB", bg="#EFF6FF"
        )
        self.power_title_lbl.pack(pady=(2, 0))
        
        self.power_calc_lbl = tk.Label(
            self.power_calc_frame, text="0.00 Watts", 
            font=("Segoe UI", 16, "bold"), fg="#1D4ED8", bg="#EFF6FF"
        )
        self.power_calc_lbl.pack(pady=2)
        
        lbl_formula = tk.Label(
            self.power_calc_frame, text="Formula: P = V × I (Watts)", 
            font=("Segoe UI Light", 7, "italic"), fg="#3B82F6", bg="#EFF6FF"
        )
        lbl_formula.pack(pady=(0, 2))

        submit_btn = ModernButton(
            body, text="⚡ Log Telemetry Stream", 
            command=self.submit_reading, bg_color="#3B82F6", hover_color="#2563EB"
        )
        submit_btn.pack(fill="x", pady=(5, 5))
        
        form_card.update_hover_recursive()

    def calculate_live_power(self, *args):
        try:
            v = float(self.voltage_var.get().strip())
            c = float(self.current_var.get().strip())
            p = v * c
            self.power_calc_lbl.config(text=f"{p:.2f} Watts")
            self.power_calc_frame.config(bg="#ECFDF5", highlightbackground="#A7F3D0")
            self.power_calc_lbl.config(fg="#047857", bg="#ECFDF5")
            self.power_title_lbl.config(fg="#047857", bg="#ECFDF5")
            self.power_calc_frame.winfo_children()[2].config(fg="#047857", bg="#ECFDF5")
        except ValueError:
            self.power_calc_lbl.config(text="0.00 Watts", fg="#1D4ED8")
            self.power_calc_frame.config(bg="#EFF6FF", highlightbackground="#BFDBFE")
            self.power_title_lbl.config(fg="#2563EB", bg="#EFF6FF")
            self.power_calc_frame.winfo_children()[2].config(fg="#3B82F6", bg="#EFF6FF")

    def submit_reading(self):
        sel = self.selected_device_var.get()
        dev_id = sel.split(" - ")[0]
        volt_str = self.voltage_var.get().strip()
        curr_str = self.current_var.get().strip()
        
        if not volt_str or not curr_str:
            messagebox.showwarning("Validation Error", "All fields are required!")
            return
        try:
            volt = float(volt_str)
            curr = float(curr_str)
            if volt <= 0 or curr <= 0: raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation Error", "Voltage and Current must be positive numeric numbers!")
            return
            
        success = self.controller.db.add_reading(dev_id, volt, curr)
        if success:
            messagebox.showinfo("Success", f"Telemetry reading logged successfully for {dev_id}!")
            self.controller.show_page("dashboard")


# =====================================================================
# 8. REDESIGNED REPORTS VIEW (Sliding charts and filters)
# =====================================================================

class ReportsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F8FAFC")
        self.controller = controller
        self.db = controller.db
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # 1. Filter Panel
        filter_card = GlassCard(self, height=80)
        filter_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        filter_body = filter_card.frame
        
        lbl_dev = tk.Label(filter_body, text="Device ID:", font=("Segoe UI Semibold", 9), bg="#FFFFFF", fg="#64748B")
        lbl_dev.pack(side="left", padx=(5, 5))
        
        self.dev_filter_var = tk.StringVar()
        devices_list = ["All Devices"] + [d['device_id'] for d in self.db.get_all_devices()]
        self.dev_filter_var.set(devices_list[0])
        self.dev_menu = ttk.OptionMenu(filter_body, self.dev_filter_var, devices_list[0], *devices_list)
        self.dev_menu.pack(side="left", padx=(0, 20), ipady=3)
        
        lbl_type = tk.Label(filter_body, text="Technology Type:", font=("Segoe UI Semibold", 9), bg="#FFFFFF", fg="#64748B")
        lbl_type.pack(side="left", padx=(5, 5))
        
        self.type_filter_var = tk.StringVar()
        types_list = ["All Types", "Solar", "Wind", "Hydro"]
        self.type_filter_var.set(types_list[0])
        self.type_menu = ttk.OptionMenu(filter_body, self.type_filter_var, types_list[0], *types_list)
        self.type_menu.pack(side="left", padx=(0, 20), ipady=3)
        
        btn_filter = ModernButton(
            filter_body, text="🔍 Apply Filters", 
            command=self.run_filters, bg_color="#3B82F6", hover_color="#2563EB"
        )
        btn_filter.pack(side="left", padx=(10, 0))
        
        btn_reset = ModernButton(
            filter_body, text="🔄 Reset", 
            command=self.reset_filters, bg_color="#64748B", hover_color="#475569"
        )
        btn_reset.pack(side="left", padx=5)
        
        filter_card.update_hover_recursive()

        # 2. Tabs display
        self.bottom_frame = tk.Frame(self, bg="#F8FAFC")
        self.bottom_frame.grid(row=1, column=0, sticky="nsew")
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(1, weight=1)
        
        self.tab_frame = tk.Frame(self.bottom_frame, bg="#F8FAFC")
        self.tab_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.current_report_type = "readings"
        
        self.btn_readings_tab = ModernButton(self.tab_frame, text="📋 All Readings Log", command=lambda: self.switch_report_tab("readings"), bg_color="#3B82F6", hover_color="#2563EB")
        self.btn_readings_tab.pack(side="left", padx=(0, 5))
        
        self.btn_monthly_tab = ModernButton(self.tab_frame, text="📊 Monthly Summary", command=lambda: self.switch_report_tab("monthly"), bg_color="#64748B", hover_color="#475569")
        self.btn_monthly_tab.pack(side="left", padx=5)
        
        self.btn_devwise_tab = ModernButton(self.tab_frame, text="🌱 Device Efficiency", command=lambda: self.switch_report_tab("devwise"), bg_color="#64748B", hover_color="#475569")
        self.btn_devwise_tab.pack(side="left", padx=5)

        self.view_card = GlassCard(self.bottom_frame, height=310)
        self.view_card.grid(row=1, column=0, sticky="nsew")
        
        self.render_tab_content()

    def switch_report_tab(self, tab_key):
        self.current_report_type = tab_key
        
        tabs = [
            ("readings", self.btn_readings_tab, "#3B82F6", "#2563EB"),
            ("monthly", self.btn_monthly_tab, "#10B981", "#059669"),
            ("devwise", self.btn_devwise_tab, "#F59E0B", "#D97706")
        ]
        for key, btn, primary, hover in tabs:
            if key == tab_key:
                btn.config(bg=primary, activebackground=hover)
                btn.bg_color = primary
                btn.hover_color = hover
            else:
                btn.config(bg="#64748B", activebackground="#475569")
                btn.bg_color = "#64748B"
                btn.hover_color = "#475569"
                
        self.render_tab_content()

    def render_tab_content(self):
        for w in self.view_card.frame.winfo_children():
            w.destroy()
        if self.current_report_type == "readings":
            self.render_readings_tab()
        elif self.current_report_type == "monthly":
            self.render_monthly_procedure_tab()
        elif self.current_report_type == "devwise":
            self.render_devwise_procedure_tab()
        self.view_card.update_hover_recursive()

    # readings Log log
    def render_readings_tab(self):
        container = tk.Frame(self.view_card.frame, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        
        lbl_head = tk.Label(container, text="Logged Device Telemetry Logs", font=("Segoe UI Bold", 10), bg="#FFFFFF", fg="#0F172A", anchor="w")
        lbl_head.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        cols = ("ID", "Device ID", "Device Name", "Tech", "Voltage", "Current", "Power (Triggered)", "Timestamp")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=8)
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        widths = {
            "ID": 50, "Device ID": 80, "Device Name": 180, 
            "Tech": 70, "Voltage": 70, "Current": 70, 
            "Power (Triggered)": 110, "Timestamp": 140
        }
        for c in cols:
            self.tree.heading(c, text=c, anchor="center")
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
            
        sb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        
        self.load_readings_table_records()

    def load_readings_table_records(self):
        dev_filter = self.dev_filter_var.get()
        type_filter = self.type_filter_var.get()
        
        readings = self.db.query_readings_report(device_id=dev_filter, device_type=type_filter)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in readings:
            self.tree.insert("", "end", values=(
                r['reading_id'], r['device_id'], r['device_name'], r['device_type'],
                f"{r['voltage']:.1f} V", f"{r['current']:.1f} A", f"{r['power']:.1f} W", r['reading_time']
            ))

    # Monthly Summary
    def render_monthly_procedure_tab(self):
        container = tk.Frame(self.view_card.frame, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        
        left_box = tk.Frame(container, bg="#FFFFFF")
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_box.columnconfigure(0, weight=1)
        left_box.rowconfigure(1, weight=1)
        
        lbl_head = tk.Label(
            left_box, text="Monthly Telemetry Summary\n(Derived from Stored Procedure)", 
            font=("Segoe UI Bold", 10), bg="#FFFFFF", fg="#0F172A", justify="left", anchor="w"
        )
        lbl_head.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        cols = ("Month", "Tech", "Readings", "Total Energy (Wh)", "Avg Volt", "Avg Curr")
        self.proc_tree = ttk.Treeview(left_box, columns=cols, show="headings", height=8)
        self.proc_tree.grid(row=1, column=0, sticky="nsew")
        
        widths = {"Month": 80, "Tech": 70, "Readings": 70, "Total Energy (Wh)": 110, "Avg Volt": 70, "Avg Curr": 70}
        for c in cols:
            self.proc_tree.heading(c, text=c)
            self.proc_tree.column(c, width=widths.get(c, 80), anchor="center")
            
        sb = ttk.Scrollbar(left_box, orient="vertical", command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        
        right_box = tk.Frame(container, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.monthly_chart = CanvasBarChart(right_box, width=380, height=230)
        self.monthly_chart.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.load_monthly_procedure_data()

    def load_monthly_procedure_data(self):
        records = self.db.get_monthly_energy_report(year=2026)
        
        for r in self.proc_tree.get_children():
            self.proc_tree.delete(r)
            
        monthly_totals = {}
        for r in records:
            m = r['Month']
            monthly_totals[m] = monthly_totals.get(m, 0.0) + r['Total_Power_W']
            
            self.proc_tree.insert("", "end", values=(
                r['Month'], r['Device_Type'], r['Total_Readings'],
                f"{r['Total_Power_W']:.1f}", f"{r['Avg_Voltage_V']:.1f}V", f"{r['Avg_Current_A']:.1f}A"
            ))

        vals = list(monthly_totals.values())
        cats = list(monthly_totals.keys())
        self.monthly_chart.plot_bars(vals, cats, title="Monthly System Power Generation 2026 (Wh)")

    # Device efficiency
    def render_devwise_procedure_tab(self):
        container = tk.Frame(self.view_card.frame, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=5, pady=5)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        
        left_box = tk.Frame(container, bg="#FFFFFF")
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_box.columnconfigure(0, weight=1)
        left_box.rowconfigure(1, weight=1)
        
        lbl_head = tk.Label(
            left_box, text="Device Efficiency Ratios\n(Derived from Stored Procedure)", 
            font=("Segoe UI Bold", 10), bg="#FFFFFF", fg="#0F172A", justify="left", anchor="w"
        )
        lbl_head.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        cols = ("Device ID", "Device Name", "Tech", "Readings", "Total Output", "Avg Power")
        self.dev_proc_tree = ttk.Treeview(left_box, columns=cols, show="headings", height=8)
        self.dev_proc_tree.grid(row=1, column=0, sticky="nsew")
        
        widths = {"Device ID": 80, "Device Name": 130, "Tech": 65, "Readings": 70, "Total Output": 90, "Avg Power": 80}
        for c in cols:
            self.dev_proc_tree.heading(c, text=c)
            self.dev_proc_tree.column(c, width=widths.get(c, 80), anchor="center")
            
        sb = ttk.Scrollbar(left_box, orient="vertical", command=self.dev_proc_tree.yview)
        self.dev_proc_tree.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        
        right_box = tk.Frame(container, bg="#FFFFFF", highlightbackground="#E2E8F0", highlightthickness=1)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.dev_chart = CanvasBarChart(right_box, width=380, height=230)
        self.dev_chart.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.load_devwise_procedure_data()

    def load_devwise_procedure_data(self):
        records = self.db.get_device_wise_stats()
        
        for r in self.dev_proc_tree.get_children():
            self.dev_proc_tree.delete(r)
            
        chart_vals = []
        chart_cats = []
        for r in records:
            chart_vals.append(r['Total_Power_W'])
            chart_cats.append(r['Device_ID'])
            
            self.dev_proc_tree.insert("", "end", values=(
                r['Device_ID'], r['Device_Name'], r['Device_Type'],
                r['Total_Readings'], f"{r['Total_Power_W']:.1f} W", f"{r['Avg_Power_W']:.1f} W"
            ))
        self.dev_chart.plot_bars(chart_vals, chart_cats, title="Accrued Generation by Device ID (Wh)")

    def run_filters(self):
        if self.current_report_type == "readings":
            self.load_readings_table_records()
        elif self.current_report_type == "monthly":
            self.load_monthly_procedure_data()
        elif self.current_report_type == "devwise":
            self.load_devwise_procedure_data()

    def reset_filters(self):
        self.dev_filter_var.set("All Devices")
        self.type_filter_var.set("All Types")
        self.run_filters()


# =====================================================================
# 9. REDESIGNED ADMIN CRUD PAGE (Dynamic modal overlays & hovers)
# =====================================================================

class DeviceAdminPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F8FAFC")
        self.controller = controller
        self.db = controller.db
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # 1. Action Controls
        ctrl_frame = tk.Frame(self, bg="#F8FAFC")
        ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        lbl_info = tk.Label(
            ctrl_frame, text="Active Device System Control Log (Select a row to Update / Delete)", 
            font=("Segoe UI Semibold", 9), bg="#F8FAFC", fg="#64748B"
        )
        lbl_info.pack(side="left", pady=5)
        
        btn_del = ModernButton(ctrl_frame, text="🗑️ Delete Selected", command=self.delete_device, bg_color="#EF4444", hover_color="#DC2626")
        btn_del.pack(side="right", padx=(5, 0))
        
        btn_edit = ModernButton(ctrl_frame, text="✏️ Edit Selected", command=self.open_edit_overlay, bg_color="#F59E0B", hover_color="#D97706")
        btn_edit.pack(side="right", padx=5)

        # 2. Main Database Table
        table_card = GlassCard(self, height=360)
        table_card.grid(row=1, column=0, sticky="nsew")
        
        body = table_card.frame
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        
        cols = ("Device ID", "Device Name", "Technology Type", "Location Field", "Installation Date", "System Status")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=12)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        widths = {"Device ID": 90, "Device Name": 200, "Technology Type": 130, "Location Field": 160, "Installation Date": 120, "System Status": 100}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
            
        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        
        self.load_devices_records()
        table_card.update_hover_recursive()

    def load_devices_records(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        devices = self.db.get_all_devices()
        for d in devices:
            self.tree.insert("", "end", values=(
                d['device_id'], d['device_name'], d['device_type'], 
                d['location'], d['installation_date'], d['status']
            ))

    def delete_device(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Admin Action", "Please select a device from the table grid to delete!")
            return
        item_vals = self.tree.item(sel[0], 'values')
        dev_id = item_vals[0]
        
        confirm = messagebox.askyesno(
            "Cascade Delete Confirmation", 
            f"WARNING: Deleting device '{dev_id}' will also delete ALL related telemetry reading logs from the database!\n\nAre you sure you want to proceed?"
        )
        if confirm:
            if self.db.delete_device(dev_id):
                messagebox.showinfo("Success", f"Device {dev_id} and all related logs successfully deleted!")
                self.load_devices_records()

    def open_edit_overlay(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Admin Action", "Please select a device from the table grid to edit!")
            return
        item_vals = self.tree.item(sel[0], 'values')
        
        overlay = tk.Toplevel(self)
        overlay.title(f"Edit Device {item_vals[0]}")
        overlay.geometry("400x490")
        overlay.resizable(False, False)
        overlay.configure(bg="#FFFFFF")
        overlay.grab_set()
        
        container = tk.Frame(overlay, bg="#FFFFFF", padx=25, pady=25)
        container.pack(fill="both", expand=True)
        
        lbl_head = tk.Label(container, text=f"Update Metadata: {item_vals[0]}", font=("Segoe UI Bold", 12), bg="#FFFFFF", fg="#0F172A")
        lbl_head.pack(pady=(0, 20), anchor="w")
        
        name_var = tk.StringVar(value=item_vals[1])
        type_var = tk.StringVar(value=item_vals[2])
        loc_var = tk.StringVar(value=item_vals[3])
        status_var = tk.StringVar(value=item_vals[5])
        
        f1, ent_name = make_modern_input(container, "Device Name*", name_var)
        f1.pack(fill="x", pady=5)
        
        tk.Label(container, text="Technology Type*", font=("Segoe UI Semibold", 9), bg="#FFFFFF", fg="#64748B").pack(anchor="w", pady=(5, 2))
        opt_type = ttk.OptionMenu(container, type_var, item_vals[2], "Solar", "Wind", "Hydro")
        opt_type.pack(fill="x", ipady=3, pady=(0, 10))
        
        f2, ent_loc = make_modern_input(container, "Location Area*", loc_var)
        f2.pack(fill="x", pady=5)
        
        tk.Label(container, text="System Status*", font=("Segoe UI Semibold", 9), bg="#FFFFFF", fg="#64748B").pack(anchor="w", pady=(5, 2))
        opt_status = ttk.OptionMenu(container, status_var, item_vals[5], "Active", "Inactive", "Maintenance")
        opt_status.pack(fill="x", ipady=3, pady=(0, 20))
        
        btn_box = tk.Frame(container, bg="#FFFFFF")
        btn_box.pack(fill="x", pady=10)
        
        btn_cancel = ModernButton(
            btn_box, text="Cancel", 
            command=overlay.destroy, bg_color="#64748B", fg_color="#FFFFFF", hover_color="#475569"
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def save_changes():
            n = name_var.get().strip()
            t = type_var.get()
            l = loc_var.get().strip()
            s = status_var.get()
            
            if not n or not l:
                messagebox.showwarning("Validation Error", "All fields are required!", parent=overlay)
                return
            if self.db.update_device(item_vals[0], n, t, l, s):
                messagebox.showinfo("Success", "Device updated successfully!", parent=overlay)
                overlay.destroy()
                self.load_devices_records()
                
        btn_save = ModernButton(
            btn_box, text="💾 Save Changes", 
            command=save_changes, bg_color="#F59E0B", fg_color="#FFFFFF", hover_color="#D97706"
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))


# =====================================================================
# Main Application Entrance
# =====================================================================
if __name__ == "__main__":
    app = RenewableEnergyApp()
    app.mainloop()
