import sys
import csv
import random
import os
import webbrowser
from urllib.parse import quote_plus
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QTextEdit, QLineEdit,
    QMessageBox, QGraphicsDropShadowEffect, QGridLayout, QTabWidget, QListWidget, QListWidgetItem, QToolBar, QAction, QScrollArea, QComboBox, QCalendarWidget, QCheckBox
)
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF, QDate, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import mysql.connector


# ---------- Log History ----------
def log_history(cat, item):
    from datetime import datetime
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    with open("history.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([cat, item, date, time])


# ---------- MySQL Helper ----------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # <-- your MySQL username
        password="",        # <-- your MySQL password
        database="hilom",   # <-- make sure this database exists
        connection_timeout=5  # 5 second timeout
    )

def init_database():
    # For now, skip MySQL initialization to avoid hanging
    print("Skipping MySQL initialization for now.")
    global MYSQL_AVAILABLE
    MYSQL_AVAILABLE = False
    print("Database initialization skipped. Appointments will be saved to history only.")

MYSQL_AVAILABLE = True

def save_appointment(info):
    global MYSQL_AVAILABLE   # ✅ REQUIRED

    if MYSQL_AVAILABLE:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointments(
                    patient_name, age, contact, gender, address, concern,
                    doctor_id, hospital_id, schedule, time_slot,
                    consultation_type, price
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                info['name'], info['age'], info['contact'], info['gender'],
                info['address'], info['concern'], info['doctor_id'],
                info['hospital_id'], info['schedule'], info['time_slot'],
                info['consultation_type'], info['price']
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print("Appointment saved to MySQL!")

        except mysql.connector.Error as e:
            print(f"Failed to save to MySQL: {e}. Saving to history only.")
            MYSQL_AVAILABLE = False  # now safe ✅
    else:
        print("MySQL not available. Appointment details logged to history.")
    
    # Always log to history
    log_history("appointment", f"Appointment for {info['name']} - {info['consultation_type']} - ${info['price']}")

# ---------- Sample Data ----------
HOSPITALS = [
    {"id":1,"name":"South Haven Mental Wellness Center", "address":"Nasugbu, Batangas, Brgy Uno", "rating":4.5, "distance":"1.8 km", "open_hours":"7:00 AM - 10:00 PM"},
    {"id":2,"name":"We Care Hospital", "address":"Nasugbu, Batangas, Brgy Dos", "rating":4.1, "distance":"2.3 km", "open_hours":"8:00 AM - 9:00 PM"},
    {"id":3,"name":"Find Hope Clinic", "address":"Nasugbu, Batangas, Brgy Cinco", "rating":4.3, "distance":"3.5 km", "open_hours":"6:00 AM - 11:00 PM"},
]

DOCTORS = [
    {"id":1,"name":"Dr Miguel Santos", "years":6, "rating":4.7, "specialty":"CBT, personality disorders, trauma-focused"},
    {"id":2,"name":"Ms Larah Velasco", "years":4, "rating":4.4, "specialty":"Works with young adults"},
    {"id":3,"name":"Dr Arianne Dela Cruz", "years":8, "rating":4.5, "specialty":"CBT, personality & trauma"},
]


# ==========================================
#  ANIMATION CLASS (For Journal)
# ==========================================
class Petal:
    """Floating petal for animation."""

    def __init__(self, x, y, size, speed):
        self.pos = QPointF(x, y)
        self.size = size
        self.speed = speed
        self.angle = random.uniform(0, 360)

    def fall(self, max_width, max_height):
        self.pos.setY(self.pos.y() + self.speed)
        self.pos.setX(self.pos.x() + 0.5 * random.choice([-1, 1]))
        self.angle += 2

        # Reset if it goes off screen
        if self.pos.y() > max_height:
            self.pos.setY(-10)
            self.pos.setX(random.randint(0, max_width))


# ==========================================
#  PAGE 1: DASHBOARD (HOME)
# ==========================================
class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        # Layout setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Background for this specific page
        bg_path = "cherry-blossom.jpg"
        # We set the ID to force the style only on this widget
        self.setObjectName("DashboardPage")
        self.setStyleSheet(f"""
            QWidget#DashboardPage {{
                background-image: url('{bg_path}');
                background-repeat: no-repeat;
                background-position: center;
            }}
        """)

        # --- Header ---
        header_row = QHBoxLayout()
        title = QLabel("WELCOME BACK!")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        header_row.addWidget(title)
        header_row.addStretch()

        notif_btn = QPushButton("Notifications")
        notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        notif_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 8px 12px;
                border-radius: 8px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        header_row.addWidget(notif_btn)
        self.layout.addLayout(header_row)

        # --- Feelings Section ---
        feelings_card = QFrame()
        feelings_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.9);
                border-radius: 15px;
            }
        """)
        f_layout = QVBoxLayout(feelings_card)
        f_layout.setContentsMargins(20, 20, 20, 20)

        subtitle = QLabel("How do you feel today?")
        subtitle.setFont(QFont("Segoe UI", 16))
        subtitle.setStyleSheet("color: #455a64; background: transparent;")
        f_layout.addWidget(subtitle)

        feelings_row = QHBoxLayout()
        feelings = ["CALM", "TIRED", "OVERWHELMED", "HOPEFUL", "GRATEFUL", "DRAINED"]
        for feeling in feelings:
            fb = QPushButton(feeling)
            fb.setCursor(Qt.CursorShape.PointingHandCursor)
            fb.setFixedHeight(40)
            fb.setCheckable(True)
            fb.setStyleSheet("""
                QPushButton {
                    background: #f1f5f9;
                    border-radius: 10px;
                    color: #223;
                    font-weight: 500;
                }
                QPushButton:hover { background: #e8f0fb; }
                QPushButton:checked {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8ac6ff, stop:1 #5aa9ff);
                    color: #fff;
                }
            """)
            feelings_row.addWidget(fb)
        f_layout.addLayout(feelings_row)
        self.layout.addWidget(feelings_card)

        # --- Quote Section ---
        quote_card = QFrame()
        quote_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
            }
        """)
        q_layout = QVBoxLayout(quote_card)
        q_layout.setContentsMargins(20, 20, 20, 20)

        # Quote Logic
        quotes = []
        try:
            if os.path.exists("day-by-day.csv"):
                with open("day-by-day.csv", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row: quotes.append(row[0].strip())
        except Exception as e:
            print("Error reading CSV:", e)

        selected_quote = random.choice(quotes) if quotes else "Every day is a fresh start."

        quote_label = QLabel(f'"{selected_quote}"')
        quote_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        quote_label.setWordWrap(True)
        quote_label.setStyleSheet("color: #37474f; background: transparent;")
        q_layout.addWidget(quote_label)

        source_label = QLabel("— Daily Inspiration")
        source_label.setStyleSheet("color: #78909c; font-size: 12px; background: transparent;")
        q_layout.addWidget(source_label)

        self.layout.addWidget(quote_card)
        self.layout.addStretch()


# ==========================================
#  PAGE 2: JOURNAL (WITH ANIMATION)
# ==========================================
class JournalPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")

        # Background Image Loading
        self.bg_pixmap = QPixmap("cherry-blossom.jpg")

        # Petal Animation Setup
        self.petals = [
            Petal(random.randint(0, 800), random.randint(0, 600), random.randint(10, 20), random.uniform(1, 3)) for _ in
            range(25)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # ~20 FPS

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        header = QLabel("JOURNAL")
        header.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        header.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(header)

        # Card container
        journal_card = QFrame()
        journal_card.setStyleSheet("background-color: rgba(255,255,255,0.7); border-radius: 20px;")

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 50))
        journal_card.setGraphicsEffect(shadow)

        j_layout = QVBoxLayout(journal_card)
        j_layout.setContentsMargins(25, 25, 25, 25)
        j_layout.setSpacing(10)


        # Date
        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.date_field = QLineEdit(today)
        self.date_field.setStyleSheet("background: #f0f0f0; border-radius: 5px; padding: 5px; color: black;")
        date_label = QLabel("DATE")
        date_label.setStyleSheet("background-color: #f0f0f0; color: black; border-radius: 5px; padding: 5px;")  # Set background color and text color
        j_layout.addWidget(date_label)

        # Title
        self.title_field = QLineEdit()
        self.title_field.setPlaceholderText("Title....")
        self.title_field.setStyleSheet("background: #f0f0f0; border-radius: 5px; padding: 5px; color: black;")
        title_label = QLabel("Title")
        title_label.setStyleSheet("background-color: #f0f0f0; color: black; border-radius: 5px; padding: 5px;")  # Set background color and text color
        j_layout.addWidget(title_label)
        j_layout.addWidget(self.title_field)

        # Feelings Field & Emojis
        self.feel_field = QLineEdit()
        self.feel_field.setPlaceholderText("How do you feel?")
        self.feel_field.setStyleSheet("background: #f0f0f0; border-radius: 5px; padding: 5px; color: black;")  # Change background to a light gray
        feel_label = QLabel("Mood")
        feel_label.setStyleSheet("background-color: #f0f0f0; color: black; border-radius: 5px; padding: 5px;")  # Set background color and text color
        j_layout.addWidget(feel_label)

        emoji_layout = QHBoxLayout()
        emoji_map = {"🙂": "Happy", "😢": "Sad", "😭": "Crying", "😐": "Neutral", "😔": "Disappointed"}
        for emoji, feel in emoji_map.items():
            btn = QPushButton(emoji)
            btn.setFixedSize(40, 40)
            btn.setFont(QFont("Segoe UI", 16))
            btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; } QPushButton:hover { font-size: 20px; }")
            btn.clicked.connect(lambda checked, f=feel: self.feel_field.setText(f))
            emoji_layout.addWidget(btn)
        j_layout.addLayout(emoji_layout)

        # Text Area
        j_layout.addWidget(QLabel("Write your thoughts..."))
        self.main_text = QTextEdit()
        self.main_text.setFont(QFont("Segoe UI", 20))
        self.main_text.setStyleSheet("background: #f0f0f0; border-radius: 5px; padding: 5px; color: black;")
        self.main_text.setCursorWidth(0)
        j_layout.addWidget(self.main_text)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("SAVE")
        save_btn.setStyleSheet(
            "background-color:#a0d5c5; color:white; font-weight:bold; border-radius:8px; padding:8px;")
        save_btn.clicked.connect(self.save_journal)

        del_btn = QPushButton("CLEAR")
        del_btn.setStyleSheet(
            "background-color:#f48a8a; color:white; font-weight:bold; border-radius:8px; padding:8px;")
        del_btn.clicked.connect(self.clear_journal)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(del_btn)
        j_layout.addLayout(btn_layout)

        layout.addWidget(journal_card)

    def update_animation(self):
        # Trigger a repaint to move petals
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # 1. Draw Background
        if not self.bg_pixmap.isNull():
            scaled_bg = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation)
            # Center the image
            x = (self.width() - scaled_bg.width()) // 2
            y = (self.height() - scaled_bg.height()) // 2
            painter.drawPixmap(x, y, scaled_bg)
        else:
            painter.fillRect(self.rect(), QColor("#e0f2f7"))

        # 2. Draw Petals
        brush = QBrush(QColor(255, 192, 203, 180))  # Pink, semi-transparent
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)

        for petal in self.petals:
            painter.save()
            painter.translate(petal.pos)
            painter.rotate(petal.angle)
            w = int(petal.size)
            h = int(petal.size / 2)
            painter.drawEllipse(int(-w / 2), int(-h / 2), w, h)
            painter.restore()

            # Update petal position for next frame
            petal.fall(self.width(), self.height())

    def save_journal(self):
        content = self.main_text.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Warning", "Journal entry is empty!")
            return
        QMessageBox.information(self, "Success", "Journal entry saved successfully!")

    def clear_journal(self):
        self.title_field.clear()
        self.feel_field.clear()
        self.main_text.clear()


