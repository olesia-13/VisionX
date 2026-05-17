import sys
import os
from PySide6.QtCore import Qt, QSize, QThread, QObject, Signal, Slot
from time import perf_counter
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                               QPushButton, QSlider, QHBoxLayout, QVBoxLayout,
                               QFrame, QGraphicsBlurEffect, QFileDialog, QScrollArea,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush
from core.main import detect
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# ----------------------------------------------------
# 1. СТИЛІ

BG_COLOR = "#F9F5FF"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E4E4E4"
TEXT_MAIN = "#000000"
TEXT_MUTED = "#696969"
PURPLE_PRIMARY = "#A06CFF"
GRAY = "#D0D0D0"
GRAY_BORDER = "#B4B4B4"

STYLE_SHEET = f"""
QMainWindow {{ background-color: {BG_COLOR}; }}

/* Картки-контейнери */
.CardFrame {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 20px;
}}

/* Тексти заголовків карток */
QLabel#CardTitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}}

/* Пунктирна кнопка завантаження зліва */
QPushButton#UploadButton {{
    background-color: transparent;
    border: 2px dashed {GRAY};
    border-radius: 20px;
    color: {TEXT_MAIN};
    font-size: 13px;
    padding: 10px;
    text-align: center;
}}
QPushButton#UploadButton:hover {{
    border-color: {PURPLE_PRIMARY};
    background-color: #F8F5FF;
    color: {PURPLE_PRIMARY};
}}

/* Кнопка Очистити (замість пунктирної після завантаження) */
QPushButton#ClearButton {{
    background-color: transparent;
    border: 2px dashed #FF5C5C;
    border-radius: 20px;
    color: #FF5C5C;
    font-size: 13px;
    font-weight: bold;
    padding: 10px;
    text-align: center;
}}
QPushButton#ClearButton:hover {{
    background-color: #FFF5F5;
}}

/* Кнопки вибору кольору */
QPushButton.ColorButton {{
    background-color: {CARD_BG};
    border: 1px solid {GRAY_BORDER};
    border-radius: 12px;
    color: {TEXT_MAIN};
    font-size: 12px;
    text-align: left;
    padding-left: 15px;
}}
QPushButton.ColorButton:checked {{
    border: 2px solid {PURPLE_PRIMARY};
    background-color: #F8F5FF;
}}

/* Слайдери */
QSlider::groove:horizontal {{ border: none; height: 6px; background: #EBE1FF; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {PURPLE_PRIMARY}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: white; border: 2px solid {PURPLE_PRIMARY}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}

/* Кнопка сканування */
QPushButton#ScanButton {{
    background-color: #C0A3F7;
    color: white;
    border-radius: 14px;
    font-size: 13px;
    font-weight: bold;
    padding-left: 10px;
}}
QPushButton#ScanButton:hover {{ background-color: {PURPLE_PRIMARY}; }}

/* Кнопка збереження */
QPushButton#SaveButton {{
    background-color: #F8F5FF;
    color: {PURPLE_PRIMARY};
    border: 1px solid #EBE1FF;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    padding: 6px 15px;
}}
QPushButton#SaveButton:hover {{
    background-color: #EBE1FF;
}}

/* Статистичні плашки */
.StatFrame {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 16px;
}}

/* Стилі для скролбару правої колонки */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: #D8C3FF;
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PURPLE_PRIMARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

/* Таблиця OBJECT REGISTRY */
QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: #F0F0F0;
    font-size: 12px;
    color: {TEXT_MAIN};
}}
QHeaderView::section {{
    background-color: #FCFAFF;
    color: {TEXT_MUTED};
    font-weight: bold;
    font-size: 11px;
    border: none;
    border-bottom: 1px solid #EBE1FF;
    padding: 8px 10px;
    text-align: left;
}}
QTableWidget::item {{
    border-bottom: 1px solid #F4F4F4;
    padding: 5px 10px;
}}
QTableWidget::item:selected {{
    background-color: #F8F5FF;
    color: {TEXT_MAIN};
}}
"""

