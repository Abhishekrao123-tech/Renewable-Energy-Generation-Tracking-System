CREATE DATABASE IF NOT EXISTS renewable_energy_db;
USE renewable_energy_db;

-- 2. Drop existing tables if they exist to allow clean re-runs
DROP TABLE IF EXISTS energy_readings;
DROP TABLE IF EXISTS devices;

-- 3. Create 'devices' Table
-- Holds information about the generation units installed (Solar, Wind, Hydro)
CREATE TABLE devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type ENUM('Solar', 'Wind', 'Hydro') NOT NULL,
    location VARCHAR(150) NOT NULL,
    installation_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Maintenance'))
);

-- 4. Create 'energy_readings' Table
-- Holds voltage, current, and auto-calculated power telemetry logs
CREATE TABLE energy_readings (
    reading_id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    voltage DECIMAL(10,2) NOT NULL,
    current DECIMAL(10,2) NOT NULL,
    power DECIMAL(10,2) NOT NULL, -- Auto-calculated by Database Trigger
    reading_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- =====================================================================
-- 5. Database Trigger: Auto-calculate Power
-- Automatically computes Power (Watts) = Voltage * Current before insertion
-- =====================================================================
DELIMITER //

CREATE TRIGGER before_reading_insert
BEFORE INSERT ON energy_readings
FOR EACH ROW
BEGIN
    SET NEW.power = NEW.voltage * NEW.current;
END //

CREATE TRIGGER before_reading_update
BEFORE UPDATE ON energy_readings
FOR EACH ROW
BEGIN
    SET NEW.power = NEW.voltage * NEW.current;
END //

DELIMITER ;

-- =====================================================================
-- 6. Stored Procedure: Monthly Energy Report
-- Aggregates total power and average electrical values by Month and Year
-- =====================================================================
DELIMITER //

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
END //

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
END //

DELIMITER ;

-- =====================================================================
-- 7. Insert Dummy/Sample Data
-- =====================================================================

-- Add Sample Devices
INSERT INTO devices (device_id, device_name, device_type, location, installation_date, status) VALUES
('SOL-001', 'Solar Panel Array Alpha', 'Solar', 'Rooftop Block A', '2025-01-15', 'Active'),
('SOL-002', 'Solar Tracker Beta', 'Solar', 'South Campus Field', '2025-03-10', 'Active'),
('WND-001', 'Wind Turbine Helix-1', 'Wind', 'East Windy Ridge', '2024-11-20', 'Active'),
('WND-002', 'Wind Turbine Helix-2', 'Wind', 'East Windy Ridge', '2025-02-18', 'Maintenance'),
('HYD-001', 'Hydro Micro-Turbine H1', 'Hydro', 'Campus Stream Fall', '2025-04-05', 'Active');

-- Add Sample Energy Readings (Power is auto-computed by the trigger!)
-- Readings span past few months of 2026 to show monthly statistics
INSERT INTO energy_readings (device_id, voltage, current, reading_time) VALUES
-- January Readings
('SOL-001', 220.5, 4.2, '2026-01-10 12:00:00'),
('WND-001', 110.2, 8.5, '2026-01-10 14:00:00'),

-- February Readings
('SOL-001', 222.0, 5.0, '2026-02-15 12:30:00'),
('WND-001', 108.5, 9.2, '2026-02-15 15:00:00'),
('SOL-002', 215.8, 3.8, '2026-02-16 11:00:00'),

-- March Readings
('SOL-001', 218.0, 4.8, '2026-03-20 13:00:00'),
('WND-001', 112.4, 7.8, '2026-03-20 16:30:00'),
('SOL-002', 220.0, 5.2, '2026-03-21 11:30:00'),
('WND-002', 110.0, 6.0, '2026-03-22 10:00:00'),

-- April Readings
('SOL-001', 224.2, 5.5, '2026-04-25 12:00:00'),
('SOL-002', 225.0, 6.1, '2026-04-25 13:00:00'),
('WND-001', 115.0, 10.5, '2026-04-26 14:30:00'),
('HYD-001', 230.0, 8.0, '2026-04-28 09:00:00'),

-- May Readings (Recent data)
('SOL-001', 221.0, 4.9, '2026-05-24 10:00:00'),
('SOL-002', 223.5, 5.4, '2026-05-24 11:00:00'),
('WND-001', 113.8, 9.0, '2026-05-24 12:30:00'),
('HYD-001', 228.4, 7.5, '2026-05-24 14:00:00'),
('SOL-001', 219.0, 4.5, '2026-05-24 15:00:00'),
('WND-001', 112.0, 8.2, '2026-05-24 16:00:00');

-- =====================================================================
-- Setup Script Completed
-- To execute this in MySQL command line, run:
--   mysql -u your_username -p < schema.sql
-- =====================================================================