# ---------- Favorite Page ----------
class FavoritePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5d0e0;")  # soft pink background
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Screen title
        title = QLabel("Favorite")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        self.layout.addWidget(title)

        # Tabs
        self.tab_layout = QHBoxLayout()
        self.tabs = {}
        tab_names = ["Music", "Video", "Podcast", "Book", "Journal"]
        for tab in tab_names:
            btn = QPushButton(tab)
            btn.setFont(QFont("Arial", 14))
            btn.setCheckable(True)
            if tab == "Music":  # Default active tab
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e0a0c0, stop:1 #c080a0);
                        color: white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.8);
                        color: #234;
                        border-radius: 10px;
                        padding: 10px 20px;
                    }
                    QPushButton:hover { background: rgba(255, 255, 255, 1); }
                """)
            btn.clicked.connect(lambda checked, t=tab: self.select_tab(t))
            self.tabs[tab] = btn
            self.tab_layout.addWidget(btn)
        self.layout.addLayout(self.tab_layout)

        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.9);
                border-radius: 15px;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # Lists for each tab
        self.music_list = QListWidget()
        self.video_list = QListWidget()
        self.podcast_list = QListWidget()
        self.book_list = QListWidget()
        self.journal_list = QListWidget()

        # Placeholder content
        self.placeholder = QLabel("No favorite content loaded yet")
        self.placeholder.setFont(QFont("Arial", 16))
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: gray;")
        self.content_layout.addWidget(self.placeholder)

        self.layout.addWidget(self.content_frame)

        self.load_favorites()

    def select_tab(self, tab_name):
        for name, btn in self.tabs.items():
            if name == tab_name:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e0a0c0, stop:1 #c080a0);
                        color: white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-weight: bold;
                    }
                """)
                btn.setChecked(True)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.8);
                        color: #234;
                        border-radius: 10px;
                        padding: 10px 20px;
                    }
                    QPushButton:hover { background: rgba(255, 255, 255, 1); }
                """)
                btn.setChecked(False)
        
        # Clear content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add the appropriate list
        if tab_name == "Music":
            if self.music_list.count() > 0:
                self.content_layout.addWidget(self.music_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No favorite music loaded yet")
        elif tab_name == "Video":
            if self.video_list.count() > 0:
                self.content_layout.addWidget(self.video_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No favorite videos loaded yet")
        elif tab_name == "Podcast":
            if self.podcast_list.count() > 0:
                self.content_layout.addWidget(self.podcast_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No favorite podcasts loaded yet")
        elif tab_name == "Book":
            if self.book_list.count() > 0:
                self.content_layout.addWidget(self.book_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No favorite books loaded yet")
        elif tab_name == "Journal":
            if self.journal_list.count() > 0:
                self.content_layout.addWidget(self.journal_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No favorite journals loaded yet")

    def load_favorites(self):
        try:
            with open("favorites.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2:
                        cat, item = row
                        if cat == "music":
                            self.music_list.addItem(QListWidgetItem(item))
                        elif cat == "video":
                            self.video_list.addItem(QListWidgetItem(item))
                        elif cat == "book":
                            self.book_list.addItem(QListWidgetItem(item))
        except FileNotFoundError:
            pass


# ---------- History Page ----------
class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5d0e0;")  # soft pink background
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Screen title
        title = QLabel("History")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        self.layout.addWidget(title)

        # Tabs
        self.tab_layout = QHBoxLayout()
        self.tabs = {}
        tab_names = ["Music", "Video", "Journal", "Appointment"]
        for tab in tab_names:
            btn = QPushButton(tab)
            btn.setFont(QFont("Arial", 14))
            btn.setCheckable(True)
            if tab == "Music":  # Default active tab
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e0a0c0, stop:1 #c080a0);
                        color: white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.8);
                        color: #234;
                        border-radius: 10px;
                        padding: 10px 20px;
                    }
                    QPushButton:hover { background: rgba(255, 255, 255, 1); }
                """)
            btn.clicked.connect(lambda checked, t=tab: self.select_tab(t))
            self.tabs[tab] = btn
            self.tab_layout.addWidget(btn)
        self.layout.addLayout(self.tab_layout)

        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.9);
                border-radius: 15px;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # Lists for each tab
        self.music_list = QListWidget()
        self.video_list = QListWidget()
        self.journal_list = QListWidget()
        self.appointment_list = QListWidget()

        # Placeholder content
        self.placeholder = QLabel("No history loaded yet")
        self.placeholder.setFont(QFont("Arial", 16))
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: gray;")
        self.content_layout.addWidget(self.placeholder)

        self.layout.addWidget(self.content_frame)

        self.load_history()

    def select_tab(self, tab_name):
        for name, btn in self.tabs.items():
            if name == tab_name:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e0a0c0, stop:1 #c080a0);
                        color: white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-weight: bold;
                    }
                """)
                btn.setChecked(True)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.8);
                        color: #234;
                        border-radius: 10px;
                        padding: 10px 20px;
                    }
                    QPushButton:hover { background: rgba(255, 255, 255, 1); }
                """)
                btn.setChecked(False)
        
        # Clear content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add the appropriate list
        if tab_name == "Music":
            if self.music_list.count() > 0:
                self.content_layout.addWidget(self.music_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No music history yet")
        elif tab_name == "Video":
            if self.video_list.count() > 0:
                self.content_layout.addWidget(self.video_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No video history yet")
        elif tab_name == "Journal":
            if self.journal_list.count() > 0:
                self.content_layout.addWidget(self.journal_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No journal history yet")
        elif tab_name == "Appointment":
            if self.appointment_list.count() > 0:
                self.content_layout.addWidget(self.appointment_list)
            else:
                self.content_layout.addWidget(self.placeholder)
                self.placeholder.setText("No appointment history yet")

    def load_history(self):
        try:
            with open("history.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 4:
                        cat, item, date, time = row
                        entry = f"{item} - {date} {time}"
                        if cat == "music":
                            self.music_list.addItem(QListWidgetItem(entry))
                        elif cat == "video":
                            self.video_list.addItem(QListWidgetItem(entry))
                        elif cat == "journal":
                            self.journal_list.addItem(QListWidgetItem(entry))
                        elif cat == "appointment":
                            self.appointment_list.addItem(QListWidgetItem(entry))
        except FileNotFoundError:
            pass


# ---------- Profile Page ----------
class ProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5d0e0;")  # soft pink background
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Screen title
        title = QLabel("Profile")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        self.layout.addWidget(title)

        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.9);
                border-radius: 15px;
                border: 1px solid rgba(0,0,0,0.1);
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # Stacked layout for sub-screens
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)

        # Sub-screens
        self.account_update_screen = self.create_account_update_screen()
        self.profile_info_screen = self.create_profile_info_screen()
        self.notification_screen = self.create_notification_screen()
        self.settings_menu = self.create_settings_menu()

        # Add screens to stacked layout
        self.stacked_widget.addWidget(self.settings_menu)
        self.stacked_widget.addWidget(self.account_update_screen)
        self.stacked_widget.addWidget(self.profile_info_screen)
        self.stacked_widget.addWidget(self.notification_screen)

        # Start with settings menu
        self.stacked_widget.setCurrentWidget(self.settings_menu)

        self.layout.addWidget(self.content_frame)

    def create_settings_menu(self):
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a9e, stop:1 #fecfef);
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 50))
        screen.setGraphicsEffect(shadow)
        layout = QVBoxLayout(screen)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Buttons for settings
        buttons_info = [("🔐 Account Login", self.account_update_screen),
                        ("👤 Profile Info", self.profile_info_screen),
                        ("🔔 Notifications", self.notification_screen)]
        for text, target_screen in buttons_info:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.9);
                    color: #333;
                    border-radius: 12px;
                    padding: 15px 25px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 1);
                }
            """)
            btn.clicked.connect(lambda checked, screen=target_screen: self.stacked_widget.setCurrentWidget(screen))
            layout.addWidget(btn)

        layout.addStretch()
        return screen

    def create_account_update_screen(self):
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a9e, stop:1 #fecfef);
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 50))
        screen.setGraphicsEffect(shadow)
        layout = QVBoxLayout(screen)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🔐 Account Update")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("New Username")
        self.new_username.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        layout.addWidget(self.new_username)

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password")
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        layout.addWidget(self.new_password)

        update_btn = QPushButton("Update Account")
        update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                color: white;
                border-radius: 14px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
        """)
        update_btn.clicked.connect(self.update_account)
        layout.addWidget(update_btn)

        back_btn = QPushButton("⬅️ Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_menu))
        layout.addWidget(back_btn)

        layout.addStretch()
        return screen

    def update_account(self):
        new_user = self.new_username.text().strip()
        new_pass = self.new_password.text().strip()
        if not new_user or not new_pass:
            QMessageBox.warning(self, "Update Failed", "Please fill in all fields.")
            return
        # Mock update
        QMessageBox.information(self, "Update Successful", "Account updated!")
        self.stacked_widget.setCurrentWidget(self.settings_menu)

    def create_profile_info_screen(self):
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a9e, stop:1 #fecfef);
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 50))
        screen.setGraphicsEffect(shadow)
        layout = QVBoxLayout(screen)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("👤 Profile Information")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Profile picture placeholder
        profile_pic = QLabel("U")
        profile_pic.setFont(QFont("Arial", 48, QFont.Bold))
        profile_pic.setAlignment(Qt.AlignCenter)
        profile_pic.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 50px;
                color: #333;
                min-width: 100px;
                min-height: 100px;
                max-width: 100px;
                max-height: 100px;
            }
        """)
        layout.addWidget(profile_pic, alignment=Qt.AlignCenter)

        info = QLabel("Name: User\nEmail: user@example.com\nJoined: 2023")
        info.setStyleSheet("color: white; font-size: 16px; font-weight: bold; text-align: center;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        back_btn = QPushButton("⬅️ Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_menu))
        layout.addWidget(back_btn)

        layout.addStretch()
        return screen

    def create_notification_screen(self):
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a9e, stop:1 #fecfef);
                border-radius: 15px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 50))
        screen.setGraphicsEffect(shadow)
        layout = QVBoxLayout(screen)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🔔 Notifications")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Notification settings
        email_notif = QCheckBox("Email Notifications")
        email_notif.setChecked(True)
        email_notif.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #55c79a;
            }
        """)
        layout.addWidget(email_notif)

        push_notif = QCheckBox("Push Notifications")
        push_notif.setChecked(True)
        push_notif.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #55c79a;
            }
        """)
        layout.addWidget(push_notif)

        reminder_notif = QCheckBox("Appointment Reminders")
        reminder_notif.setChecked(True)
        reminder_notif.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #55c79a;
            }
        """)
        layout.addWidget(reminder_notif)

        back_btn = QPushButton("⬅️ Back")
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_menu))
        layout.addWidget(back_btn)

        layout.addStretch()
        return screen


