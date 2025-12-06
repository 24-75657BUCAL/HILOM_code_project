
# admin_dashboard_fixed.py
# Requires: PyQt5, mysql-connector-python (optional)
# Run: python admin_dashboard_fixed.py

import sys, time
from dataclasses import dataclass
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor

# MySQL optional
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False

# ---------------- DB CONFIG ----------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "your_db_user",
    "password": "your_db_password",
    "database": "your_database_name",
}

# ---------------- Data classes ----------------
@dataclass
class UserActivity:
    username: str
    status: str
    last_action: str
    login_time: Optional[str]
    logout_time: Optional[str]

@dataclass
class ScheduledTask:
    task_name: str
    schedule_time: str
    color_code: str
    status: str

# ---------------- DB Worker ----------------
class DBWorker(QThread):
    users_fetched = pyqtSignal(list)
    tasks_fetched = pyqtSignal(list)
    db_error = pyqtSignal(str)

    def __init__(self, poll_interval_s=5):
        super().__init__()
        self.poll_interval_s = poll_interval_s
        self._running = True
        self._conn = None
        self._cursor = None

    def run(self):
        if MYSQL_AVAILABLE:
            try:
                self._connect()
            except Exception as e:
                self.db_error.emit("DB connection failed: " + str(e))
                self._close_conn()
        else:
            self.db_error.emit("mysql-connector not installed; using sample data fallback")

        while self._running:
            try:
                users = self.fetch_user_activity()
                tasks = self.fetch_scheduled_tasks()
                self.users_fetched.emit(users)
                self.tasks_fetched.emit(tasks)
            except Exception as e:
                self.db_error.emit("Error querying DB: " + str(e))
                self.users_fetched.emit(self.sample_users())
                self.tasks_fetched.emit(self.sample_tasks())

            for _ in range(int(self.poll_interval_s * 2)):
                if not self._running:
                    break
                time.sleep(0.5)
        self._close_conn()

    def stop(self):
        self._running = False

    def _connect(self):
        self._conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG.get("port", 3306),
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            connection_timeout=5,
            autocommit=True
        )
        self._cursor = self._conn.cursor(dictionary=True)

    def _close_conn(self):
        try:
            if self._cursor: self._cursor.close()
            if self._conn: self._conn.close()
        except Exception:
            pass
        self._cursor = None
        self._conn = None

    def fetch_user_activity(self) -> List[UserActivity]:
        if MYSQL_AVAILABLE and self._conn:
            q = ("SELECT username, status, last_action, "
                 "DATE_FORMAT(login_time, '%Y-%m-%d %H:%i:%s') AS login_time, "
                 "DATE_FORMAT(logout_time, '%Y-%m-%d %H:%i:%s') AS logout_time "
                 "FROM user_activity "
                 "ORDER BY FIELD(status, 'online','idle','offline'), updated_at DESC LIMIT 200;")
            self._cursor.execute(q)
            rows = self._cursor.fetchall()
            return [UserActivity(
                username=r.get("username") or "Unknown",
                status=r.get("status") or "offline",
                last_action=r.get("last_action") or "",
                login_time=r.get("login_time"),
                logout_time=r.get("logout_time"),
            ) for r in rows]
        return self.sample_users()

    def fetch_scheduled_tasks(self) -> List[ScheduledTask]:
        if MYSQL_AVAILABLE and self._conn:
            q = ("SELECT task_name, schedule_time, color_code, status "
                 "FROM scheduled_tasks ORDER BY updated_at DESC LIMIT 100;")
            self._cursor.execute(q)
            rows = self._cursor.fetchall()
            return [ScheduledTask(
                task_name=r.get("task_name") or "Unnamed Task",
                schedule_time=r.get("schedule_time") or "",
                color_code=r.get("color_code") or "#2196F3",
                status=r.get("status") or "pending",
            ) for r in rows]
        return self.sample_tasks()

    @staticmethod
    def sample_users() -> List[UserActivity]:
        return [
            UserActivity("Alice", "online", "Viewing Dashboard", "2025-12-07 00:50:23", None),
            UserActivity("Bob", "idle", "Idle on Reports", "2025-12-07 00:34:12", None),
            UserActivity("Charlie", "offline", "Logged out", "2025-12-06 23:02:01", "2025-12-06 23:30:09"),
        ]

    @staticmethod
    def sample_tasks() -> List[ScheduledTask]:
        return [
            ScheduledTask("Daily Backup", "02:00 AM", "#2196F3", "scheduled"),
            ScheduledTask("Monthly Report Gen", "1st day of month", "#FF9800", "scheduled"),
            ScheduledTask("Data Purge (Pending)", "Manual", "#F44336", "pending"),
        ]

