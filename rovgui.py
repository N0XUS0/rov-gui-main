import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QSlider, QGridLayout, QTextEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QTime, QProcess

import cv2
from PyQt5.QtGui import QImage, QPixmap

class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Cameras")
        self.setGeometry(100, 100, 1300, 700)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.captures = []
        self.labels = []

        # شغل أول 4 كاميرات
        for i in range(4):
            cap = cv2.VideoCapture(i)
            self.captures.append(cap)

            label = QLabel()
            label.setFixedSize(620, 360)
            label.setStyleSheet("background-color: black;")
            self.labels.append(label)
            self.layout.addWidget(label, i // 2, i % 2)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)

    def update_frames(self):
        for i, cap in enumerate(self.captures):
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image).scaled(self.labels[i].width(), self.labels[i].height(), Qt.KeepAspectRatio)
                self.labels[i].setPixmap(pixmap)

    def closeEvent(self, event):
        for cap in self.captures:
            cap.release()
        event.accept()

class ControlPanelWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROV Control Panel")
        self.setGeometry(200, 100, 1400, 900)
        self.setStyleSheet("background-color: #2c2c2c; color: white;")
        self.process = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # الكاميرات
        self.camera_layout = QGridLayout()
        self.camera_labels = []
        for i in range(4):
            cam_label = QLabel(f"Camera {i+1}")
            cam_label.setFixedSize(630, 390)
            cam_label.setAlignment(Qt.AlignCenter)
            cam_label.setStyleSheet("background-color: #000; color: white; border: 2px solid #555;")
            self.camera_labels.append(cam_label)
        self.camera_positions = [0, 1, 2, 3]
        self.update_camera_grid()

        # زرار فتح كل الكاميرات
        self.open_all_cameras_button = QPushButton(" open cams ")
        self.open_all_cameras_button.setStyleSheet(
            "background-color: #008CBA; color: white; padding: 10px; font-weight: bold;"
        )
        self.open_all_cameras_button.clicked.connect(self.open_all_cameras)

        # تجميع الكاميرات والزرار في Layout واحد
        camera_control_layout = QVBoxLayout()
        camera_control_layout.addLayout(self.camera_layout)
        camera_control_layout.addWidget(self.open_all_cameras_button)
        camera_widget = QWidget()
        camera_widget.setLayout(camera_control_layout)

        # البانل اليمين
        right_panel = QVBoxLayout()

        actuators_box = QGroupBox("Tasks")
        actuator_layout = QVBoxLayout()
        for i in range(4):
            btn = QPushButton(f"Task {i+1}")
            btn.setStyleSheet("background-color: orange; padding: 10px; font-weight: bold;")
            btn.clicked.connect(lambda _, num=i+1: self.run_task_script(num))
            actuator_layout.addWidget(btn)
        actuators_box.setLayout(actuator_layout)

        sensors_box = QGroupBox("Sensors")
        sensor_layout = QVBoxLayout()
        for name in ["IMU", "Depth", "Leak", "Current"]:
            label = QLabel(name + ": [data]")
            label.setStyleSheet("padding: 5px;")
            sensor_layout.addWidget(label)
        sensors_box.setLayout(sensor_layout)

        self.camera_dropdowns = []
        camera_switch_box = QGroupBox("Switch Camera Locations")
        camera_switch_layout = QVBoxLayout()
        for i in range(4):
            combo = QComboBox()
            combo.addItems(["1", "2", "3", "4"])
            combo.setCurrentIndex(i)
            combo.currentIndexChanged.connect(self.switch_camera_positions)
            self.camera_dropdowns.append(combo)
            camera_switch_layout.addWidget(QLabel(f"Camera {i+1} Position:"))
            camera_switch_layout.addWidget(combo)
        camera_switch_box.setLayout(camera_switch_layout)

        connection_box = QGroupBox("Connection Status")
        connection_layout = QVBoxLayout()
        self.rov_status = QLabel("ROV: Connected")
        self.joystick_status = QLabel("Joystick: Disconnected")
        connection_layout.addWidget(self.rov_status)
        connection_layout.addWidget(self.joystick_status)
        connection_box.setLayout(connection_layout)

        sensitivity_box = QGroupBox("Controller Sensitivity")
        sensitivity_layout = QVBoxLayout()
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(0)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(50)
        self.sensitivity_slider.setTickInterval(10)
        self.sensitivity_slider.setTickPosition(QSlider.TicksBelow)
        self.sensitivity_value_label = QLabel("50")
        self.sensitivity_value_label.setAlignment(Qt.AlignCenter)
        self.sensitivity_slider.valueChanged.connect(
            lambda value: self.sensitivity_value_label.setText(str(value))
        )
        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_value_label)
        sensitivity_box.setLayout(sensitivity_layout)

        float_box = QGroupBox("Float Device Reading")
        float_layout = QVBoxLayout()
        self.float_label = QLabel("Float Value: 0.0")
        self.float_label.setAlignment(Qt.AlignCenter)
        float_layout.addWidget(self.float_label)
        float_box.setLayout(float_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_elapsed = QTime(0, 0, 0)

        competition_box = QGroupBox("Competition Time")
        competition_layout = QVBoxLayout()
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 18))
        self.start_button = QPushButton("Start Timer")
        self.pause_button = QPushButton("Pause Timer")
        self.reset_button = QPushButton("Reset Timer")
        self.start_button.clicked.connect(self.start_competition_timer)
        self.pause_button.clicked.connect(self.pause_competition_timer)
        self.reset_button.clicked.connect(self.reset_competition_timer)
        for btn in [self.start_button, self.pause_button, self.reset_button]:
            btn.setStyleSheet("padding: 8px; background-color: #444; color: white;")
        competition_layout.addWidget(self.timer_label)
        competition_layout.addWidget(self.start_button)
        competition_layout.addWidget(self.pause_button)
        competition_layout.addWidget(self.reset_button)
        competition_box.setLayout(competition_layout)

        output_box = QGroupBox("Terminal Output")
        output_layout = QVBoxLayout()
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("background-color: black; color: lime;")
        output_layout.addWidget(self.output_display)
        output_box.setLayout(output_layout)

        right_panel.addWidget(actuators_box)
        right_panel.addWidget(sensors_box)
        right_panel.addWidget(camera_switch_box)
        right_panel.addWidget(connection_box)
        right_panel.addWidget(sensitivity_box)
        right_panel.addWidget(float_box)
        right_panel.addWidget(competition_box)
        right_panel.addWidget(output_box)
        right_panel.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        right_widget.setFixedWidth(400)

        main_layout.addWidget(camera_widget)
        main_layout.addWidget(right_widget)
        self.setLayout(main_layout)

    def run_task_script(self, task_number):
        script_name = f"task{task_number}.py"
        self.output_display.append(f"Running {script_name}...\n")
        self.process = QProcess(self)
        self.process.setProgram("python")
        self.process.setArguments([script_name])
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.start()

    def read_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output_display.append(data)

    def read_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.output_display.append(f"<span style='color:red'>{data}</span>")

    def switch_camera_positions(self):
        selected = [combo.currentIndex() for combo in self.camera_dropdowns]
        if len(set(selected)) == 4:
            self.camera_positions = selected
            self.update_camera_grid()

    def update_camera_grid(self):
        for i in reversed(range(self.camera_layout.count())):
            self.camera_layout.itemAt(i).widget().setParent(None)
        for idx, pos in enumerate(self.camera_positions):
            row = idx // 2
            col = idx % 2
            self.camera_layout.addWidget(self.camera_labels[pos], row, col)

    def start_competition_timer(self):
        self.timer.start(1000)

    def pause_competition_timer(self):
        self.timer.stop()

    def reset_competition_timer(self):
        self.timer.stop()
        self.time_elapsed = QTime(0, 0, 0)
        self.timer_label.setText("00:00:00")

    def update_timer(self):
        self.time_elapsed = self.time_elapsed.addSecs(1)
        self.timer_label.setText(self.time_elapsed.toString("hh:mm:ss"))

    def open_all_cameras(self):
        self.output_display.append("فتح جميع الكاميرات...\n")
        self.camera_window = CameraWindow()
        self.camera_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlPanelWindow()
    window.show()
    sys.exit(app.exec_())