# ---------- Appointment Screens ----------
class LocationEntry(QWidget):
    def __init__(self, goto_list_cb):
        super().__init__()
        self.goto_list_cb = goto_list_cb
        self._build()
    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel("ENTER LOCATION"); title.setObjectName('title')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        subtitle = QLabel("Find nearby hospitals and clinics"); subtitle.setStyleSheet('color:#666; font-size:14px')
        form = QVBoxLayout()
        form.setSpacing(15)
        self.city = QLineEdit(); self.city.setPlaceholderText('City *')
        self.city.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.province = QLineEdit(); self.province.setPlaceholderText('Province *')
        self.province.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.zipcode = QLineEdit(); self.zipcode.setPlaceholderText('Zip Code *')
        self.zipcode.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        form.addWidget(self.city); form.addWidget(self.province); form.addWidget(self.zipcode)
        btn = QPushButton('Find nearby hospitals')
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                color: white;
                border-radius: 14px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
            QPushButton:pressed { background: #2e7d32; }
        """)
        btn.clicked.connect(self.on_find)
        layout.addWidget(title); layout.addWidget(subtitle); layout.addLayout(form); layout.addStretch(); layout.addWidget(btn, alignment=Qt.AlignRight)
        self.setLayout(layout)
    def on_find(self):
        if not self.city.text().strip() or not self.province.text().strip() or not self.zipcode.text().strip():
            QMessageBox.warning(self, "Input Error", "Please fill in all location fields (City, Province, Zip Code).")
        else:
            self.goto_list_cb()

class HospitalList(QWidget):
    def __init__(self, goto_detail_cb, back_cb):
        super().__init__()
        self.goto_detail_cb = goto_detail_cb
        self.back_cb = back_cb
        self._build()
    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel('Nearby Hospitals & Clinics')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        layout.addWidget(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        content = QWidget(); v = QVBoxLayout()
        v.setSpacing(15)
        for h in HOSPITALS:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.9);
                    border-radius: 15px;
                    border: 1px solid rgba(0,0,0,0.1);
                }
                QFrame:hover {
                    background: rgba(255,255,255,1);
                    border: 2px solid #55c79a;
                }
            """)
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(20, 20, 20, 20)
            header = QHBoxLayout()
            name = QLabel(h['name']); name.setStyleSheet('font-size:18px; font-weight:bold; color:#004c3f; background: transparent;')
            rating = QLabel(f"★ {h['rating']}"); rating.setStyleSheet('font-size:16px; color:#c79f10; font-weight:bold; background: transparent;')
            header.addWidget(name)
            header.addStretch()
            header.addWidget(rating)
            addr = QLabel(f"📍 {h['address']} — {h['distance']}"); addr.setStyleSheet('color:#666; font-size:12px; margin-top:5px; background: transparent;')
            hours = QLabel(f"🕐 {h['open_hours']}"); hours.setStyleSheet('color:#666; font-size:12px; margin-top:2px; background: transparent;')
            view_btn = QPushButton('View Details')
            view_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                    color: white;
                    border-radius: 10px;
                    padding: 8px 16px;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
            """)
            view_btn.clicked.connect(lambda _,x=h: self.goto_detail_cb(x))
            card_layout.addLayout(header)
            card_layout.addWidget(addr)
            card_layout.addWidget(hours)
            card_layout.addWidget(view_btn, alignment=Qt.AlignCenter)
            card.setLayout(card_layout); v.addWidget(card)
        content.setLayout(v); scroll.setWidget(content)
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)
        layout.addWidget(scroll); layout.addWidget(back, alignment=Qt.AlignRight)
        self.setLayout(layout)

class HospitalDetail(QWidget):
    def __init__(self, hospital, goto_doctors_cb, back_cb):
        super().__init__()
        self.hospital = hospital
        self.goto_doctors_cb = goto_doctors_cb
        self.back_cb = back_cb
        # Year-over-year ratings data (2020-2025)
        self.yearly_ratings = [3.8, 4.1, 4.3, 4.5, 4.2, 4.7]  # Sample ratings for each year
        self.progress = 0.0
        self._build()
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_graph)
        self.timer.start(50)

    def draw_graph(self):
        pixmap = QPixmap(500, 150)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)

        # Title
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(180, 20, "Year-over-Year Patient Satisfaction")

        # Draw axes
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(50, 120, 450, 120)  # x-axis
        painter.drawLine(50, 30, 50, 120)    # y-axis

        # Axis labels
        painter.setFont(QFont("Arial", 10))
        painter.drawText(450, 135, "Year")
        painter.drawText(20, 25, "Rating")

        # Y-axis scale (1-5 stars)
        painter.setPen(QPen(Qt.gray, 1))
        for i in range(1, 6):
            y = 120 - (i * 18)
            painter.drawLine(45, y, 50, y)
            painter.drawText(30, y + 5, str(i))

        # X-axis years
        years = ["2020", "2021", "2022", "2023", "2024", "2025"]
        for i, year in enumerate(years):
            x = 80 + (i * 60)
            painter.drawLine(x, 115, x, 120)
            painter.drawText(x - 15, 135, year)

        # Convert ratings to points (rating 1-5 mapped to y-coordinates)
        points = []
        for i, rating in enumerate(self.yearly_ratings):
            x = 80 + (i * 60)
            y = 120 - (rating * 18)  # 18 pixels per rating point
            points.append((x, y))

        # Draw lines smoothly
        painter.setPen(QPen(Qt.blue, 3))
        for i in range(len(points) - 1):
            if i < int(self.progress):
                painter.drawLine(int(points[i][0]), int(points[i][1]), int(points[i + 1][0]), int(points[i + 1][1]))
            elif i == int(self.progress):
                frac = self.progress - int(self.progress)
                x2 = int(points[i][0] + frac * (points[i + 1][0] - points[i][0]))
                y2 = int(points[i][1] + frac * (points[i + 1][1] - points[i][1]))
                painter.drawLine(int(points[i][0]), int(points[i][1]), x2, y2)

        # Draw points up to current progress
        painter.setPen(QPen(Qt.red, 1))
        painter.setBrush(Qt.red)
        for i in range(int(self.progress) + 1):
            if i < len(points):
                painter.drawEllipse(int(points[i][0]) - 4, int(points[i][1]) - 4, 8, 8)

        # Draw rating values above points
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 9))
        for i in range(int(self.progress) + 1):
            if i < len(self.yearly_ratings):
                rating_text = f"{self.yearly_ratings[i]}★"
                painter.drawText(int(points[i][0]) - 10, int(points[i][1]) - 10, rating_text)

        painter.end()
        self.graph.setPixmap(pixmap)

    def animate_graph(self):
        self.progress += 0.1
        self.draw_graph()
        if self.progress >= len(self.yearly_ratings) - 1:
            self.timer.stop()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Hospital name and rating
        name = QLabel(self.hospital['name'])
        name.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        name.setStyleSheet("color: #1f2d3d; background: transparent;")

        addr = QLabel(self.hospital['address'])
        addr.setStyleSheet('color:#666; font-size:14px; background: transparent;')

        hours = QLabel(f"🕐 Operating Hours: {self.hospital['open_hours']}")
        hours.setStyleSheet('color:#666; font-size:14px; margin-top:5px; background: transparent;')

        top_row = QHBoxLayout()
        top_row.addWidget(name)
        top_row.addStretch()

        rating_value = round(self.hospital['rating'] + random.uniform(-0.2,0.2),1)
        rating = QLabel(f"★ {rating_value} ({len(self.yearly_ratings)} reviews)")
        rating.setStyleSheet('font-size:18px; color:#c79f10; background: transparent;')
        top_row.addWidget(rating)

        # Year-over-year ratings graph
        self.graph = QLabel()
        self.graph.setFixedHeight(150)
        self.graph.setFixedWidth(500)
        self.graph.setStyleSheet('border:2px solid #e0e0e0; background: white; border-radius: 10px; padding: 10px;')
        self.draw_graph()  # initial draw

        # Patient comments section
        comments_title = QLabel("Patient Reviews & Comments")
        comments_title.setFont(QFont("Arial", 14, QFont.Bold))
        comments_title.setStyleSheet("color: #1f2d3d; margin-top: 10px;")

        comments_scroll = QScrollArea()
        comments_scroll.setWidgetResizable(True)
        comments_scroll.setFixedHeight(120)
        comments_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: #f9f9f9;
            }
        """)

        comments_widget = QWidget()
        comments_layout = QVBoxLayout(comments_widget)
        comments_layout.setSpacing(8)

        # Sample patient comments
        patient_comments = [
            {"name": "Maria S.", "rating": 5, "comment": "Excellent care and very professional staff. The therapy sessions really helped me manage my anxiety.", "date": "2025-01-15"},
            {"name": "John D.", "rating": 5, "comment": "Dr. Santos is amazing! The CBT approach worked wonders for my depression. Highly recommend!", "date": "2024-12-08"},
            {"name": "Lisa M.", "rating": 4, "comment": "Great facility with caring staff. Wait times could be shorter but overall very satisfied.", "date": "2024-11-22"},
            {"name": "Robert K.", "rating": 5, "comment": "Life-changing experience. The personalized treatment plan made all the difference.", "date": "2024-10-30"},
            {"name": "Anna P.", "rating": 4, "comment": "Very supportive environment. Staff goes above and beyond to help patients feel comfortable.", "date": "2024-09-15"},
            {"name": "Michael T.", "rating": 5, "comment": "Outstanding mental health support. The group therapy sessions were particularly helpful.", "date": "2024-08-20"}
        ]

        for comment in patient_comments:
            comment_frame = QFrame()
            comment_frame.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)

            comment_layout = QVBoxLayout(comment_frame)
            comment_layout.setContentsMargins(8, 8, 8, 8)

            # Header with name, rating, and date
            header_layout = QHBoxLayout()
            name_label = QLabel(f"{comment['name']}")
            name_label.setFont(QFont("Arial", 11, QFont.Bold))
            name_label.setStyleSheet("color: #2e7d32;")

            rating_label = QLabel("★" * comment['rating'])
            rating_label.setStyleSheet("color: #ffc107; font-size: 12px;")

            date_label = QLabel(comment['date'])
            date_label.setStyleSheet("color: #666; font-size: 10px;")

            header_layout.addWidget(name_label)
            header_layout.addWidget(rating_label)
            header_layout.addStretch()
            header_layout.addWidget(date_label)

            # Comment text
            comment_text = QLabel(comment['comment'])
            comment_text.setWordWrap(True)
            comment_text.setStyleSheet("color: #333; font-size: 11px; line-height: 1.4;")

            comment_layout.addLayout(header_layout)
            comment_layout.addWidget(comment_text)

            comments_layout.addWidget(comment_frame)

        comments_scroll.setWidget(comments_widget)

        # Navigation buttons
        details_btn = QPushButton('View Available Doctors')
        details_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                color: white;
                border-radius: 14px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
        """)
        details_btn.clicked.connect(self.goto_doctors_cb)

        back = QPushButton('← Back to Hospital List')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)

        # Add all elements to main layout
        layout.addLayout(top_row)
        layout.addWidget(addr)
        layout.addWidget(hours)
        layout.addWidget(self.graph, alignment=Qt.AlignCenter)
        layout.addWidget(comments_title)
        layout.addWidget(comments_scroll)
        layout.addStretch()
        layout.addWidget(details_btn, alignment=Qt.AlignCenter)
        layout.addWidget(back, alignment=Qt.AlignLeft)

        self.setLayout(layout)

class DoctorSelection(QWidget):
    def __init__(self, goto_book_cb, back_cb):
        super().__init__()
        self.goto_book_cb = goto_book_cb
        self.back_cb = back_cb
        self._build()
    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel('Select Doctor')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        layout.addWidget(title)
        shuffled_doctors = random.sample(DOCTORS, len(DOCTORS))
        grid = QGridLayout()
        grid.setSpacing(20)
        for i, d in enumerate(shuffled_doctors):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.9);
                    border-radius: 15px;
                    border: 1px solid rgba(0,0,0,0.1);
                }
                QFrame:hover {
                    background: rgba(255,255,255,1);
                    border: 2px solid #55c79a;
                }
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 50))
            shadow.setOffset(2, 2)
            card.setGraphicsEffect(shadow)
            h = QVBoxLayout()
            h.setContentsMargins(20, 20, 20, 20)
            h.setSpacing(10)
            name = QLabel(f"👨‍⚕️ {d['name']}"); name.setStyleSheet('font-size:18px; font-weight:bold; color:#004c3f; background: transparent;')
            rating = QLabel(f"⭐ {d['rating']} ★"); rating.setStyleSheet('font-size:16px; color:#c79f10; font-weight:bold; background: transparent;')
            years = QLabel(f"Experience: {d['years']} years"); years.setStyleSheet('color:#666; font-size:14px; background: transparent;')
            specialty = QLabel(f"Specialty: {d['specialty']}"); specialty.setStyleSheet('color:#666; font-size:14px; background: transparent;')
            book = QPushButton('Book Appointment')
            book.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                    color: white;
                    border-radius: 12px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
                QPushButton:pressed { background: #2e7d32; }
            """)
            book.clicked.connect(self.goto_book_cb)
            h.addWidget(name)
            h.addWidget(rating)
            h.addWidget(years)
            h.addWidget(specialty)
            h.addWidget(book, alignment=Qt.AlignCenter)
            card.setLayout(h)
            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)
        layout.addLayout(grid)
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)
        layout.addStretch(); layout.addWidget(back, alignment=Qt.AlignRight)
        self.setLayout(layout)

