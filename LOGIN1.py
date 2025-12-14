import sys
import csv
import os
import mysql.connector
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
                             QPushButton, QLabel, QGraphicsOpacityEffect, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve


# ==================== ADMIN PANEL ====================
from admin import AdminPanel


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
        self.background_pixmap = QPixmap('cherry-blossom.jpg')
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
        self.logo_pixmap = QPixmap('hilom.jpg')
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
            cursor.execute("CREATE DATABASE IF NOT EXISTS HILOM")
            cursor.execute("USE HILOM")
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
                    database="HILOM"
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
        self.background_pixmap = QPixmap('cherry-blossom.jpg')
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
            self.register_window.showFullScreen()
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
            self.admin_window = AdminPanel()
            self.admin_window.show()
            return

        try:
            with open('registered_list.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) >= 2 and row[0] == username and row[1] == password:
                        QMessageBox.information(self, "Success", "Login successful!")

                        # Open Dashboard app
                        import os
                        os.startfile("dashboard.py")
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