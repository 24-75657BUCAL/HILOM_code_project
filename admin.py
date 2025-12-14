import sys
import csv
import os
import mysql.connector
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QTabWidget, QMessageBox, QTextEdit, QSplitter
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QTimer
import subprocess
import signal

class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM Admin Panel")
        self.setGeometry(100, 100, 1200, 800)
        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("HILOM Administration Panel")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2e7d32; margin: 20px;")
        main_layout.addWidget(header)

        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Login Records Tab
        self.create_login_records_tab()

        # Registered Users Tab
        self.create_registered_users_tab()

        # Appointments Tab
        self.create_appointments_tab()

        # System Control Tab
        self.create_system_control_tab()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh All Data")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #45a049; }
        """)
        refresh_btn.clicked.connect(self.refresh_all_data)
        main_layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        # Load initial data
        self.refresh_all_data()

    def create_login_records_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("📊 Login Records")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        self.login_table = QTableWidget()
        self.login_table.setColumnCount(4)
        self.login_table.setHorizontalHeaderLabels(["Username", "Timestamp", "IP Address", "Status"])
        layout.addWidget(self.login_table)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Login Records")

    def create_registered_users_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("👥 Registered Users")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Split view for CSV and MySQL data
        splitter = QSplitter(Qt.Vertical)

        # CSV Users
        csv_frame = QFrame()
        csv_layout = QVBoxLayout()
        csv_label = QLabel("CSV Registered Users:")
        csv_label.setFont(QFont("Arial", 12, QFont.Bold))
        csv_layout.addWidget(csv_label)

        self.csv_users_table = QTableWidget()
        self.csv_users_table.setColumnCount(3)
        self.csv_users_table.setHorizontalHeaderLabels(["Name", "Password", "Email"])
        csv_layout.addWidget(self.csv_users_table)
        csv_frame.setLayout(csv_layout)
        splitter.addWidget(csv_frame)

        # MySQL Users
        mysql_frame = QFrame()
        mysql_layout = QVBoxLayout()
        mysql_label = QLabel("MySQL Registered Users:")
        mysql_label.setFont(QFont("Arial", 12, QFont.Bold))
        mysql_layout.addWidget(mysql_label)

        self.mysql_users_table = QTableWidget()
        self.mysql_users_table.setColumnCount(4)
        self.mysql_users_table.setHorizontalHeaderLabels(["ID", "Name", "Password", "Email"])
        mysql_layout.addWidget(self.mysql_users_table)
        mysql_frame.setLayout(mysql_layout)
        splitter.addWidget(mysql_frame)

        layout.addWidget(splitter)
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Registered Users")

    def create_appointments_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("📅 Appointments")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        self.appointments_table = QTableWidget()
        self.appointments_table.setColumnCount(8)
        self.appointments_table.setHorizontalHeaderLabels([
            "Name", "Date", "Time", "Type", "Price", "Contact", "Concern", "Status"
        ])
        layout.addWidget(self.appointments_table)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Appointments")

    def create_system_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("⚙️ System Control")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # System status
        status_frame = QFrame()
        status_layout = QVBoxLayout()

        self.status_label = QLabel("System Status: Checking...")
        self.status_label.setFont(QFont("Arial", 14))
        status_layout.addWidget(self.status_label)

        # Control buttons
        controls_layout = QHBoxLayout()

        shutdown_btn = QPushButton("🛑 Shutdown Dashboard")
        shutdown_btn.setStyleSheet("""
            QPushButton {
                background: #f44336;
                color: white;
                padding: 15px 30px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #d32f2f; }
        """)
        shutdown_btn.clicked.connect(self.shutdown_dashboard)
        controls_layout.addWidget(shutdown_btn)

        restart_btn = QPushButton("🔄 Restart Dashboard")
        restart_btn.setStyleSheet("""
            QPushButton {
                background: #ff9800;
                color: white;
                padding: 15px 30px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #f57c00; }
        """)
        restart_btn.clicked.connect(self.restart_dashboard)
        controls_layout.addWidget(restart_btn)

        status_layout.addLayout(controls_layout)
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

        # System logs
        logs_label = QLabel("System Logs:")
        logs_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(logs_label)

        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(200)
        layout.addWidget(self.logs_text)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "System Control")

    def refresh_all_data(self):
        self.load_login_records()
        self.load_registered_users()
        self.load_appointments()
        self.check_system_status()
        self.load_system_logs()

    def load_login_records(self):
        # For now, create sample login records
        # In a real implementation, you'd read from a log file
        sample_logins = [
            ["user1", "2025-12-14 10:30:00", "192.168.1.1", "Success"],
            ["admin", "2025-12-14 11:15:00", "192.168.1.1", "Success"],
            ["user2", "2025-12-14 12:00:00", "192.168.1.1", "Failed"]
        ]

        self.login_table.setRowCount(len(sample_logins))
        for row, login in enumerate(sample_logins):
            for col, data in enumerate(login):
                self.login_table.setItem(row, col, QTableWidgetItem(data))

    def load_registered_users(self):
        # Load CSV users
        csv_users = []
        try:
            if os.path.exists("registered_list.csv"):
                with open("registered_list.csv", "r", newline="") as file:
                    reader = csv.reader(file)
                    next(reader, None)  # Skip header
                    csv_users = list(reader)
        except Exception as e:
            print(f"Error loading CSV users: {e}")

        # Add sample data if no CSV users
        if not csv_users:
            csv_users = [
                ["John Doe", "password123", "john@example.com"],
                ["Jane Smith", "pass456", "jane@example.com"]
            ]

        self.csv_users_table.setRowCount(len(csv_users))
        for row, user in enumerate(csv_users):
            for col, data in enumerate(user):
                self.csv_users_table.setItem(row, col, QTableWidgetItem(data))

        # Load MySQL users
        mysql_users = []
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="HILOM"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, password, email FROM registered_users")
            mysql_users = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error loading MySQL users: {e}")
            # Add sample MySQL data
            mysql_users = [
                [1, "Admin User", "admin123", "admin@hilom.com"],
                [2, "Test User", "test456", "test@hilom.com"]
            ]

        self.mysql_users_table.setRowCount(len(mysql_users))
        for row, user in enumerate(mysql_users):
            for col, data in enumerate(user):
                self.mysql_users_table.setItem(row, col, QTableWidgetItem(str(data)))

    def load_appointments(self):
        appointments = []
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="hilom"
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT patient_name, schedule, time_slot, consultation_type, price,
                       contact, concern, 'Active' as status
                FROM appointments
                ORDER BY created_at DESC
            """)
            appointments = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error loading appointments: {e}")
            # Fallback: try to load from history.csv
            try:
                if os.path.exists("day-by-day.csv"):
                    with open("day-by-day.csv", "r") as file:
                        reader = csv.reader(file)
                        for row in reader:
                            if len(row) >= 3 and row[0] == "appointment":
                                appointments.append([row[1], "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "Logged"])
            except Exception as e2:
                print(f"Error loading history: {e2}")

        # Add sample appointments if none found
        if not appointments:
            appointments = [
                ["John Doe", "2025-12-15", "10:00 AM", "Online", "$100", "123-456-7890", "Anxiety", "Active"],
                ["Jane Smith", "2025-12-16", "2:00 PM", "Face-to-Face", "$150", "987-654-3210", "Depression", "Active"]
            ]

        self.appointments_table.setRowCount(len(appointments))
        for row, apt in enumerate(appointments):
            for col, data in enumerate(apt):
                self.appointments_table.setItem(row, col, QTableWidgetItem(str(data)))

    def check_system_status(self):
        # Check if dashboard is running
        try:
            import psutil
            dashboard_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                        if 'dashboard.py' in ' '.join(proc.info['cmdline']):
                            dashboard_running = True
                            break
                except:
                    continue

            if dashboard_running:
                self.status_label.setText("🟢 System Status: Dashboard is RUNNING")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("🔴 System Status: Dashboard is NOT RUNNING")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
        except ImportError:
            self.status_label.setText("⚠️ System Status: Cannot check (psutil not installed)")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

    def load_system_logs(self):
        logs = []
        try:
            if os.path.exists("history.csv"):
                with open("history.csv", "r") as file:
                    reader = csv.reader(file)
                    logs = list(reader)[-20:]  # Last 20 entries
        except Exception as e:
            logs = [f"Error loading logs: {e}"]

        log_text = "\n".join([", ".join(row) for row in logs])
        self.logs_text.setPlainText(log_text)

    def shutdown_dashboard(self):
        reply = QMessageBox.question(
            self, "Confirm Shutdown",
            "Are you sure you want to shutdown the dashboard application?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                import psutil
                shutdown_count = 0
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                            if 'dashboard.py' in ' '.join(proc.info['cmdline']):
                                proc.terminate()
                                shutdown_count += 1
                    except:
                        continue

                if shutdown_count > 0:
                    QMessageBox.information(self, "Success", f"Shutdown {shutdown_count} dashboard instance(s)")
                    self.check_system_status()
                else:
                    QMessageBox.warning(self, "Not Found", "No running dashboard instances found")
            except ImportError:
                QMessageBox.warning(self, "Error", "Cannot shutdown (psutil not installed)")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Shutdown failed: {e}")

    def restart_dashboard(self):
        reply = QMessageBox.question(
            self, "Confirm Restart",
            "Are you sure you want to restart the dashboard application?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # First shutdown
            self.shutdown_dashboard()
            # Then restart
            try:
                import os
                os.startfile("dashboard.py")
                QMessageBox.information(self, "Success", "Dashboard restart initiated")
                QTimer.singleShot(2000, self.check_system_status)  # Check status after 2 seconds
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Restart failed: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    admin_panel = AdminPanel()
    admin_panel.show()
    sys.exit(app.exec_())