class PersonalInfoForm(QWidget):
    def __init__(self, goto_schedule_cb, back_cb):
        super().__init__()
        self.goto_schedule_cb = goto_schedule_cb
        self.back_cb = back_cb
        self._build()
    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel('Book Appointment — Personal Information')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        form = QGridLayout()
        form.setSpacing(15)
        self.name = QLineEdit(); self.name.setPlaceholderText('Full name')
        self.name.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.age = QLineEdit(); self.age.setPlaceholderText('Age')
        self.age.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.contact = QLineEdit(); self.contact.setPlaceholderText('Contact number')
        self.contact.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.gender = QComboBox(); self.gender.addItems(['Prefer not to say','Male','Female','Other'])
        self.gender.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox:focus { border: 2px solid #55c79a; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: url(down_arrow.png); }
        """)
        self.address = QLineEdit(); self.address.setPlaceholderText('Address')
        self.address.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #55c79a; }
        """)
        self.concern = QTextEdit(); self.concern.setPlaceholderText('Reason to visit / concern')
        self.concern.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
            }
            QTextEdit:focus { border: 2px solid #55c79a; }
        """)
        form.addWidget(QLabel('Name'),0,0); form.addWidget(self.name,0,1)
        form.addWidget(QLabel('Age'),0,2); form.addWidget(self.age,0,3)
        form.addWidget(QLabel('Contact'),1,0); form.addWidget(self.contact,1,1)
        form.addWidget(QLabel('Gender'),1,2); form.addWidget(self.gender,1,3)
        form.addWidget(QLabel('Address'),2,0); form.addWidget(self.address,2,1,1,3)
        form.addWidget(QLabel('Concern'),3,0); form.addWidget(self.concern,3,1,1,3)
        next_btn = QPushButton('Next')
        next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        next_btn.clicked.connect(self.on_next)
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)
        layout.addWidget(title); layout.addLayout(form); layout.addStretch(); layout.addWidget(back, alignment=Qt.AlignLeft); layout.addWidget(next_btn, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def on_next(self):
        if not self.name.text().strip() or not self.age.text().strip() or not self.contact.text().strip() or not self.address.text().strip() or not self.concern.toPlainText().strip():
            QMessageBox.warning(self, "Input Error", "Please fill in all personal information fields.")
        else:
            self.goto_schedule_cb()

class ScheduleSelection(QWidget):
    def __init__(self, personal_form, back_cb, next_cb):
        super().__init__()
        self.personal_form = personal_form
        self.back_cb = back_cb
        self.next_cb = next_cb
        self._build()
    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        title = QLabel('Select Schedule')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: black; background: transparent;")
        layout.addWidget(title)
        subtitle = QLabel('Choose your preferred date and time for the appointment.')
        subtitle.setStyleSheet('color: black; font-size:14px; background: transparent; margin-bottom:10px')
        layout.addWidget(subtitle)

        # Card container
        schedule_card = QFrame()
        schedule_card.setStyleSheet("background-color: white; border-radius: 20px;")

        s_layout = QVBoxLayout(schedule_card)
        s_layout.setContentsMargins(25, 25, 25, 25)
        s_layout.setSpacing(15)

        self.cal = QCalendarWidget(); self.cal.setGridVisible(True); self.cal.setMinimumDate(QDate.currentDate()); self.cal.setNavigationBarVisible(True); self.cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.cal.setStyleSheet("""
            QCalendarWidget { background: white; border-radius: 10px; border: 1px solid rgba(0,0,0,0.1); }
        """)
        s_layout.addWidget(self.cal)
        time_label = QLabel('Available Time Slots:')
        time_label.setStyleSheet('font-weight:bold; color: black; background: transparent; margin-top:10px')
        s_layout.addWidget(time_label)

        self.all_times = ['9:00 AM','10:00 AM','11:00 AM','12:00 PM','1:00 PM','2:00 PM','3:00 PM','4:00 PM','5:00 PM','6:00 PM']
        self.time_buttons = QGridLayout()
        selected_times = random.sample(self.all_times, 6)
        for i, t in enumerate(selected_times):
            btn = QPushButton(t)
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 1px solid black;
                    padding: 8px 12px;
                    border-radius: 8px;
                    color: black;
                    font-weight: bold;
                }
                QPushButton:hover { background: #f0f0f0; }
                QPushButton:checked { background: #e0e0e0; color: black; }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, x=t: self.select_time(x))
            self.time_buttons.addWidget(btn, i//3, i%3)
        s_layout.addLayout(self.time_buttons)

        self.selected_time_label = QLabel('Selected Time: None')
        self.selected_time_label.setStyleSheet('color: black; font-weight:bold; background: transparent; margin-top:10px')
        s_layout.addWidget(self.selected_time_label)

        layout.addWidget(schedule_card)
        submit = QPushButton('Next')
        submit.setStyleSheet("""
            QPushButton {
                background: white;
                color: black;
                border-radius: 14px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid black;
            }
            QPushButton:hover { background: #f0f0f0; }
        """)
        submit.clicked.connect(self.on_next)
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid black;
                padding: 10px 16px;
                border-radius: 10px;
                color: black;
                font-weight: bold;
            }
            QPushButton:hover { background: #f0f0f0; }
        """)
        back.clicked.connect(self.back_cb)
        layout.addWidget(back, alignment=Qt.AlignLeft)
        layout.addWidget(submit, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    def select_time(self, t):
        self.selected_time = t
        self.selected_time_label.setText(f'Selected Time: {t}')
        # Uncheck other buttons
        for i in range(self.time_buttons.count()):
            btn = self.time_buttons.itemAt(i).widget()
            if btn.text() != t:
                btn.setChecked(False)
            else:
                btn.setChecked(True)
    def on_next(self):
        info = {
            'name': self.personal_form.name.text(),
            'age': self.personal_form.age.text(),
            'contact': self.personal_form.contact.text(),
            'gender': self.personal_form.gender.currentText(),
            'address': self.personal_form.address.text(),
            'concern': self.personal_form.concern.toPlainText(),
            'doctor_id': 1,
            'hospital_id': 1,
            'schedule': self.cal.selectedDate().toString("yyyy-MM-dd"),
            'time_slot': self.selected_time or '9AM'
        }
        self.next_cb(info)


class ConsultationTypeSelection(QWidget):
    def __init__(self, appointment_info, back_cb, next_cb):
        super().__init__()
        self.appointment_info = appointment_info
        self.back_cb = back_cb
        self.next_cb = next_cb
        self.selected_type = None
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel('Select Consultation Type')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel('Choose your preferred consultation method.')
        subtitle.setStyleSheet('color:#666; font-size:14px; background: transparent; margin-bottom:10px')
        layout.addWidget(subtitle)

        # Online option
        online_frame = QFrame()
        online_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 2px solid rgba(0,0,0,0.1);
            }
        """)
        online_layout = QVBoxLayout(online_frame)
        online_layout.setContentsMargins(20, 20, 20, 20)

        online_title = QLabel('💻 Online Consultation')
        online_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        online_title.setStyleSheet("color: #1f2d3d;")
        online_layout.addWidget(online_title)

        online_desc = QLabel('Convenient video call from anywhere.\nSecure and private session.')
        online_desc.setStyleSheet("color: #666; font-size: 14px;")
        online_layout.addWidget(online_desc)

        online_price = QLabel('$100')
        online_price.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        online_price.setStyleSheet("color: #55c79a;")
        online_layout.addWidget(online_price, alignment=Qt.AlignRight)

        online_btn = QPushButton('Select Online')
        online_btn.setCheckable(True)
        online_btn.setStyleSheet("""
            QPushButton {
                background: rgba(85, 199, 154, 0.1);
                border: 2px solid #55c79a;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: #55c79a;
            }
            QPushButton:hover { background: rgba(85, 199, 154, 0.2); }
            QPushButton:checked {
                background: #55c79a;
                color: white;
            }
        """)
        online_btn.clicked.connect(lambda: self.select_type('online', 100, online_btn, face_btn))
        online_layout.addWidget(online_btn)

        layout.addWidget(online_frame)

        # Face-to-face option
        face_frame = QFrame()
        face_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 2px solid rgba(0,0,0,0.1);
            }
        """)
        face_layout = QVBoxLayout(face_frame)
        face_layout.setContentsMargins(20, 20, 20, 20)

        face_title = QLabel('🏥 Face-to-Face Consultation')
        face_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        face_title.setStyleSheet("color: #1f2d3d;")
        face_layout.addWidget(face_title)

        face_desc = QLabel('In-person visit at the clinic.\nDirect interaction with doctor.')
        face_desc.setStyleSheet("color: #666; font-size: 14px;")
        face_layout.addWidget(face_desc)

        face_price = QLabel('$150')
        face_price.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        face_price.setStyleSheet("color: #55c79a;")
        face_layout.addWidget(face_price, alignment=Qt.AlignRight)

        face_btn = QPushButton('Select Face-to-Face')
        face_btn.setCheckable(True)
        face_btn.setStyleSheet("""
            QPushButton {
                background: rgba(85, 199, 154, 0.1);
                border: 2px solid #55c79a;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: #55c79a;
            }
            QPushButton:hover { background: rgba(85, 199, 154, 0.2); }
            QPushButton:checked {
                background: #55c79a;
                color: white;
            }
        """)
        face_btn.clicked.connect(lambda: self.select_type('face-to-face', 150, face_btn, online_btn))
        face_layout.addWidget(face_btn)

        layout.addWidget(face_frame)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)
        nav_layout.addWidget(back, alignment=Qt.AlignLeft)

        self.next_btn = QPushButton('Next')
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                color: white;
                border-radius: 14px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
            QPushButton:disabled {
                background: #ccc;
                color: #666;
            }
        """)
        self.next_btn.clicked.connect(self.on_next)
        nav_layout.addWidget(self.next_btn, alignment=Qt.AlignCenter)

        layout.addLayout(nav_layout)
        self.setLayout(layout)

    def select_type(self, type_name, price, selected_btn, other_btn):
        self.selected_type = type_name
        self.selected_price = price
        selected_btn.setChecked(True)
        other_btn.setChecked(False)
        self.next_btn.setEnabled(True)

    def on_next(self):
        self.appointment_info['consultation_type'] = self.selected_type
        self.appointment_info['price'] = self.selected_price
        self.next_cb(self.appointment_info)


class ConfirmationScreen(QWidget):
    def __init__(self, appointment_info, back_cb, accept_cb):
        super().__init__()
        self.appointment_info = appointment_info
        self.back_cb = back_cb
        self.accept_cb = accept_cb
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel('Confirm Appointment')
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2d3d; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel('Please review your appointment details.')
        subtitle.setStyleSheet('color:#666; font-size:14px; background: transparent; margin-bottom:10px')
        layout.addWidget(subtitle)

        # Details frame
        details_frame = QFrame()
        details_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border: 2px solid rgba(0,0,0,0.1);
            }
        """)
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(20, 20, 20, 20)

        details = [
            f"Name: {self.appointment_info['name']}",
            f"Age: {self.appointment_info['age']}",
            f"Contact: {self.appointment_info['contact']}",
            f"Gender: {self.appointment_info['gender']}",
            f"Address: {self.appointment_info['address']}",
            f"Concern: {self.appointment_info['concern']}",
            f"Date: {self.appointment_info['schedule']}",
            f"Time: {self.appointment_info['time_slot']}",
            f"Type: {self.appointment_info['consultation_type'].title()}",
            f"Price: ${self.appointment_info['price']}"
        ]

        for detail in details:
            label = QLabel(detail)
            label.setStyleSheet("color: #1f2d3d; font-size: 14px; margin: 5px 0;")
            details_layout.addWidget(label)

        layout.addWidget(details_frame)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        back = QPushButton('Back')
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 16px;
                border-radius: 10px;
                color: #234;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff; }
        """)
        back.clicked.connect(self.back_cb)
        nav_layout.addWidget(back, alignment=Qt.AlignLeft)

        accept = QPushButton('Accept & Book')
        accept.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55c79a, stop:1 #4caf50);
                color: white;
                border-radius: 14px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4caf50, stop:1 #388e3c); }
        """)
        accept.clicked.connect(self.on_accept)
        nav_layout.addWidget(accept, alignment=Qt.AlignCenter)

        layout.addLayout(nav_layout)
        self.setLayout(layout)

    def on_accept(self):
        save_appointment(self.appointment_info)
        self.accept_cb()