# ---------------- UI Components ----------------
class HoverFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.normal_style = """
            QFrame { background-color: rgba(255,255,255,0.95); border-radius:12px; border:1px solid #e6e6e6; }
        """
        self.hover_style = """
            QFrame { background-color: rgba(250,250,250,1); border-radius:12px; border:1px solid #d8d8d8; }
        """
        self.setStyleSheet(self.normal_style)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.normal_style)
        super().leaveEvent(event)

class AdminToggleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(4)
        self.toggle_state = True
        self.setCursor(Qt.PointingHandCursor)

        self.icon_stack = QLabel("⚡")
        self.icon_stack.setAlignment(Qt.AlignCenter)
        self.icon_stack.setStyleSheet("font-size:18pt; color:#00c853;")
        self.state_label = QLabel("ON")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setStyleSheet("font-weight:600; font-size:9pt; color:#333333; padding-top:2px;")

        layout.addWidget(self.icon_stack)
        layout.addWidget(self.state_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0); shadow.setYOffset(3)
        shadow.setColor(QColor(0,0,0,40))
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_state = not self.toggle_state
            self.update_ui()
        super().mousePressEvent(event)

    def update_ui(self):
        if self.toggle_state:
            self.icon_stack.setText("⚡")
            self.state_label.setText("ON")
        else:
            self.icon_stack.setText("🚫")
            self.state_label.setText("OFF")

class UserActivityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(6)
        self.user_list = QListWidget()
        self.user_list.setStyleSheet("""
            QListWidget { border:none; background:transparent; padding:0; }
            QListWidget::item { padding:8px; border-bottom:1px solid #f1f1f1; }
            QListWidget::item:selected { background-color:#e8f4ff; border-left:3px solid #2196F3; }
        """)
        self.layout.addWidget(self.user_list)

    def set_users(self, users: List[UserActivity]):
        self.user_list.clear()
        for u in users:
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(6,6,6,6)
            h_layout.setSpacing(8)
            avatar = QLabel("👤"); avatar.setFixedWidth(28); avatar.setStyleSheet("font-size:14pt;")
            h_layout.addWidget(avatar)
            name_label = QLabel(u.username); name_label.setStyleSheet("font-size:10pt; color:#222; font-weight:600;")
            status_label = QLabel(f"{u.status} • {u.last_action}"); status_label.setStyleSheet("font-size:9pt; color:#757575;")
            name_status_layout = QVBoxLayout(); name_status_layout.setContentsMargins(0,0,0,0)
            name_status_layout.addWidget(name_label); name_status_layout.addWidget(status_label)
            h_layout.addLayout(name_status_layout)
            h_layout.addStretch(1)
            item = QListWidgetItem(self.user_list)
            item.setSizeHint(widget.sizeHint())
            self.user_list.addItem(item)
            self.user_list.setItemWidget(item, widget)

class ScheduledTasksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(10)
        self.task_list = QVBoxLayout()
        container = QWidget(); container.setLayout(self.task_list)
        self.layout.addWidget(container)
        self.layout.addStretch(1)

    def set_tasks(self, tasks: List[ScheduledTask]):
        while self.task_list.count():
            item = self.task_list.takeAt(0)
            w = item.widget()
            if w: w.setParent(None)
        for t in tasks:
            frame = HoverFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {t.color_code}1A;
                    border: 1px solid {t.color_code}30;
                    border-radius: 10px;
                    padding: 10px;
                }}
            """)
            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(8,8,8,8)
            name_label = QLabel(t.task_name); name_label.setStyleSheet(f"font-size:10pt; color:{t.color_code}; font-weight:700;")
            time_label = QLabel(t.schedule_time + (" • " + t.status if t.status else "")); time_label.setStyleSheet("font-size:9pt; color:#616161;")
            h_layout.addWidget(name_label)
            h_layout.addStretch(1)
            h_layout.addWidget(time_label)
            self.task_list.addWidget(frame)

# ---------------- Main Window ----------------
class AdminToggleInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Admin Dashboard")
        self.setGeometry(100, 100, 980, 640)
        self.setStyleSheet("QMainWindow { background-color: #fbfdfe; font-family: 'Segoe UI', sans-serif; }")

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget); main_layout.setContentsMargins(36,36,36,36); main_layout.setSpacing(18)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Admin Console"); title_font = QFont(); title_font.setPointSize(20); title_font.setWeight(QFont.Bold); title_label.setFont(title_font)
        title_label.setStyleSheet("color:#ffffff; padding:8px 14px; border-radius:12px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #76c7c0, stop:1 #8ad4ff);")
        self.admin_toggle = AdminToggleWidget()
        header_layout.addWidget(title_label); header_layout.addStretch(1); header_layout.addWidget(self.admin_toggle)
        main_layout.addLayout(header_layout)

        hr = QFrame(); hr.setFixedHeight(1); hr.setStyleSheet("background-color: #efefef;"); main_layout.addWidget(hr)

        # Card
        card_container = QFrame(); card_container.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.88); border:1px solid #f0f0f0; border-radius:16px; }"); card_container.setMinimumSize(860,420)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(36); shadow.setXOffset(0); shadow.setYOffset(12); shadow.setColor(QColor(0,0,0,45)); card_container.setGraphicsEffect(shadow)
        card_layout = QHBoxLayout(card_container); card_layout.setContentsMargins(20,20,20,20); card_layout.setSpacing(18)

        # Left
        left_layout = QVBoxLayout(); left_header = QLabel("Active Users"); left_header.setStyleSheet("font-weight:700; font-size:16pt; padding:10px; background-color:#fafafa; border-radius:12px; color:#303030;"); left_layout.addWidget(left_header)
        self.user_widget = UserActivityWidget(); left_layout.addWidget(self.user_widget)

        # Divider
        divider = QFrame(); divider.setFrameShape(QFrame.VLine); divider.setFixedWidth(1); divider.setStyleSheet("background-color: #e9e9e9; margin-top:6px; margin-bottom:6px;")

        # Right
        right_layout = QVBoxLayout(); right_header = QLabel("Scheduled Tasks"); right_header.setStyleSheet("font-weight:700; font-size:16pt; padding:10px; background-color:#fafafa; border-radius:12px; color:#303030;"); right_layout.addWidget(right_header)
        self.tasks_widget = ScheduledTasksWidget(); right_layout.addWidget(self.tasks_widget)

        card_layout.addLayout(left_layout,1); card_layout.addWidget(divider); card_layout.addLayout(right_layout,1)
        content_wrapper = QHBoxLayout(); content_wrapper.addStretch(1); content_wrapper.addWidget(card_container); content_wrapper.addStretch(1); main_layout.addLayout(content_wrapper)
        main_layout.addStretch(1)

        # Status label
        self.status_label = QLabel(""); self.status_label.setStyleSheet("font-size:9pt; color:#666666;"); main_layout.addWidget(self.status_label)

        # DB Worker
        self.db_worker = DBWorker(poll_interval_s=5)
        self.db_worker.users_fetched.connect(self.on_users_fetched)
        self.db_worker.tasks_fetched.connect(self.on_tasks_fetched)
        self.db_worker.db_error.connect(self.on_db_error)
        self.db_worker.start()

    def closeEvent(self, event):
        try:
            if hasattr(self, "db_worker") and self.db_worker: self.db_worker.stop(); self.db_worker.wait(2000)
        except Exception: pass
        super().closeEvent(event)

    # Slots
    def on_users_fetched(self, users: List[UserActivity]): self.user_widget.set_users(users)
    def on_tasks_fetched(self, tasks: List[ScheduledTask]): self.tasks_widget.set_tasks(tasks)
    def on_db_error(self, message: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S"); self.status_label.setText(f"[{ts}] {message}")

# ---------------- MAIN ----------------
if __name__ == '__main__':
    app = QApplication(sys.argv); app.setFont(QFont("Segoe UI",10))
    window = AdminToggleInterface(); window.show()
    sys.exit(app.exec_())


import sys
import csv
import os
import mysql.connector
import dash_board as db
import admin as db
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                             QPushButton, QLabel, QGraphicsOpacityEffect, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve


# ==================== HOVER BUTTON ====================
class HoverButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)


# ==================== REGISTER WINDOW ====================
class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM - Register")
        self.setGeometry(100, 100, 600, 550)
        self.initDatabase()
        self.initUI()

    def initUI(self):
        # Background
        self.background_pixmap = QPixmap('cherry-blossom-tree-thumb.jpg')
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(600, 550)
            self.background_pixmap.fill(QColor("#A0C4FF"))

        # Wrapper
        self.wrapper = QWidget(self)
        self.inner_layout = QVBoxLayout(self.wrapper)
        self.inner_layout.setAlignment(Qt.AlignCenter)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setSpacing(12)

        # Title
        self.title_label = QLabel("CREATE ACCOUNT")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.inner_layout.addWidget(self.title_label)

        # Logo
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap('HILOM.png')
        if not self.logo_pixmap.isNull():
            scaled_logo = self.logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            self.logo_label.setText("HILOM")
            self.logo_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.inner_layout.addWidget(self.logo_label)

        # Input style
        input_style = "border: 2px solid #ccc; padding: 10px; border-radius: 10px;"

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        self.name_input.setStyleSheet(input_style)
        self.name_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.name_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet(input_style)
        self.email_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.email_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.password_input)

        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet(input_style)
        self.confirm_password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.confirm_password_input)

        # Register Button
        self.register_button = HoverButton("REGISTER")
        self.register_button.setFixedWidth(150)
        self.register_button.setFixedHeight(40)
        self.register_button.clicked.connect(self.save_account)
        self.inner_layout.addWidget(self.register_button, alignment=Qt.AlignCenter)

        # Back to Login
        self.back_link = QPushButton("Already have an account? Login")
        self.back_link.setFixedWidth(220)
        self.back_link.setFont(QFont('Arial', 10))
        self.back_link.setStyleSheet("""
            QPushButton {
                color: #000000;
                background-color: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #4CAF50;
            }
        """)
        self.back_link.setCursor(Qt.PointingHandCursor)
        self.back_link.clicked.connect(self.back_to_login)
        self.inner_layout.addWidget(self.back_link, alignment=Qt.AlignCenter)

        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.wrapper.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def back_to_login(self):
        self.close()

    def initDatabase(self):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS hilom_db")
            cursor.execute("USE hilom_db")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registered_users(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            conn.commit()
            conn.close()
            print("Database ready: hilom_db")
        except mysql.connector.Error as e:
            print("Database Error:", e)
        except Exception as e:
            print("Unexpected error in initDatabase:", e)

    def validate_inputs(self, name, pwd, confirm, email):
        if not name.strip():
            QMessageBox.warning(self, "Error", "Name cannot be empty!")
            return False
        if not email.strip():
            QMessageBox.warning(self, "Error", "Email cannot be empty!")
            return False
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email!")
            return False
        if not pwd:
            QMessageBox.warning(self, "Error", "Password cannot be empty!")
            return False
        if len(pwd) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters!")
            return False
        if pwd != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return False
        return True

    def save_account(self):
        try:
            name = self.name_input.text()
            pwd = self.password_input.text()
            confirm = self.confirm_password_input.text()
            email = self.email_input.text()

            if not self.validate_inputs(name, pwd, confirm, email):
                return

            csv_saved = False
            mysql_saved = False

            # Save to CSV
            try:
                file_exists = os.path.isfile("registered_list.csv")
                with open("registered_list.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    if not file_exists:
                        writer.writerow(["Name", "Password", "Email"])
                    writer.writerow([name, pwd, email])
                csv_saved = True
                print("Account saved to CSV")
            except Exception as e:
                print("CSV save error:", e)

            # Save to MySQL
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="login"
                )
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO registered_users (name, password, email)
                    VALUES (%s, %s, %s)
                """, (name, pwd, email))
                conn.commit()
                conn.close()
                mysql_saved = True
                print("Account saved to MySQL")
            except mysql.connector.IntegrityError as e:
                if "Duplicate entry" in str(e):
                    QMessageBox.warning(self, "Error", "This email is already registered!")
                    return
            except mysql.connector.Error as e:
                print("MySQL ERROR:", e)

            if csv_saved or mysql_saved:
                msg = "Account registered successfully!"
                if csv_saved and not mysql_saved:
                    msg += "\
(Saved to CSV only)"
                QMessageBox.information(self, "Success", msg)
                self.name_input.clear()
                self.password_input.clear()
                self.confirm_password_input.clear()
                self.email_input.clear()
            else:
                QMessageBox.critical(self, "Error", "Failed to save account!")

        except Exception as e:
            print("Error in save_account:", e)
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.rect(), self.background_pixmap)

        shape_width = 480
        shape_height = 470
        offset_y = -30
        x = (self.width() - shape_width) / 2
        y = (self.height() - shape_height) / 2 + offset_y

        # Shadow
        for i in range(6):
            alpha = 40 - i * 6
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x + i, y + i, shape_width, shape_height), 25, 25)

        # Glow
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(x - 5, y - 5, shape_width + 10, shape_height + 10), 28, 28)

        # Main shape
        painter.setBrush(QColor("#E1FFD9"))
        painter.setPen(QPen(QColor(0, 0, 0, 40), 2))
        painter.drawRoundedRect(QRectF(x, y, shape_width, shape_height), 25, 25)

        self.wrapper.setGeometry(int(x), int(y), int(shape_width), int(shape_height))
        painter.end()


