import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt, QSize


class DarkFramelessWindow(QWidget):
    """
    一个继承自 QWidget 的自定义窗口。
    特点：
    - 无系统边框和标题栏
    - 深色主题风格
    - 窗口和按钮均为圆角矩形
    - 包含“开始游戏”和“新建游戏流程”两个按钮
    """

    on_start_game_clicked = Signal()
    on_manager_flow_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. 设置窗口属性：无边框和透明背景
        #    - Qt.FramelessWindowHint: 移除窗口的边框和标题栏。
        #    - Qt.WA_TranslucentBackground: 允许背景透明，这是实现圆角的关键。
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置窗口标题（在任务栏中可能显示）和初始大小
        self.setWindowTitle("游戏启动器")

        # 2. 创建UI组件
        self.setup_ui()

        # 3. 应用QSS样式表
        self.apply_stylesheet()

        # 4. 连接信号与槽
        self.connect_signals()

    def setup_ui(self):
        """初始化用户界面"""
        # 创建按钮
        self.start_button = QPushButton("开始游戏")
        self.manage_flow_button = QPushButton("新建游戏流程")

        # 设置按钮的最小高度，使其看起来更舒适
        self.start_button.setMinimumHeight(45)
        self.manage_flow_button.setMinimumHeight(45)

        # 创建一个垂直布局管理器
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 设置内边距
        main_layout.setSpacing(15)  # 设置控件之间的间距

        # 将按钮添加到布局中
        main_layout.addStretch()  # 添加一个弹性空间，将按钮推向中心
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.manage_flow_button)
        main_layout.addStretch()  # 添加一个弹性空间

        # 为主窗口设置布局
        self.setLayout(main_layout)

    def apply_stylesheet(self):
        """应用QSS样式"""
        # 使用多行字符串定义QSS样式
        # 类似于Web开发中的CSS
        qss = """
            /* QWidget#main_widget 是为了确保样式只应用于这个窗口，而不是所有QWidget */
            /* 如果这个窗口是主窗口，也可以直接用 QWidget */
            QWidget {
                background-color: #2c3e50; /* 深蓝灰色背景 */
                border-radius: 15px;      /* 圆角半径 */
                color: white;             /* 默认字体颜色 */
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; /* 字体 */
            }

            QPushButton {
                background-color: #34495e; /* 按钮背景色，比主背景稍亮 */
                color: #ecf0f1;           /* 按钮文字颜色 */
                border: 1px solid #2980b9;/* 边框颜色 */
                border-radius: 8px;       /* 按钮圆角 */
                padding: 10px;            /* 内边距 */
                font-size: 16px;          /* 字体大小 */
                font-weight: bold;        /* 字体加粗 */
            }

            /* 鼠标悬停在按钮上时的样式 */
            QPushButton:hover {
                background-color: #4a6278; /* 悬停时背景变亮 */
                border: 1px solid #3498db;
            }

            /* 鼠标按下按钮时的样式 */
            QPushButton:pressed {
                background-color: #2980b9; /* 按下时背景变为边框色 */
            }
        """
        self.setStyleSheet(qss)

    def connect_signals(self):
        """连接按钮点击信号到槽函数"""
        self.start_button.clicked.connect(self.on_start_game_clicked.emit)
        self.manage_flow_button.clicked.connect(self.on_manager_flow_clicked.emit)