# ==========================================
#  MAIN WINDOW (CONTAINER)
# ==========================================
class HilomMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM - Holistic Wellness")
        # self.setFixedSize(1100, 720)  # Removed to allow full screen

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.background_label = QLabel(central_widget)
        self.background_label.setPixmap(QPixmap("cherry-blossom.jpg"))
        self.background_label.setScaledContents(True)
        self.background_label.lower()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8f7f9, stop:1 #d0eff7);
                border-right: 1px solid rgba(0,0,0,0.05);
            }
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(15, 30, 15, 30)
        sb_layout.setSpacing(10)

        # Logo
        logo = QLabel("HILOM")
        logo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        logo.setStyleSheet("color: #2e7d32; background: transparent;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(logo)
        sb_layout.addSpacing(20)

        # Navigation Buttons
        self.btn_group = []
        menu_items = ["Home", "Journal", "Recommend", "Appointment", "Favorite", "History", "Profile"]

        for index, text in enumerate(menu_items):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            # Store index to use in click event
            btn.clicked.connect(lambda checked, idx=index: self.switch_page(idx))

            # Base style
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #234;
                    text-align: left;
                    padding-left: 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(60, 120, 180, 0.1);
                    font-weight: bold;
                }
            """)
            self.btn_group.append(btn)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # User Profile (Bottom of Sidebar)
        profile_frame = QFrame()
        pf_layout = QHBoxLayout(profile_frame)
        pf_layout.setContentsMargins(0, 0, 0, 0)

        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("background: #fff; border-radius: 16px; border: 1px solid #ccc;")

        user_lbl = QLabel("User")
        user_lbl.setStyleSheet("color: #234; font-size: 13px; font-weight: bold; background: transparent;")

        pf_layout.addWidget(avatar)
        pf_layout.addWidget(user_lbl)
        sb_layout.addWidget(profile_frame)

        # Add Sidebar to Main Layout
        main_layout.addWidget(sidebar)

        # --- Content Area (Stacked Widget) ---
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        # Initialize Pages
        self.home_page = DashboardPage()
        self.journal_page = JournalPage()
        self.recommend_page = RecommendationApp()
        self.favorite_page = FavoritePage()

        # History Page
        self.history_page = HistoryPage()

        # Profile Page
        self.profile_page = ProfilePage()

        # Appointment Pages
        self.appointment_stack = QStackedWidget()
        self.appointment_location = LocationEntry(lambda: self.appointment_stack.setCurrentIndex(1))
        self.appointment_hospitals = HospitalList(lambda h: self.show_appointment_detail(h), lambda: self.appointment_stack.setCurrentIndex(0))
        self.appointment_detail = HospitalDetail(HOSPITALS[0], lambda: self.appointment_stack.setCurrentIndex(3), lambda: self.appointment_stack.setCurrentIndex(1))
        self.appointment_doctors = DoctorSelection(lambda: self.appointment_stack.setCurrentIndex(4), lambda: self.appointment_stack.setCurrentIndex(2))
        self.appointment_personal = PersonalInfoForm(lambda: self.appointment_stack.setCurrentIndex(5), lambda: self.appointment_stack.setCurrentIndex(3))
        self.appointment_schedule = ScheduleSelection(self.appointment_personal, lambda: self.appointment_stack.setCurrentIndex(4), self.show_consultation_type)
        self.appointment_consultation = None  # Will be created dynamically
        self.appointment_confirmation = None  # Will be created dynamically
        self.appointment_stack.addWidget(self.appointment_location)
        self.appointment_stack.addWidget(self.appointment_hospitals)
        self.appointment_stack.addWidget(self.appointment_detail)
        self.appointment_stack.addWidget(self.appointment_doctors)
        self.appointment_stack.addWidget(self.appointment_personal)
        self.appointment_stack.addWidget(self.appointment_schedule)

        # Add Pages to Stack
        self.stack.addWidget(self.home_page)  # Index 0
        self.stack.addWidget(self.journal_page)  # Index 1
        self.stack.addWidget(self.recommend_page)  # Index 2
        self.stack.addWidget(self.appointment_stack)  # Index 3
        self.stack.addWidget(self.favorite_page)  # Index 4
        self.stack.addWidget(self.history_page)  # Index 5
        self.stack.addWidget(self.profile_page)  # Index 6

        main_layout.addWidget(self.stack)

        # Set initial page style
        self.highlight_sidebar(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.highlight_sidebar(index)

    def highlight_sidebar(self, active_index):
        # Reset all buttons
        for i, btn in enumerate(self.btn_group):
            if i == active_index:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #b0e0e6;
                        color: #004d40;
                        text-align: left;
                        padding-left: 15px;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #234;
                        text-align: left;
                        padding-left: 15px;
                        border-radius: 8px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background: rgba(60, 120, 180, 0.1);
                    }
                """)


    def show_appointment_detail(self, hospital):
        idx = 2
        old = self.appointment_stack.widget(idx)
        self.appointment_stack.removeWidget(old)
        old.deleteLater()
        self.appointment_detail = HospitalDetail(hospital, lambda: self.appointment_stack.setCurrentIndex(3), lambda: self.appointment_stack.setCurrentIndex(1))
        self.appointment_stack.insertWidget(idx, self.appointment_detail)
        self.appointment_stack.setCurrentIndex(idx)

    def show_consultation_type(self, appointment_info):
        if self.appointment_consultation:
            self.appointment_consultation.deleteLater()
        self.appointment_consultation = ConsultationTypeSelection(appointment_info, lambda: self.appointment_stack.setCurrentIndex(5), self.show_confirmation)
        self.appointment_stack.addWidget(self.appointment_consultation)
        self.appointment_stack.setCurrentIndex(6)

    def show_confirmation(self, appointment_info):
        if self.appointment_confirmation:
            self.appointment_confirmation.deleteLater()
        self.appointment_confirmation = ConfirmationScreen(appointment_info, lambda: self.appointment_stack.setCurrentIndex(6), lambda: self.stack.setCurrentIndex(0))
        self.appointment_stack.addWidget(self.appointment_confirmation)
        self.appointment_stack.setCurrentIndex(7)