# ==================== LOGIN WINDOW ====================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM - Login")
        self.setGeometry(100, 100, 600, 500)
        self.initUI()

    def initUI(self):
        # Background
        self.background_pixmap = QPixmap('cherry-blossom-tree-thumb.jpg')
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(600, 500)
            self.background_pixmap.fill(QColor("#A0C4FF"))

        # Wrapper
        self.wrapper = QWidget(self)
        self.inner_layout = QVBoxLayout(self.wrapper)
        self.inner_layout.setAlignment(Qt.AlignCenter)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setSpacing(12)

        # Welcome label
        self.welcome_label = QLabel("WELCOME BACK!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.inner_layout.addWidget(self.welcome_label)

        # Logo
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap('HILOM.png')
        if not self.logo_pixmap.isNull():
            scaled_logo = self.logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            self.logo_label.setText("HILOM")
            self.logo_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.inner_layout.addWidget(self.logo_label)

        # Username
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Username")
        self.surname_input.setStyleSheet("border: 2px solid #ccc; padding: 10px; border-radius: 10px;")
        self.surname_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.surname_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("border: 2px solid #ccc; padding: 10px; border-radius: 10px;")
        self.password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.password_input)
        

        # Login button
        self.login_button = HoverButton("LOGIN")
        self.login_button.setFixedWidth(150)
        self.login_button.setFixedHeight(40)
        self.login_button.clicked.connect(self.check_login)
        self.inner_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)
        

        # Create account link
        self.create_account_link = QPushButton("Create new account")
        self.create_account_link.setFixedWidth(150)
        self.create_account_link.setFont(QFont('Arial', 10))
        self.create_account_link.setStyleSheet("""
            QPushButton {
                color: #000000;
                background-color: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #4CAF50;
            }
        """)
        self.create_account_link.setCursor(Qt.PointingHandCursor)
        self.create_account_link.clicked.connect(self.open_register)
        self.inner_layout.addWidget(self.create_account_link, alignment=Qt.AlignCenter)

        # Fade in
        self.opacity_effect = QGraphicsOpacityEffect()
        self.wrapper.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def open_register(self):
        try:
            self.register_window = RegisterWindow()
            self.register_window.show()
        except Exception as e:
            print("Failed to open RegisterWindow:", e)

    def check_login(self):
        username = self.surname_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password!")
            return
        
        if username.lower() == "admin" and password == "secretadmin":
            self.hide()
            self.admin_window = AdminToggleInterface(self)
            self.admin_window.show()
            return

        try:
            with open('registered_list.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= 2 and row[0] == username and row[1] == password:
                        QMessageBox.information(self, "Success", "Login successful!")
                        print("Login successful!")

                        # Open Dashboard
                        self.dash_board = db.HiLOMMain()
                        self.dash_board.show()

                        # Close login window
                        self.close()
                        return
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "No registered users found. Please create an account first.")
            return

        QMessageBox.warning(self, "Error", "Invalid username or password!")


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.rect(), self.background_pixmap)

        shape_width = 480
        shape_height = 420
        offset_y = -50
        x = (self.width() - shape_width) / 2
        y = (self.height() - shape_height) / 2 + offset_y

        # Shadow
        for i in range(6):
            alpha = 40 - i * 6
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x + i, y + i, shape_width, shape_height), 25, 25)

        # Glow
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(x - 5, y - 5, shape_width + 10, shape_height + 10), 28, 28)

        # Main shape
        painter.setBrush(QColor("#E1FFD9"))
        painter.setPen(QPen(QColor(0, 0, 0, 40), 2))
        painter.drawRoundedRect(QRectF(x, y, shape_width, shape_height), 25, 25)

        self.wrapper.setGeometry(int(x), int(y), int(shape_width), int(shape_height))
        painter.end()