class DetectionWorker(QObject):
    finished = Signal(list, int, dict, str)
    progress = Signal(int)  # опціонально

    def __init__(self, image_path, colors_to_check, params):
        super().__init__()
        self.image_path = image_path
        # colors_to_check: list of tuples (color_name, bgr_tuple, hex)
        self.colors_to_check = colors_to_check
        self.params = params

    @Slot()
    def run(self):
        try:
            start = perf_counter()
            all_results = []
            breakdown = {}
            for color_name, bgr, hex_color in self.colors_to_check:
                # call detect; it returns list of Detected objects
                try:
                    detections = detect(
                        self.image_path,
                        target_color=bgr,
                        hue_range=self.params.get("hue_range", None),
                        min_s=self.params.get("min_s", 150),
                        min_v=self.params.get("min_v", 60),
                        min_area=self.params.get("min_area", 120),
                        blur_level=self.params.get("blur_level", 1),
                        morphology_level=self.params.get("morphology_level", 1),
                    )
                except Exception as e:
                    detections = []
                for det in detections:
                    all_results.append({
                        "color_name": color_name,
                        "bgr": bgr,
                        "hex": hex_color,
                        "center": det.center,
                        "box": det.box,
                        "area": det.area
                    })
                breakdown[color_name] = len(detections)
            elapsed = int((perf_counter() - start) * 1000)
            self.finished.emit(all_results, elapsed, breakdown, "")
        except Exception as e:
            self.finished.emit([], 0, {}, str(e))

class AspectRatioLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update_image()

    def clear(self):
        self._pixmap = None
        super().clear()

    def update_image(self):
        if self._pixmap and not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()


# ----------------------------------------------------
# 2. ІНТЕРФЕЙС

class ColorHunterUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COLOR HUNTER / vX")
        self.resize(1280, 830)
        self.setMinimumSize(1150, 800)
        self.setStyleSheet(STYLE_SHEET)

        self.setAcceptDrops(True)

        self.color_buttons = []
        self.current_image_path = None

        self._detection_thread = None
        self._detection_worker = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ----------------------------------------------------
        # ШАПКА

        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(65)
        self.header_frame.setStyleSheet(
            f"background-color: rgba(255, 255, 255, 0.7); border-bottom: 1px solid {BORDER_COLOR};")

        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(35)
        self.header_frame.setGraphicsEffect(blur)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title_label = QLabel()
        title_label.setText(f"""
            <span style='color: {PURPLE_PRIMARY}; font-size: 24px;'>●</span> 
            <span style='font-weight: bold; font-size: 16px; color: black;'>COLOR HUNTER </span>
            <span style='font-size: 16px; color: {TEXT_MUTED};'>/ vX</span><br>
            <span style='font-size: 10px; color: {TEXT_MUTED}; font-weight: bold; letter-spacing: 2px;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;AUTONOMOUS VISION MODULE</span>
        """)
        header_layout.addWidget(title_label)

        hsv_icon_path = os.path.join(IMAGES_DIR, "hsv_pipeline.svg").replace('\\', '/')
        header_menu = QLabel(
            f"<img src='{hsv_icon_path}' width='14' height='14'>&nbsp;HSV pipeline   •   "
            f"connected components   •   multi-color"
        )
        header_menu.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        header_layout.addWidget(header_menu, alignment=Qt.AlignRight | Qt.AlignVCenter)

        root_layout.addWidget(self.header_frame)


        workspace_widget = QWidget()
        workspace_layout = QHBoxLayout(workspace_widget)
        workspace_layout.setContentsMargins(30, 20, 20, 25)
        workspace_layout.setSpacing(25)
        root_layout.addWidget(workspace_widget)

        # ЛІВА КОЛОНКА
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        # 01 / INPUT CARD
        input_card = QFrame()
        input_card.setProperty("class", "CardFrame")
        input_card.setFixedHeight(140)

        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 10, 20, 12)

        input_title = QLabel("01 / INPUT")
        input_title.setObjectName("CardTitle")
        input_layout.addWidget(input_title)

        self.upload_btn = QPushButton()
        self.upload_btn.setObjectName("UploadButton")
        self.upload_btn.setCheckable(False)
        self.upload_btn.setFixedHeight(85)
        self.upload_btn.clicked.connect(self.open_file_dialog)

        upload_content_layout = QVBoxLayout(self.upload_btn)
        upload_content_layout.setContentsMargins(0, 5, 0, 5)
        upload_content_layout.setSpacing(4)
        upload_content_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join(IMAGES_DIR, "upload_image.svg")).pixmap(QSize(20, 20)))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("border: none; background: transparent;")
        upload_content_layout.addWidget(icon_label)

        text_label = QLabel("Завантажити зображення")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet(
            f"color: {TEXT_MAIN}; font-size: 12px; font-weight: normal; border: none; background: transparent;")
        upload_content_layout.addWidget(text_label)

        formats_label = QLabel(".png .jpg .jpeg")
        formats_label.setAlignment(Qt.AlignCenter)
        formats_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none; background: transparent;")
        upload_content_layout.addWidget(formats_label)

        input_layout.addWidget(self.upload_btn)

        self.clear_btn = QPushButton()
        self.clear_btn.setObjectName("ClearButton")
        self.clear_btn.setFixedHeight(85)
        self.clear_btn.clicked.connect(self.clear_image)

        clear_content_layout = QVBoxLayout(self.clear_btn)
        clear_content_layout.setContentsMargins(0, 5, 0, 5)
        clear_content_layout.setSpacing(6)
        clear_content_layout.setAlignment(Qt.AlignCenter)

        delete_icon_label = QLabel()
        delete_icon_label.setPixmap(QIcon(os.path.join(IMAGES_DIR, "delete.svg")).pixmap(QSize(24, 24)))
        delete_icon_label.setAlignment(Qt.AlignCenter)
        delete_icon_label.setStyleSheet("border: none; background: transparent;")
        clear_content_layout.addWidget(delete_icon_label)

        clear_text_label = QLabel("Очистити")
        clear_text_label.setAlignment(Qt.AlignCenter)
        clear_text_label.setStyleSheet(
            "color: #FF5C5C; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        clear_content_layout.addWidget(clear_text_label)

        input_layout.addWidget(self.clear_btn)
        self.clear_btn.hide()

        left_column.addWidget(input_card)

        # 02 / TARGET COLORS CARD
        colors_card = QFrame()
        colors_card.setProperty("class", "CardFrame")
        colors_layout = QVBoxLayout(colors_card)
        colors_layout.setContentsMargins(20, 12, 20, 15)

        colors_title = QLabel("02 / TARGET COLORS")
        colors_title.setObjectName("CardTitle")
        colors_layout.addWidget(colors_title)

        colors_vbox = QVBoxLayout()
        colors_vbox.setSpacing(8)

        self.UI_COLOR_MAP = {
            "Червоний": {"bgr": (0, 0, 255), "hex": "#FF5C5C"},
            "Помаранчевий": {"bgr": (0, 130, 255), "hex": "#FF8200"},
            "Жовтий": {"bgr": (0, 255, 255), "hex": "#FFD233"},
            "Зелений": {"bgr": (0, 255, 0), "hex": "#33D12A"},
            "Блакитний": {"bgr": (255, 255, 0), "hex": "#00E1FF"},
            "Синій": {"bgr": (255, 0, 0), "hex": "#33A1FF"},
            "Фіолетовий": {"bgr": (255, 0, 100), "hex": "#6400FF"},
            "Рожевий": {"bgr": (200, 0, 255), "hex": "#FF00C8"},
            "Білий": {"bgr": (255, 255, 255), "hex": "#FFFFFF"},
            "Чорний": {"bgr": (0, 0, 0), "hex": "#000000"}
        }

        target_colors = [
            ("Червоний", "red.svg"), ("Помаранчевий", "orange.svg"),
            ("Жовтий", "yellow.svg"), ("Зелений", "green.svg"),
            ("Блакитний", "light_blue.svg"), ("Синій", "blue.svg"),
            ("Фіолетовий", "purple.svg"), ("Рожевий", "pink.svg"),
            ("Білий", "white.svg"), ("Чорний", "black.svg")
        ]

        for idx in range(0, len(target_colors), 2):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            name1, file1 = target_colors[idx]
            btn1 = QPushButton(f"  {name1}")
            btn1.setProperty("class", "ColorButton")
            btn1.setCheckable(True)
            btn1.setIcon(QIcon(os.path.join(IMAGES_DIR, file1)))
            btn1.setIconSize(QSize(16, 16))
            btn1.setFixedHeight(34)
            btn1.toggled.connect(self.update_active_colors_count)
            row_layout.addWidget(btn1)
            self.color_buttons.append(btn1)

            if idx + 1 < len(target_colors):
                name2, file2 = target_colors[idx + 1]
                btn2 = QPushButton(f"  {name2}")
                btn2.setProperty("class", "ColorButton")
                btn2.setCheckable(True)
                btn2.setIcon(QIcon(os.path.join(IMAGES_DIR, file2)))
                btn2.setIconSize(QSize(16, 16))
                btn2.setFixedHeight(34)
                btn2.toggled.connect(self.update_active_colors_count)
                row_layout.addWidget(btn2)
                self.color_buttons.append(btn2)

            colors_vbox.addLayout(row_layout)

        colors_layout.addLayout(colors_vbox)
        left_column.addWidget(colors_card)

        # 03 / ROBUSTNESS CARD
        robust_card = QFrame()
        robust_card.setProperty("class", "CardFrame")
        robust_layout = QVBoxLayout(robust_card)
        robust_layout.setContentsMargins(20, 12, 20, 15)
        robust_layout.setSpacing(10)

        robust_title = QLabel("03 / ROBUSTNESS")
        robust_title.setObjectName("CardTitle")
        robust_layout.addWidget(robust_title)

        def create_slider_block(label_text, min_val, max_val, default_val, unit=""):
            block_layout = QVBoxLayout()
            lbl_layout = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 11px;")
            val_lbl = QLabel(f"{default_val}{unit}")
            val_lbl.setStyleSheet(f"color: {PURPLE_PRIMARY}; font-size: 11px; font-weight: bold;")
            lbl_layout.addWidget(lbl)
            lbl_layout.addWidget(val_lbl, alignment=Qt.AlignRight)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)
            slider.valueChanged.connect(lambda val: val_lbl.setText(f"{val}{unit}"))

            block_layout.addLayout(lbl_layout)
            block_layout.addWidget(slider)
            robust_layout.addLayout(block_layout)
            return slider

        self.slider_area = create_slider_block("Мін. площа об'єкта", 1, 2000, 120, "px")
        self.slider_blur = create_slider_block("Розмиття (антишум)", 0, 3, 1)
        self.slider_morph = create_slider_block("Морфологія (open)", 0, 3, 1)
        left_column.addWidget(robust_card)

        # СКАНУВАННЯ
        self.scan_btn = QPushButton(" ЗАПУСТИТИ СКАНУВАННЯ")
        self.scan_btn.setObjectName("ScanButton")
        self.scan_btn.setIcon(QIcon(os.path.join(IMAGES_DIR, "start_scaning.svg")))
        self.scan_btn.setIconSize(QSize(16, 16))
        self.scan_btn.setFixedHeight(44)
        self.scan_btn.clicked.connect(self.start_scan)
        left_column.addWidget(self.scan_btn)

        left_column.addStretch()
        workspace_layout.addLayout(left_column, stretch=2)

        # ПРАВА КОЛОНКА
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QFrame.NoFrame)
        self.right_scroll.setStyleSheet("background-color: transparent;")

        self.right_content_widget = QWidget()
        self.right_content_widget.setStyleSheet("background-color: transparent;")
        right_column = QVBoxLayout(self.right_content_widget)
        right_column.setContentsMargins(0, 0, 10, 0)
        right_column.setSpacing(20)

        # 1. КАРТКА ЗОБРАЖЕННЯ
        detection_card = QFrame()
        detection_card.setProperty("class", "CardFrame")
        detection_layout = QVBoxLayout(detection_card)
        detection_layout.setContentsMargins(25, 20, 25, 25)

        det_header_layout = QHBoxLayout()
        det_title = QLabel("OUTPUT / DETECTION")
        det_title.setObjectName("CardTitle")

        self.save_btn = QPushButton(" Зберегти")
        self.save_btn.setObjectName("SaveButton")
        self.save_btn.setIcon(QIcon(os.path.join(IMAGES_DIR, "save.svg")))
        self.save_btn.hide()

        det_header_layout.addWidget(det_title)
        det_header_layout.addStretch()
        det_header_layout.addWidget(self.save_btn)
        detection_layout.addLayout(det_header_layout)

        self.image_display = QFrame()
        self.image_display.setMinimumHeight(450)
        self.default_display_style = "border: 2px dashed #EBE1FF; border-radius: 20px; background-color: #FCFAFF;"
        self.loaded_display_style = "border: none; background-color: transparent;"
        self.image_display.setStyleSheet(self.default_display_style)

        img_layout = QVBoxLayout(self.image_display)
        img_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = AspectRatioLabel()
        self.image_label.hide()
        img_layout.addWidget(self.image_label)

        right_upload_icon = os.path.join(IMAGES_DIR, "upload_image_right.svg").replace('\\', '/')
        self.placeholder_lbl = QLabel(
            f"<img src='{right_upload_icon}' width='42' height='42'><br><br>"
            f"Завантажте зображення, щоб почати пошук об'єктів"
        )
        self.placeholder_lbl.setAlignment(Qt.AlignCenter)
        self.placeholder_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 14px; border: none; background: transparent;")
        img_layout.addWidget(self.placeholder_lbl)

        detection_layout.addWidget(self.image_display, stretch=1)
        right_column.addWidget(detection_card)

        # 2. БЛОК ЗНИЗУ
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        def create_stat_tile(title, default_value):
            tile = QFrame()
            tile.setProperty("class", "StatFrame")
            tile.setFixedHeight(75)
            t_layout = QVBoxLayout(tile)
            t_layout.setContentsMargins(20, 12, 20, 12)

            t_lbl = QLabel(title.upper())
            t_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
            v_lbl = QLabel(str(default_value))
            v_lbl.setStyleSheet(
                f"color: {PURPLE_PRIMARY}; font-size: 22px; font-weight: bold; background: transparent;")

            t_layout.addWidget(t_lbl)
            t_layout.addWidget(v_lbl)
            stats_layout.addWidget(tile)
            return v_lbl

        self.lbl_stat_objects = create_stat_tile("Detected Objects", "0")
        self.lbl_stat_colors = create_stat_tile("Active Colors", "0")
        self.lbl_stat_time = create_stat_tile("Scan Time", "0 ms")

        res_tile = QFrame()
        res_tile.setProperty("class", "StatFrame")
        res_tile.setFixedHeight(75)
        r_layout = QVBoxLayout(res_tile)
        r_layout.setContentsMargins(20, 12, 20, 12)
        r_lbl = QLabel("RESOLUTION")
        r_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")

        self.lbl_stat_resolution = QLabel("—")
        self.lbl_stat_resolution.setStyleSheet(
            f"color: {TEXT_MAIN}; font-size: 22px; font-weight: bold; background: transparent;")

        r_layout.addWidget(r_lbl)
        r_layout.addWidget(self.lbl_stat_resolution)
        stats_layout.addWidget(res_tile)

        right_column.addLayout(stats_layout)

        # 3. БЛОК BREAKDOWN
        self.breakdown_card = QFrame()
        self.breakdown_card.setProperty("class", "CardFrame")
        breakdown_layout = QVBoxLayout(self.breakdown_card)
        breakdown_layout.setContentsMargins(25, 20, 25, 20)

        br_title = QLabel("BREAKDOWN")
        br_title.setObjectName("CardTitle")
        breakdown_layout.addWidget(br_title)

        self.breakdown_tags_layout = QHBoxLayout()
        self.breakdown_tags_layout.setAlignment(Qt.AlignLeft)
        self.breakdown_tags_layout.setSpacing(10)
        breakdown_layout.addLayout(self.breakdown_tags_layout)

        right_column.addWidget(self.breakdown_card)
        self.breakdown_card.hide()

        # 4. БЛОК OBJECT REGISTRY
        self.registry_card = QFrame()
        self.registry_card.setProperty("class", "CardFrame")
        registry_layout = QVBoxLayout(self.registry_card)
        registry_layout.setContentsMargins(25, 20, 25, 25)

        reg_header_layout = QHBoxLayout()
        reg_title = QLabel("OBJECT REGISTRY")
        reg_title.setObjectName("CardTitle")

        self.reg_entries_lbl = QLabel("0 entries")
        self.reg_entries_lbl.setStyleSheet(
            f"background-color: #F9F5FF; color: {PURPLE_PRIMARY}; font-size: 11px; font-weight: bold; border-radius: 10px; padding: 4px 10px;")

        reg_header_layout.addWidget(reg_title)
        reg_header_layout.addWidget(self.reg_entries_lbl)
        reg_header_layout.addStretch()
        registry_layout.addLayout(reg_header_layout)

        # Таблиця
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Color", "Center (x, y)", "BBox (x, y, w, h)", "Area"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFixedHeight(250)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        registry_layout.addWidget(self.table)

        right_column.addWidget(self.registry_card)
        self.registry_card.hide()

        right_column.addStretch()

        self.right_scroll.setWidget(self.right_content_widget)
        workspace_layout.addWidget(self.right_scroll, stretch=5)

    # ----------------------------------
    # ЛОГІКА

    def update_active_colors_count(self):
        active_count = sum(1 for btn in self.color_buttons if btn.isChecked())
        self.lbl_stat_colors.setText(str(active_count))

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Оберіть зображення", "", "Зображення (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        self.current_image_path = file_path

        self.placeholder_lbl.hide()
        self.image_label.setPixmap(pixmap)
        self.image_label.show()
        self.image_display.setStyleSheet(self.loaded_display_style)

        self.upload_btn.hide()
        self.clear_btn.show()

        self.lbl_stat_resolution.setText(f"{pixmap.width()}x{pixmap.height()}")
        self.hide_scan_results()

    def clear_image(self):
        self.current_image_path = None
        self.image_label.clear()

        self.image_label.hide()
        self.placeholder_lbl.show()
        self.image_display.setStyleSheet(self.default_display_style)

        self.clear_btn.hide()
        self.upload_btn.show()

        self.lbl_stat_resolution.setText("—")
        self.hide_scan_results()

    def hide_scan_results(self):
        self.save_btn.hide()
        self.breakdown_card.hide()
        self.registry_card.hide()
        self.lbl_stat_objects.setText("0")
        self.lbl_stat_time.setText("0 ms")

    # ----------------------------------
    # ВИВЕДЕННЯ ПРИКЛАДУ РЕЗУЛЬТАТІВ

    def get_selected_colors(self):
        selected = []
        for btn in self.color_buttons:
            if btn.isChecked():
                name = btn.text().strip()
                color_info = self.UI_COLOR_MAP.get(name)
                if color_info:
                    selected.append((name, color_info["bgr"], color_info["hex"]))
        return selected

    def start_scan(self):
        if not self.current_image_path:
            return

        selected_colors = self.get_selected_colors()
        if not selected_colors:
            return

        self.scan_btn.setEnabled(False)
        self.lbl_stat_time.setText("—")
        self.lbl_stat_objects.setText("…")
        self.save_btn.hide()
        self.hide_scan_results()
        if self.current_image_path:
            original_pixmap = QPixmap(self.current_image_path)
            self.image_label.setPixmap(original_pixmap)
            self.image_label.show()
        params = {
            "hue_range": None,
            "min_s": 150,
            "min_v": 60,
            "min_area": int(self.slider_area.value()),
            "blur_level": int(self.slider_blur.value()),
            "morphology_level": int(self.slider_morph.value())
        }

        self._detection_thread = QThread()
        self._detection_worker = DetectionWorker(self.current_image_path, selected_colors, params)
        self._detection_worker.moveToThread(self._detection_thread)
        self._detection_thread.started.connect(self._detection_worker.run)
        # on finish
        self._detection_worker.finished.connect(self.on_detection_finished)

        def cleanup(results, elapsed, breakdown, error):
            try:
                self._detection_thread.quit()
                self._detection_thread.wait(2000)
            except Exception:
                pass

        self._detection_worker.finished.connect(cleanup)

        self._detection_thread.start()

    @Slot(list, int, dict, str)
    def on_detection_finished(self, results, elapsed_ms, breakdown, error_message):
        self.scan_btn.setEnabled(True)
        if error_message:
            self.lbl_stat_time.setText("error")
            return

        total_objects = len(results)
        self.lbl_stat_objects.setText(str(total_objects))
        self.lbl_stat_time.setText(f"{elapsed_ms} ms")
        for i in reversed(range(self.breakdown_tags_layout.count())):
            w = self.breakdown_tags_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for color_name, count in breakdown.items():
            hex_color = self.UI_COLOR_MAP.get(color_name, {}).get("hex", "#000000")
            tag = QLabel(
                f"<span style='color:{hex_color};'>●</span> {color_name}: <span style='color:{TEXT_MAIN};'>{count}</span>")
            tag.setStyleSheet(
                f"background-color: #FCFAFF; border: 1px solid #EBE1FF; border-radius: 12px; padding: 6px 12px; font-size: 11px; font-weight: bold;")
            self.breakdown_tags_layout.addWidget(tag)
        if breakdown:
            self.breakdown_card.show()

        self.table.setRowCount(total_objects)
        for row_idx, item in enumerate(results):
            id_item = QTableWidgetItem(f"{row_idx + 1:03d}")
            id_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            id_item.setForeground(QColor(TEXT_MUTED))
            self.table.setItem(row_idx, 0, id_item)

            color_item = QTableWidgetItem(item["color_name"])
            dot_pixmap = QPixmap(32, 32)
            dot_pixmap.fill(Qt.transparent)
            painter = QPainter(dot_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(item["hex"])))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 24, 24)
            painter.end()
            color_item.setIcon(QIcon(dot_pixmap))
            self.table.setItem(row_idx, 1, color_item)

            # center
            cx, cy = item["center"]
            center_item = QTableWidgetItem(f"{cx}, {cy}")
            center_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row_idx, 2, center_item)

            # bbox
            x, y, w, h = item["box"]
            bbox_item = QTableWidgetItem(f"{x}, {y}, {w}, {h}")
            bbox_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row_idx, 3, bbox_item)

            area_item = QTableWidgetItem(f"{int(item['area'])} px")
            area_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row_idx, 4, area_item)

        if total_objects > 0:
            self.reg_entries_lbl.setText(f"{total_objects} entries")
            self.registry_card.show()
            self.render_detections_on_pixmap(self.current_image_path, results)
            self.save_btn.show()
        else:
            self.reg_entries_lbl.setText("0 entries")
            self.registry_card.hide()
            self.save_btn.hide()


    def simulate_scan(self):
        self.start_scan()

    def render_detections_on_pixmap(self, image_path, results):
        base = QPixmap(image_path)
        if base.isNull():
            return

        pix = QPixmap(base)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        black_pen = painter.pen()
        black_pen.setColor(Qt.black)
        black_pen.setWidth(2)

        for item in results:
            try:
                x, y, w, h = map(int, item["box"])
                cx, cy = map(int, item["center"])
            except Exception:
                continue

            painter.setPen(black_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x, y, w, h)

            hex_color = item.get("hex", "#FF0000")
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(hex_color)))
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)

        painter.end()
        self.image_label.setPixmap(pix)
        self.image_label.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg')):
                event.accept()
                return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_image(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ColorHunterUI()
    ui.show()
    sys.exit(app.exec())