# ---------- Mood Content (songs + videos + books) ----------
mood_content = {
    "HAPPY": {
        "songs": [
            "Bruno Mars – 24K Magic", "Bruno Mars – Treasure", "Katy Perry – Last Friday Night (T.G.I.F.)",
            "Katy Perry – California Gurls", "Taylor Swift – 22", "Taylor Swift – Shake It Off",
            "Ariana Grande – Break Free", "Ariana Grande – Into You", "Justin Timberlake – Can’t Stop The Feeling!",
            "Walk The Moon – Shut Up and Dance", "BLACKPINK – JUMP", "BLACKPINK – Boombayah",
            "TWICE – Likey", "TWICE – Cheer Up", "TWICE – What Is Love?", "BTS – Dynamite",
            "BTS – Permission to Dance", "SEVENTEEN – Very Nice (아주 NICE)", "Red Velvet – Red Flavor",
            "NewJeans – Super Shy", "Dua Lipa – Don’t Start Now", "Carly Rae Jepsen – Call Me Maybe",
            "Justin Bieber, Nicki Minaj – Beauty and A Beat", "Meghan Trainor – Me Too", "Icona Pop – I Love It",
            "BINI – Pantropiko", "BINI – Salamin, Salamin", "SB19 – Gento", "Maymay Entrata – Amakabogera",
            "Vice Ganda – Karakaraka"
        ],
        "videos": [
            {"title": "The Simple Secret of Being Happier | Tia Graham | TEDxManitouSprings", "youtube": "https://www.youtube.com/watch?v=gYeHV_nA36c", "spotify": ""},
            {"title": "How To Be Happy & Remove Negative Thoughts in ANY Situation | Tony Robbins", "youtube": "https://youtu.be/r4ZdyS6v3qA?si=h-kcEKnlaHajWcQC", "spotify": ""},
            {"title": "You can be happy without changing your life | Cassie Holmes | TEDxManhattanBeach", "youtube": "https://youtu.be/VOC44gKRTI4?si=_v4Fk17JazdrkM9R", "spotify": ""},
            {"title": "How to Be Happy Every Day: It Will Change the World | Jacqueline Way | TEDxStanleyPark", "youtube": "https://youtu.be/78nsxRxbf4w?si=aunmqh6uvv_XKy-5", "spotify": ""},
            {"title": "You Don't Find Happiness, You Create It | Katarina Blom | TEDxGöteborg", "youtube": "https://youtu.be/9DtcSCFwDdw?si=QrpA2gLoyq43SIvp", "spotify": ""},
            {"title": "How To be Happy", "youtube": "", "spotify": "https://open.spotify.com/episode/1buRk9XQH7c6zfYhQuPOQo?si=f48247f0b23248f9"},
            {"title": "How to Push Yourself to be happy even when life is hard", "youtube": "", "spotify": "https://open.spotify.com/episode/6qFAIe1McmITlhFPPklw8i?si=NhlFbZDgQbONzvPabp7oCw"},
            {"title": "A happy & healthy life", "youtube": "", "spotify": "https://open.spotify.com/episode/4uTLnCklbPIA2RDozUfTbT?si=h2zLVG9oRH2CbQRAvbVxyg"}
        ],
        "books": [
            {"title": "The Art of Happiness by the Dalai Lama & Howard Cutler", "description": "A classic blending Buddhist wisdom and psychological insight, arguing that happiness comes more from the state of our minds than external conditions.", "link": "https://www.amazon.com/Art-Happiness-Handbook-Living/dp/1573221112"},
            {"title": "The Happiness Hypothesis by Jonathan Haidt", "description": "Explores ancient philosophical ideas about happiness and compares them with modern psychology research; good for understanding what really makes people fulfilled.", "link": "https://www.amazon.com/Happiness-Hypothesis-Finding-Modern-Ancient/dp/0465028020"},
            {"title": "Authentic Happiness by Martin E. P. Seligman", "description": "A foundational book in positive psychology, showing how happiness can be cultivated by discovering and using your personal strengths, finding meaning, and building well-being.", "link": "https://www.amazon.com/Authentic-Happiness-Using-Positive-Psychology/dp/0743222989"},
            {"title": "The Power of Positive Thinking by Norman Vincent Peale", "description": "A self-help classic that emphasizes optimism, affirmations, and mindset as tools for improving daily life and emotional well-being.", "link": "https://www.amazon.com/Power-Positive-Thinking/dp/0743234804"},
            {"title": "Happiness Becomes You by Tina Turner", "description": "A more personal and spiritual take: the author shares her life journey and insights on how to find inner peace and happiness despite hardships.", "link": "https://www.amazon.com/Happiness-Becomes-You-Tina-Turner/dp/0062686726"}
        ]
    },
    "SAD": {
        "songs": [
            "Angela Ken – Ako Naman Muna", "Angela Ken – It’s Okay Not Be Okay", "Coldplay – Fix You",
            "Coldplay – The Scientist", "Coldplay – Sparks", "Coldplay – Yellow", "Coldplay – Everglow",
            "Eraserheads – With a Smile", "Eraserheads – Alapaap", "Eraserheads – Huwag Kang Matakot",
            "Adie – You’ll be safe here", "NIKI – You’ll be in My Heart", "TONEEJAY – 711", "Ben&Ben – Leaves",
            "Jan Roberts – Sagip", "Emman – Teka Lang", "Orange & Lemons – Heaven Knows", "Dilaw – Janice",
            "Munimuni – Minsan", "beabadoobee – Glue Song", "Amiel Sol – Sa Bawat Sandali",
            "Wave to Earth – Seasons", "Wave to Earth – Bad", "Rex Orange County – Happiness", "Yung Kai – blue",
            "Hale – Blue Sky", "Billie Eilish – Birds Of A Feather", "Ed Sheeran – Supermarket Flowers",
            "Taylor Swift – My tears ricochet", "Taylor Swift – This is me trying"
        ],
        "videos": [
            {"title": "\"I'm Fine\" - Learning To Live With Depression | Jake Tyler | TEDxBrighton", "youtube": "https://youtu.be/IDPDEKtd2yM?si=H-jNV1lu0ZeyuPaX", "spotify": ""},
            {"title": "How to talk to the worst parts of yourself | Karen Faith | TEDxKC", "youtube": "https://youtu.be/gUV5DJb6KGs?si=nrhWRfM47i7NN9p2", "spotify": ""},
            {"title": "Getting stuck in the negatives (and how to get unstuck) | Alison Ledgerwood | TEDxUCDavis", "youtube": "https://youtu.be/7XFLTDQ4JMk?si=4e8xVvIjZowTymXe", "spotify": ""},
            {"title": "Listen To This When You Are Feeling Down | Buddhism In English", "youtube": "https://youtu.be/BloutcYWbJg?si=83T_Vl_98cxTJbOU", "spotify": ""},
            {"title": "How to Deal with Negative Emotions - Distress Tolerance", "youtube": "https://youtu.be/puoddnGTAJk?si=IZ7q4eiwm_meUziU", "spotify": ""},
            {"title": "mga habits that make you sad", "youtube": "", "spotify": "https://open.spotify.com/episode/2CVCpJI0AN7pMFlsJZXrhV?si=8N74pp3GRlaLsLNm61xZ7A"},
            {"title": "Lungkot? Lungkot.", "youtube": "", "spotify": "https://open.spotify.com/episode/0zTnUc1tLgi3yN4dhKROKL?si=zZMqBCVMSYagtSXjnrWoMg"},
            {"title": "I found comfort in sadness", "youtube": "", "spotify": "https://open.spotify.com/episode/12k9esN1hOFn5A3zBNQplL?si=oBdwTpfxTFmucKMkvWmVWA"},
            {"title": "It’s okay to not be okay", "youtube": "", "spotify": "https://open.spotify.com/show/0ueXNkUlQsDxSRNTLZHnLZ?si=9628a29af7e342b0"}
        ],
        "books": [
            {"title": "The Comfort Book — Matt Haig", "description": "Gentle reminders, short reflections, and soft motivation when you're overwhelmed.", "link": "https://www.amazon.com/Comfort-Book-Matt-Haig/dp/052556630X"},
            {"title": "The Mountain Is You — Brianna Wiest", "description": "About healing, emotional growth, and turning pain into strength.", "link": "https://www.amazon.com/Mountain-You-Overcoming-Internal-Resistance/dp/1949759339"},
            {"title": "The Happiness Trap — Dr. Russ Harris", "description": "Teaches you healthy ways to handle sadness and negative thoughts through acceptance.", "link": "https://www.amazon.com/Happiness-Trap-Stop-Struggling-Live/dp/1590305841"},
            {"title": "Reasons to Stay Alive — Matt Haig", "description": "A hopeful, real story about surviving depression and finding light again.", "link": "https://www.amazon.com/Reasons-Stay-Alive-Matt-Haig/dp/052556396X"},
            {"title": "The Courage to Be Disliked — Ichiro Kishimi & Fumitake Koga", "description": "Motivational lessons on freeing yourself from past pain, expectations, and self-doubt.", "link": "https://www.amazon.com/Courage-Be-Disliked-Phenomenon-Psychology/dp/1501197274"}
        ]
    },
    "ANGER": {
        "songs": [
            "Dua Lipa – IDGAF", "Olivia Rodrigo – good 4 u", "Dua Lipa – Don’t Start Now", "Taylor Swift – Bad Blood",
            "Taylor Swift – Sorry Not Sorry", "Madison Beer – Reckless", "Olivia Rodrigo – happier",
            "Taylor Swift – Look What You Made Me Do", "Olivia Rodrigo – vampire", "Olivia Rodrigo – traitor",
            "Taylor Swift – Better Than Revenge", "Taylor Swift – Don’t Blame Me", "Conan Gray – Maniac",
            "Billie Eilish – Happier Than Ever", "Katy Perry – Dark Horse", "Olivia Rodrigo – get him back",
            "Leyla Blue – What A Shame", "Olivia Rodrigo – Jealousy Jealousy", "Olivia Rodrigo – brutal",
            "Billie Eilish – Therefore I Am", "SZA – Kill Bill", "Maroon 5 – Animals", "Rihanna – Breakin’ Dishes",
            "SZA – I Hate U", "Conan Gray – Wish You Were Sober", "Taylor Swift – Karma", "Olivia Rodrigo – love is embarrassing",
            "Olivia Rodrigo – all-american bitch", "Gracie Abrams – That’s So True", "Imagine Dragons – Enemy"
        ],
        "videos": [
            {"title": "5 Ways to Diffuse Your anger", "youtube": "https://youtu.be/H4WYp9a6Yzg?si=Qb5nvlXVbCPRouBt", "spotify": ""},
            {"title": "A simple Practice to deal with Anger | Buddhism In English", "youtube": "https://youtu.be/tV2Ecd7m6Tc?si=v9MTAxrgT9x_93Fn", "spotify": ""},
            {"title": "How to let go of the anger in your heart | Buddhism In English", "youtube": "https://youtu.be/gKiv2ot3-Eg?si=frEk5Sun7wSD1gjd", "spotify": ""},
            {"title": "Dr. Gabor Maté — How to Process Your Anger and Rage", "youtube": "https://youtu.be/Yh1-y3TzSO4?si=vHo2h6v8fYRgg0", "spotify": ""},
            {"title": "The Antidote to Anger | Mike Goldman | TEDxGainesville", "youtube": "https://youtu.be/hCIfi-xvjgE?si=CFStT6KaSPVw2WgV", "spotify": ""},
            {"title": "How to use anger as a force for good | Marcia Reynolds | TEDxAtlanta", "youtube": "https://youtu.be/owZb9qub-RU?si=5T_SA4gIVqI3nESG", "spotify": ""},
            {"title": "Anger Is Your Ally: A Mindful Approach to Anger | Juna Mustad | TEDxWabashCollege", "youtube": "https://youtu.be/sbVBsrNnBy8?si=AELBtrmDo8jTT4td", "spotify": ""},
            {"title": "How to Let Go of Anger and Resentment", "youtube": "", "spotify": "https://open.spotify.com/episode/2Qy7OewGPMHLoXmaICHnR5?si=bbb6a13321e543d6"},
            {"title": "How to Get your Anger under control", "youtube": "", "spotify": "https://open.spotify.com/episode/1TgivM1vPsyJp92B5hvqqX?si=3ebef14332da49cf"},
            {"title": "Anger Management techniques", "youtube": "", "spotify": "https://open.spotify.com/episode/3hJ4WwWXcA3DH4luFnjlll?si=4d69f2c144884ae7"}
        ],
        "books": [
            {"title": "The Dance of Anger — Harriet Lerner", "description": "Explains that anger is a signal, not a problem. Helps you recognize patterns, express feelings assertively, and set healthy boundaries.", "link": "https://www.amazon.com/Dance-Anger-Women-Change-Relationship/dp/0062319690"},
            {"title": "Anger Management for Everyone — Raymond Chip Tafrate", "description": "Uses psychology-based techniques to help you understand the root causes of anger. Offers exercises to respond thoughtfully rather than react impulsively.", "link": "https://www.amazon.com/Anger-Management-Everyone-Practical-Techniques/dp/1626257117"},
            {"title": "The Cow in the Parking Lot — Susan Edmiston & Leonard Scheff", "description": "A humorous, easy-to-read guide for staying patient in frustrating situations. Teaches simple daily strategies to keep calm in small and big conflicts.", "link": "https://www.amazon.com/Cow-Parking-Lot-Simple-Strategies/dp/1569754923"},
            {"title": "Emotional Intelligence 2.0 — Travis Bradberry & Jean Greaves", "description": "Teaches self-awareness, empathy, and emotional regulation. Includes strategies to manage anger and other strong emotions in real-time.", "link": "https://www.amazon.com/Emotional-Intelligence-2-0-Travis-Bradberry/dp/0974320625"},
            {"title": "Mind Over Mood — Dennis Greenberger & Christine A. Padesky", "description": "Practical exercises to manage anger, mood, and emotional responses.", "link": "https://www.amazon.com/Mind-Over-Mood-Change-Depression/dp/1626251259"}
        ]
    },
    "FEAR": {
        "songs": [
            "Billie Eilish – bury a friend", "Imagine Dragons – Demons", "Linkin Park – In the End",
            "Coldplay – Trouble", "Radiohead – Creep", "The Weeknd – Save Your Tears", "Kodaline – All I Want",
            "Twenty One Pilots – Stressed Out", "Sia – Breathe Me", "Adele – Hello"
        ],
        "videos": [
            {"title": "How Fear Works | Tony Robbins", "youtube": "https://youtu.be/Z0_Jx3_QPUE", "spotify": ""},
            {"title": "Facing Your Fears | Jocko Willink | TEDx", "youtube": "https://youtu.be/9NhTshcUZcM", "spotify": ""},
            {"title": "Overcoming Fear | Jordan Peterson", "youtube": "https://youtu.be/3GRS0nDq8vM", "spotify": ""}
        ],
        "books": [
            {"title": "Feel the Fear and Do It Anyway – Susan Jeffers", "description": "A classic guide on confronting fear and moving past it into action.", "link": "https://www.amazon.com/Feel-Fear-Do-Anyway/dp/0345487427"},
            {"title": "Daring Greatly – Brené Brown", "description": "Encourages vulnerability and courage to overcome fear in personal and professional life.", "link": "https://www.amazon.com/Daring-Greatly-Courage-Vulnerable-Transforms/dp/1592408419"},
            {"title": "The Gift of Fear – Gavin de Becker", "description": "A practical book on understanding fear as a protective tool.", "link": "https://www.amazon.com/Gift-Fear-Survival-Signals-Violence/dp/0440226198"}
        ]
    },
    "STRESS": {
        "songs": [
            "Calm – Weightless", "Coldplay – Fix You", "Norah Jones – Don’t Know Why", "Ed Sheeran – Photograph",
            "Enya – Only Time", "Sade – By Your Side"
        ],
        "videos": [
            {"title": "Stress Management Techniques", "youtube": "https://youtu.be/hnpQrMqDoqE", "spotify": ""},
            {"title": "Guided Meditation for Stress", "youtube": "https://youtu.be/MIr3RsUWrdo", "spotify": ""}
        ],
        "books": [
            {"title": "Why Zebras Don’t Get Ulcers – Robert M. Sapolsky", "description": "Explains stress physiology and practical coping mechanisms.", "link": "https://www.amazon.com/Why-Zebras-Dont-Get-Ulcers/dp/0805073698"},
            {"title": "The Relaxation and Stress Reduction Workbook – Martha Davis", "description": "Provides exercises and techniques to manage stress effectively.", "link": "https://www.amazon.com/Relaxation-Stress-Reduction-Workbook/dp/0898623920"}
        ]
    },
    "LOVE": {
        "songs": [
            "Ed Sheeran – Perfect", "Adele – Make You Feel My Love", "Beyoncé – Halo",
            "John Legend – All of Me", "Taylor Swift – Lover", "Maroon 5 – Sugar"
        ],
        "videos": [
            {"title": "The Science of Love | TED-Ed", "youtube": "https://youtu.be/0kOPrP7zE0", "spotify": ""}
        ],
        "books": [
            {"title": "The 5 Love Languages – Gary Chapman", "description": "Explains how different people express and feel love differently.", "link": "https://www.amazon.com/Love-Languages-Secret-Lasting-Relationships/dp/080241270X"},
            {"title": "Attached – Amir Levine", "description": "Explores attachment styles in relationships.", "link": "https://www.amazon.com/Attached-Science-Adult-Attachment-Relationships/dp/1585428485"}
        ]
    },
    "CALM": {
        "songs": [
            "Enya – Only Time", "Ludovico Einaudi – Nuvole Bianche", "Yiruma – River Flows in You",
            "Norah Jones – Come Away with Me", "Coldplay – Paradise"
        ],
        "videos": [
            {"title": "Guided Relaxation for Calm", "youtube": "https://youtu.be/mG2P7sw6YwA", "spotify": ""}
        ],
        "books": [
            {"title": "The Book of Calm – Paul Wilson", "description": "Practical advice and reflections for inner calm.", "link": "https://www.amazon.com/Book-Calm-Paul-Wilson/dp/1842226996"},
            {"title": "Calm – Michael Acton Smith", "description": "Insights into meditation and relaxation techniques.", "link": "https://www.amazon.com/Calm-Michael-Acton-Smith/dp/1444715233"}
        ]
    },
    "HOPE": {
        "songs": [
            "Katy Perry – Firework", "Rachel Platten – Fight Song", "Andra Day – Rise Up",
            "Coldplay – A Sky Full of Stars", "U2 – Beautiful Day"
        ],
        "videos": [
            {"title": "Finding Hope in Difficult Times", "youtube": "https://youtu.be/5Cp2p3rsmGk", "spotify": ""}
        ],
        "books": [
            {"title": "Man’s Search for Meaning – Viktor E. Frankl", "description": "Finding purpose and hope even in dire circumstances.", "link": "https://www.amazon.com/Mans-Search-Meaning-Viktor-Frankl/dp/080701429X"},
            {"title": "Option B – Sheryl Sandberg", "description": "How to build resilience and hope after adversity.", "link": "https://www.amazon.com/Option-B-Facing-Adversity-Building/dp/1524732680"}
        ]
    }
}