# ==================== MAIN ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())



login.py                                                                                             

import sys
import csv
import os
import mysql.connector
import dash_board as db
import admin as db
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                             QPushButton, QLabel, QGraphicsOpacityEffect, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve


# ==================== HOVER BUTTON ====================
class HoverButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)


# ==================== REGISTER WINDOW ====================
class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM - Register")
        self.setGeometry(100, 100, 600, 550)
        self.initDatabase()
        self.initUI()

    def initUI(self):
        # Background
        self.background_pixmap = QPixmap('cherry-blossom-tree-thumb.jpg')
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(600, 550)
            self.background_pixmap.fill(QColor("#A0C4FF"))

        # Wrapper
        self.wrapper = QWidget(self)
        self.inner_layout = QVBoxLayout(self.wrapper)
        self.inner_layout.setAlignment(Qt.AlignCenter)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setSpacing(12)

        # Title
        self.title_label = QLabel("CREATE ACCOUNT")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.inner_layout.addWidget(self.title_label)

        # Logo
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap('HILOM.png')
        if not self.logo_pixmap.isNull():
            scaled_logo = self.logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            self.logo_label.setText("HILOM")
            self.logo_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.inner_layout.addWidget(self.logo_label)

        # Input style
        input_style = "border: 2px solid #ccc; padding: 10px; border-radius: 10px;"

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        self.name_input.setStyleSheet(input_style)
        self.name_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.name_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet(input_style)
        self.email_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.email_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.password_input)

        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet(input_style)
        self.confirm_password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.confirm_password_input)

        # Register Button
        self.register_button = HoverButton("REGISTER")
        self.register_button.setFixedWidth(150)
        self.register_button.setFixedHeight(40)
        self.register_button.clicked.connect(self.save_account)
        self.inner_layout.addWidget(self.register_button, alignment=Qt.AlignCenter)

        # Back to Login
        self.back_link = QPushButton("Already have an account? Login")
        self.back_link.setFixedWidth(220)
        self.back_link.setFont(QFont('Arial', 10))
        self.back_link.setStyleSheet("""
            QPushButton {
                color: #000000;
                background-color: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #4CAF50;
            }
        """)
        self.back_link.setCursor(Qt.PointingHandCursor)
        self.back_link.clicked.connect(self.back_to_login)
        self.inner_layout.addWidget(self.back_link, alignment=Qt.AlignCenter)

        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.wrapper.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def back_to_login(self):
        self.close()

    def initDatabase(self):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS hilom_db")
            cursor.execute("USE hilom_db")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registered_users(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            conn.commit()
            conn.close()
            print("Database ready: hilom_db")
        except mysql.connector.Error as e:
            print("Database Error:", e)
        except Exception as e:
            print("Unexpected error in initDatabase:", e)

    def validate_inputs(self, name, pwd, confirm, email):
        if not name.strip():
            QMessageBox.warning(self, "Error", "Name cannot be empty!")
            return False
        if not email.strip():
            QMessageBox.warning(self, "Error", "Email cannot be empty!")
            return False
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email!")
            return False
        if not pwd:
            QMessageBox.warning(self, "Error", "Password cannot be empty!")
            return False
        if len(pwd) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters!")
            return False
        if pwd != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return False
        return True

    def save_account(self):
        try:
            name = self.name_input.text()
            pwd = self.password_input.text()
            confirm = self.confirm_password_input.text()
            email = self.email_input.text()

            if not self.validate_inputs(name, pwd, confirm, email):
                return

            csv_saved = False
            mysql_saved = False

            # Save to CSV
            try:
                file_exists = os.path.isfile("registered_list.csv")
                with open("registered_list.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    if not file_exists:
                        writer.writerow(["Name", "Password", "Email"])
                    writer.writerow([name, pwd, email])
                csv_saved = True
                print("Account saved to CSV")
            except Exception as e:
                print("CSV save error:", e)

            # Save to MySQL
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="login"
                )
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO registered_users (name, password, email)
                    VALUES (%s, %s, %s)
                """, (name, pwd, email))
                conn.commit()
                conn.close()
                mysql_saved = True
                print("Account saved to MySQL")
            except mysql.connector.IntegrityError as e:
                if "Duplicate entry" in str(e):
                    QMessageBox.warning(self, "Error", "This email is already registered!")
                    return
            except mysql.connector.Error as e:
                print("MySQL ERROR:", e)

            if csv_saved or mysql_saved:
                msg = "Account registered successfully!"
                if csv_saved and not mysql_saved:
                    msg += "\
(Saved to CSV only)"
                QMessageBox.information(self, "Success", msg)
                self.name_input.clear()
                self.password_input.clear()
                self.confirm_password_input.clear()
                self.email_input.clear()
            else:
                QMessageBox.critical(self, "Error", "Failed to save account!")

        except Exception as e:
            print("Error in save_account:", e)
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.rect(), self.background_pixmap)

        shape_width = 480
        shape_height = 470
        offset_y = -30
        x = (self.width() - shape_width) / 2
        y = (self.height() - shape_height) / 2 + offset_y

        # Shadow
        for i in range(6):
            alpha = 40 - i * 6
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x + i, y + i, shape_width, shape_height), 25, 25)

        # Glow
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(x - 5, y - 5, shape_width + 10, shape_height + 10), 28, 28)

        # Main shape
        painter.setBrush(QColor("#E1FFD9"))
        painter.setPen(QPen(QColor(0, 0, 0, 40), 2))
        painter.drawRoundedRect(QRectF(x, y, shape_width, shape_height), 25, 25)

        self.wrapper.setGeometry(int(x), int(y), int(shape_width), int(shape_height))
        painter.end()


# ==================== LOGIN WINDOW ====================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM - Login")
        self.setGeometry(100, 100, 600, 500)
        self.initUI()

    def initUI(self):
        # Background
        self.background_pixmap = QPixmap('cherry-blossom-tree-thumb.jpg')
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(600, 500)
            self.background_pixmap.fill(QColor("#A0C4FF"))

        # Wrapper
        self.wrapper = QWidget(self)
        self.inner_layout = QVBoxLayout(self.wrapper)
        self.inner_layout.setAlignment(Qt.AlignCenter)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setSpacing(12)

        # Welcome label
        self.welcome_label = QLabel("WELCOME BACK!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setFont(QFont('Arial', 20, QFont.Bold))
        self.inner_layout.addWidget(self.welcome_label)

        # Logo
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap('HILOM.png')
        if not self.logo_pixmap.isNull():
            scaled_logo = self.logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            self.logo_label.setText("HILOM")
            self.logo_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.inner_layout.addWidget(self.logo_label)

        # Username
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Username")
        self.surname_input.setStyleSheet("border: 2px solid #ccc; padding: 10px; border-radius: 10px;")
        self.surname_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.surname_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("border: 2px solid #ccc; padding: 10px; border-radius: 10px;")
        self.password_input.setFixedWidth(300)
        self.inner_layout.addWidget(self.password_input)
        

        # Login button
        self.login_button = HoverButton("LOGIN")
        self.login_button.setFixedWidth(150)
        self.login_button.setFixedHeight(40)
        self.login_button.clicked.connect(self.check_login)
        self.inner_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)
        

        # Create account link
        self.create_account_link = QPushButton("Create new account")
        self.create_account_link.setFixedWidth(150)
        self.create_account_link.setFont(QFont('Arial', 10))
        self.create_account_link.setStyleSheet("""
            QPushButton {
                color: #000000;
                background-color: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #4CAF50;
            }
        """)
        self.create_account_link.setCursor(Qt.PointingHandCursor)
        self.create_account_link.clicked.connect(self.open_register)
        self.inner_layout.addWidget(self.create_account_link, alignment=Qt.AlignCenter)

        # Fade in
        self.opacity_effect = QGraphicsOpacityEffect()
        self.wrapper.setGraphicsEffect(self.opacity_effect)
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.start()

    def open_register(self):
        try:
            self.register_window = RegisterWindow()
            self.register_window.show()
        except Exception as e:
            print("Failed to open RegisterWindow:", e)

    def check_login(self):
        username = self.surname_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password!")
            return
        
        if username.lower() == "admin" and password == "secretadmin":
            self.hide()
            self.admin_window = AdminToggleInterface(self)
            self.admin_window.show()
            return

        try:
            with open('registered_list.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= 2 and row[0] == username and row[1] == password:
                        QMessageBox.information(self, "Success", "Login successful!")
                        print("Login successful!")

                        # Open Dashboard
                        self.dash_board = db.HiLOMMain()
                        self.dash_board.show()

                        # Close login window
                        self.close()
                        return
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "No registered users found. Please create an account first.")
            return

        QMessageBox.warning(self, "Error", "Invalid username or password!")


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.rect(), self.background_pixmap)

        shape_width = 480
        shape_height = 420
        offset_y = -50
        x = (self.width() - shape_width) / 2
        y = (self.height() - shape_height) / 2 + offset_y

        # Shadow
        for i in range(6):
            alpha = 40 - i * 6
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x + i, y + i, shape_width, shape_height), 25, 25)

        # Glow
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(x - 5, y - 5, shape_width + 10, shape_height + 10), 28, 28)

        # Main shape
        painter.setBrush(QColor("#E1FFD9"))
        painter.setPen(QPen(QColor(0, 0, 0, 40), 2))
        painter.drawRoundedRect(QRectF(x, y, shape_width, shape_height), 25, 25)

        self.wrapper.setGeometry(int(x), int(y), int(shape_width), int(shape_height))
        painter.end()


# ==================== MAIN ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