# ---------- helper functions ----------
def youtube_search_url(query_text: str) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(query_text)

def spotify_search_url(query_text: str) -> str:
    return "https://open.spotify.com/search/" + quote_plus(query_text)

def spotify_uri_search(query_text: str) -> str:
    return "spotify:search:" + query_text

# ---------- Embedded Player Widget ----------
class EmbeddedPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.toolbar = QToolBar()
        self.btn_youtube = QAction("YouTube", self)
        self.btn_spotify_web = QAction("Spotify (Web)", self)
        self.btn_spotify_app = QAction("Open in Spotify App", self)
        self.toolbar.addAction(self.btn_youtube)
        self.toolbar.addAction(self.btn_spotify_web)
        self.toolbar.addAction(self.btn_spotify_app)
        layout.addWidget(self.toolbar)

        self.web = QWebEngineView()
        layout.addWidget(self.web, 1)

        self.current_title = None

    def load_youtube_search_and_autoplay(self, query: str):
        self.current_title = query
        search = youtube_search_url(query)
        self.web.load(QUrl(search))

    def load_spotify_web_search(self, query: str):
        self.current_title = query
        self.web.load(QUrl(spotify_search_url(query)))

    def open_in_spotify_app(self, query: str):
        uri = spotify_uri_search(query)
        try:
            webbrowser.open(uri)
        except Exception:
            webbrowser.open(spotify_search_url(query))

# ---------- Card ----------
class Card(QFrame):
    def __init__(self, title, mood=None, parent=None):
        super().__init__(parent)
        self.mood = mood
        self.setFixedSize(180, 120)
        self.setStyleSheet("QFrame{background:white;border-radius:12px;}QFrame:hover{background:#fff0f6}")
        l = QVBoxLayout(self)
        lbl = QLabel(title)
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        l.addWidget(lbl)

    def mousePressEvent(self, event):
        w = self
        while w and not isinstance(w, RecommendationApp):
            w = w.parent()
        if isinstance(w, RecommendationApp):
            w.show_playlist(self.mood)

# ---------- Main App ----------
class RecommendationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HILOM — Recommendation (YouTube + Spotify + Books + Podcasts)")
        self.setGeometry(60, 30, 1400, 760)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8,8,8,8)


        
        # Center layout
        center_layout = QVBoxLayout()
        header = QLabel("RECOMMENDATION")
        header.setFont(QFont("Arial", 28, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        center_layout.addWidget(self.tabs)

        # Music Tab
        music_tab = QWidget()
        music_v = QVBoxLayout()
        grid = QGridLayout()
        moods = list(mood_content.keys())
        for i, m in enumerate(moods):
            c = Card(m, m, parent=self)
            wrapper = QWidget()
            wl = QVBoxLayout(wrapper)
            wl.setContentsMargins(0,0,0,0)
            wl.addWidget(c, alignment=Qt.AlignCenter)
            grid.addWidget(wrapper, i//4, i%4)
        music_v.addLayout(grid)

        # Controls
        ctrl = QHBoxLayout()
        self.random_btn = QPushButton("Random")
        self.random_btn.clicked.connect(self.random_pick)
        ctrl.addWidget(self.random_btn)
        
        self.fav_song_btn = QPushButton("❤️ Favorite Song")
        self.fav_song_btn.clicked.connect(self.favorite_song)
        ctrl.addWidget(self.fav_song_btn)
        
        self.fav_video_btn = QPushButton("❤️ Favorite Video")
        self.fav_video_btn.clicked.connect(self.favorite_video)
        ctrl.addWidget(self.fav_video_btn)
        
        self.fav_book_btn = QPushButton("❤️ Favorite Book")
        self.fav_book_btn.clicked.connect(self.favorite_book)
        ctrl.addWidget(self.fav_book_btn)
        
        ctrl.addStretch()
        music_v.addLayout(ctrl)

        # Song list
        self.song_list = QListWidget()
        self.song_list.itemClicked.connect(self.song_single_click)
        self.song_list.itemDoubleClicked.connect(self.song_double_click)
        music_v.addWidget(self.song_list)

        # Videos list
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.video_single_click)
        self.video_list.itemDoubleClicked.connect(self.song_double_click)
        music_v.addWidget(QLabel("Youtube:"))
        music_v.addWidget(self.video_list)

        # Books list
        self.book_list = QListWidget()
        self.book_list.itemClicked.connect(self.book_click)
        music_v.addWidget(QLabel("Books:"))
        music_v.addWidget(self.book_list)

        music_tab.setLayout(music_v)
        self.tabs.addTab(music_tab, "RECOMMENDATIONS")

        # Center + Player
        center_and_player = QHBoxLayout()
        center_container = QWidget()
        center_container.setLayout(center_layout)
        center_container.setMinimumWidth(520)
        center_and_player.addWidget(center_container)

        self.player = EmbeddedPlayer()
        center_and_player.addWidget(self.player, 1)

        # Connect toolbar
        self.player.btn_youtube.triggered.connect(self._player_play_youtube_current)
        self.player.btn_spotify_web.triggered.connect(self._player_play_spotify_web_current)
        self.player.btn_spotify_app.triggered.connect(self._player_open_spotify_app_current)

        main_layout.addLayout(center_and_player, 1)

        # State
        self.current_mood = None
        self.current_titles = []
        self.favorites = {"music": [], "video": [], "book": []}
        self.load_favorites()

    # Show playlist
    def show_playlist(self, mood):
        self.current_mood = mood
        content = mood_content.get(mood, {})
        self.current_titles = content.get("songs", [])
        self.song_list.clear()
        self.video_list.clear()
        self.book_list.clear()

        for t in content.get("songs", []):
            self.song_list.addItem(QListWidgetItem(t))
        for v in content.get("videos", []):
            self.video_list.addItem(QListWidgetItem(v["title"]))
        for b in content.get("books", []):
            self.book_list.addItem(QListWidgetItem(b["title"]))

        self.tabs.setCurrentIndex(0)

    # Song click
    def song_single_click(self, item):
        title = item.text()
        if not title: return
        self.player.load_youtube_search_and_autoplay(title)
        log_history("music", title)

    def song_double_click(self, item):
        title = item.text()
        if not title: return
        self.player.load_youtube_search_and_autoplay(title)
        log_history("music", title)

    # Video click
    def video_single_click(self, item):
        title = item.text()
        if not title: return
        vids = mood_content.get(self.current_mood, {}).get("videos", [])
        for v in vids:
            if v["title"] == title:
                self.player.load_youtube_search_and_autoplay(v["youtube"])
                log_history("video", title)
                break

    # Book click
    def book_click(self, item):
        title = item.text()
        books = mood_content.get(self.current_mood, {}).get("books", [])
        for b in books:
            if b["title"] == title:
                webbrowser.open(b["link"])
                log_history("book", title)
                break

    # Random pick
    def random_pick(self):
        if self.current_mood:
            pick = random.choice(self.current_titles)
        else:
            mood = random.choice(list(mood_content.keys()))
            pick = random.choice(mood_content[mood]["songs"])
            self.show_playlist(mood)
        self.player.load_youtube_search_and_autoplay(pick)
        matches = self.song_list.findItems(pick, Qt.MatchExactly)
        if matches:
            self.song_list.setCurrentItem(matches[0])

    def favorite_song(self):
        item = self.song_list.currentItem()
        if item and item.text() not in self.favorites["music"]:
            self.favorites["music"].append(item.text())
            print(f"Favorited song: {item.text()}")

    def favorite_video(self):
        item = self.video_list.currentItem()
        if item and item.text() not in self.favorites["video"]:
            self.favorites["video"].append(item.text())
            print(f"Favorited video: {item.text()}")

    def favorite_book(self):
        item = self.book_list.currentItem()
        if item and item.text() not in self.favorites["book"]:
            self.favorites["book"].append(item.text())
            self.save_favorites()
            print(f"Favorited book: {item.text()}")

    def load_favorites(self):
        try:
            with open("favorites.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2:
                        cat, item = row
                        if cat in self.favorites:
                            self.favorites[cat].append(item)
        except FileNotFoundError:
            pass

    def save_favorites(self):
        with open("favorites.csv", "w", newline="") as f:
            writer = csv.writer(f)
            for cat, items in self.favorites.items():
                for item in items:
                    writer.writerow([cat, item])

    # Toolbar wrappers
    def _player_play_youtube_current(self):
        title = self._current_title_or_selected()
        if title:
            self.player.load_youtube_search_and_autoplay(title)

    def _player_play_spotify_web_current(self):
        title = self._current_title_or_selected()
        if title:
            self.player.load_spotify_web_search(title)

    def _player_open_spotify_app_current(self):
        title = self._current_title_or_selected()
        if title:
            self.player.open_in_spotify_app(title)

    def _current_title_or_selected(self):
        sel = self.song_list.currentItem()
        if sel:
            return sel.text()
        if self.current_titles:
            return self.current_titles[0]
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'background_label'):
            self.background_label.setGeometry(0, 0, self.width(), self.height())


if __name__ == "__main__":
    try:
        init_database()
        app = QApplication(sys.argv)
        window = HilomMainWindow()
        window.showFullScreen()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        import traceback
        traceback.print_exc() 