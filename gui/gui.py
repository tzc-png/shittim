import sys
import os
os.environ["G_DEBUG"] = "fatal-warnings"  # 只显示致命错误
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QLineEdit, QPushButton, QLabel,
                             QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl, QFileSystemWatcher, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)

# ==============================================================================
# ⚙️ 全局配置变量
# ==============================================================================
# 获取当前脚本的绝对路径（包含文件名）
current_file_path = os.path.abspath(__file__)

# 获取当前脚本所在的目录路径（不包含文件名）
current_dir = os.path.dirname(current_file_path)

CONFIG_FILE_PATH = os.path.join(current_dir, "../history/plana_history.jsonl")       # 历史对话文本配置文件路径（只读、监听）
AVATAR_ME_PATH = os.path.join(current_dir, "sensei.png")          # 你的头像路径
AVATAR_ROBOT_PATH = os.path.join(current_dir, "plana.png")    # 对方（普拉娜酱）的头像路径
LIVE_VIDEO_PATH = os.path.join(current_dir, "plana.webm") # 侧边动态立绘视频路径

# 外部命令配置
COMMAND_NAME = "shittim"           # 调用的主命令
COMMAND_ROLE = "plana"             # 调用的角色参数

# 窗口的标题
WINDOW_TITLE = "plana"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
LIVE_ZONE_WIDTH = 350
# ==============================================================================

def get_round_avatar(image_path, size=40):
    if not os.path.exists(image_path):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.lightGray)
        return pixmap
    src_pixmap = QPixmap(image_path)
    scaled_pixmap = src_pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    out_pixmap = QPixmap(size, size)
    out_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled_pixmap)
    painter.end()
    return out_pixmap

class MessageWidget(QFrame):
    def __init__(self, sender, content, timestamp, avatar_pixmap, is_loading=False, is_error=False, parent=None):
        super().__init__(parent)
        self.init_ui(sender, content, timestamp, avatar_pixmap, is_loading, is_error)

    def init_ui(self, sender, content, timestamp, avatar_pixmap, is_loading, is_error):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 5)
        self.main_layout.setSpacing(10)

        avatar_label = QLabel()
        avatar_label.setFixedSize(QSize(40, 40))
        avatar_label.setPixmap(avatar_pixmap)

        content_stack_layout = QVBoxLayout()
        content_stack_layout.setSpacing(4)

        display_name = "老师" if sender == "Me" else "普拉娜"
        name_time_label = QLabel(f"{display_name}  {timestamp}")
        name_time_label.setStyleSheet("font-size: 11px; color: #888888; font-family: sans-serif;")

        self.bubble = QFrame()
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # 【修改】控制文本颜色：如果是错误则显示红色加粗
        if is_error:
            content_label.setStyleSheet("font-size: 14px; color: #FF4D4F; font-weight: bold; font-family: sans-serif;")
        elif is_loading:
            content_label.setStyleSheet("font-size: 14px; color: #999999; font-style: italic; font-family: sans-serif;")
        else:
            content_label.setStyleSheet("font-size: 14px; color: #333333; font-family: sans-serif;")
            
        bubble_layout.addWidget(content_label)

        is_me = (sender == "Me")
        if is_me:
            name_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            content_stack_layout.addWidget(name_time_label)
            content_stack_layout.addWidget(self.bubble, alignment=Qt.AlignmentFlag.AlignRight)
            self.main_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            self.main_layout.addLayout(content_stack_layout)
            self.main_layout.addWidget(avatar_label, alignment=Qt.AlignmentFlag.AlignTop)
            
            if is_loading:
                self.bubble.setStyleSheet("QFrame { background-color: #E0E0E0; border-radius: 8px; }")
            else:
                self.bubble.setStyleSheet("QFrame { background-color: #95EC69; border-radius: 8px; }")
        else:
            name_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            content_stack_layout.addWidget(name_time_label)
            content_stack_layout.addWidget(self.bubble, alignment=Qt.AlignmentFlag.AlignLeft)
            self.main_layout.addWidget(avatar_label, alignment=Qt.AlignmentFlag.AlignTop)
            self.main_layout.addLayout(content_stack_layout)
            self.main_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            
            # 【修改】控制气泡背景色：如果是错误则显示浅红气泡
            if is_error:
                self.bubble.setStyleSheet("QFrame { background-color: #FFD8D8; border-radius: 8px; }")
            else:
                self.bubble.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 8px; }")

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

class CommandRunnerThread(QThread):
    # 【修改】让信号可以携带一个 int 类型的参数
    finished_signal = pyqtSignal(int)

    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        return_code = -1
        try:
            # 允许 check=False，以便能抓到进程退出时的真正错误码
            result = subprocess.run([COMMAND_NAME, COMMAND_ROLE, self.message], check=False)
            return_code = result.returncode
        except Exception as e:
            print(f"执行外部命令失败: {e}")
        finally:
            self.finished_signal.emit(return_code) # 将结果发回主线程

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.avatar_me = get_round_avatar(AVATAR_ME_PATH)    
        self.avatar_robot = get_round_avatar(AVATAR_ROBOT_PATH) 
        
        self.current_line_count = 0
        self.loading_widget = None # 用来保存临时的等待状态气泡控件
        
        self.init_ui()
        self.load_all_history_from_config()
        
        self.file_watcher = QFileSystemWatcher(self)
        if os.path.exists(CONFIG_FILE_PATH):
            self.file_watcher.addPath(CONFIG_FILE_PATH)
            self.file_watcher.fileChanged.connect(self.on_config_file_changed)

        QTimer.singleShot(100, self.scroll_to_bottom)

    def init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        global_layout = QHBoxLayout(self)
        global_layout.setContentsMargins(0, 0, 0, 0)
        global_layout.setSpacing(0)

        # ================= 左侧：立绘展示区 =================
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedWidth(LIVE_ZONE_WIDTH)
        
        palette = self.video_widget.palette()
        palette.setColor(self.video_widget.backgroundRole(), Qt.GlobalColor.white)
        self.video_widget.setPalette(palette)
        self.video_widget.setAutoFillBackground(True)
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0)

        video_path = os.path.abspath(LIVE_VIDEO_PATH)
        if os.path.exists(video_path):
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.media_player.play()
        else:
            placeholder = QLabel(f"未找到立绘视频\n{LIVE_VIDEO_PATH}")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888888; background-color: #FFFFFF;")
            self.video_widget = placeholder
            self.video_widget.setFixedWidth(LIVE_ZONE_WIDTH)

        global_layout.addWidget(self.video_widget)

        # ================= 右侧：聊天区 =================
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #F5F5F5; border: none; }")

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_container.setStyleSheet("background-color: #F5F5F5;")
        self.messages_layout.setContentsMargins(0, 10, 0, 10)
        self.messages_layout.setSpacing(10)

        self.top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.messages_layout.addSpacerItem(self.top_spacer)

        self.scroll_area.setWidget(self.messages_container)
        chat_layout.addWidget(self.scroll_area, stretch=1)

        # 底部输入框
        input_container = QFrame()
        input_container.setStyleSheet("QFrame { background-color: white; border-top: 1px solid #DDDDDD; }")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("想对普拉娜说点什么...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("QLineEdit { padding: 10px; font-size: 14px; border: 1px solid #DDDDDD; border-radius: 4px; }")

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton { padding: 10px 20px; font-size: 14px; background-color: #07C160; color: white; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #06AD56; }
            QPushButton:disabled { background-color: #A0A0A0; }
        """)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        chat_layout.addWidget(input_container, stretch=0)

        global_layout.addWidget(chat_container, stretch=1)
        self.setLayout(global_layout)

    def format_smart_datetime(self, raw_time_str):
        """将 2026-06-25 11:22:07 转换为 2026-06-25 11:22"""
        if not raw_time_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            # 尝试按照标准格式解析
            dt = datetime.strptime(raw_time_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # 如果 shittim 脚本传过来的格式没有秒，或者格式特殊，则原样返回防崩
            return raw_time_str.strip()

    def parse_json_line(self, line):
        try:
            data = json.loads(line.strip())
            role = data.get("role")
            content = data.get("content", "").strip()
            raw_time = data.get("time", "")
            
            if raw_time:
                try:
                    dt = datetime.strptime(raw_time.strip(), "%Y-%m-%d %H:%M:%S")
                    timestamp = dt.strftime("%H:%M")
                except ValueError:
                    timestamp = raw_time
            else:
                timestamp = datetime.now().strftime('%H:%M')
            
            sender = "Me" if role == "user" else "Robot"
            return sender, content, timestamp
        except Exception:
            return None

    def load_all_history_from_config(self):
        if not os.path.exists(CONFIG_FILE_PATH):
            return
        
        self.current_line_count = 0
        last_user_time = "" # 用来记住最近一次 user 处的原始 time 字符串
        
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line.strip())
                        role = data.get("role")
                        content = data.get("content", "").strip()
                        
                        if role == "user":
                            last_user_time = data.get("time", "")
                            sender = "Me"
                        else:
                            sender = "Robot"
                        
                        # 无论是 user 还是 assistant，统一格式化并使用当前配对的 user 时间
                        display_time = self.format_smart_datetime(last_user_time)
                        self.append_message_to_display(sender, content, display_time, auto_scroll=False)
                    except Exception:
                        pass
                    self.current_line_count += 1
        except Exception as e:
            print(f"首次读取配置文件失败: {e}")

    def on_config_file_changed(self, path):
        # 外部 shittim 写入完成后触发读取
        QTimer.singleShot(50, self.read_new_lines)

    def read_new_lines(self):
        if not os.path.exists(CONFIG_FILE_PATH):
            return
        
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                if len(lines) > self.current_line_count:
                    # 移除临时等待气泡
                    if self.loading_widget:
                        self.messages_layout.removeWidget(self.loading_widget)
                        self.loading_widget.deleteLater()
                        self.loading_widget = None

                    new_lines = lines[self.current_line_count:]
                    
                    # 追溯历史中最近的一次 user 时间（防止切片断层）
                    last_user_time = ""
                    for i in range(min(len(lines), self.current_line_count)):
                        try:
                            prev_data = json.loads(lines[i].strip())
                            if prev_data.get("role") == "user":
                                last_user_time = prev_data.get("time", "")
                        except Exception:
                            pass

                    # 增量处理新行
                    for line in new_lines:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line.strip())
                            role = data.get("role")
                            content = data.get("content", "").strip()
                            
                            if role == "user":
                                last_user_time = data.get("time", "")
                                sender = "Me"
                            else:
                                sender = "Robot"
                                
                            # 强制让 plana 的时间与那一次的 user 时间完全保持一致
                            display_time = self.format_smart_datetime(last_user_time)
                            self.append_message_to_display(sender, content, display_time, auto_scroll=True)
                        except Exception:
                            pass
                    
                    self.current_line_count = len(lines)
        except Exception as e:
            print(f"增量读取新消息失败: {e}")

    def append_message_to_display(self, sender, content, timestamp, auto_scroll=True, is_loading=False, is_error=False):
        avatar = self.avatar_me if sender == "Me" else self.avatar_robot
        # 【修改】透传 is_error 参数
        message_widget = MessageWidget(sender, content, timestamp, avatar, is_loading, is_error)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)

        if is_loading:
            self.loading_widget = message_widget

        if auto_scroll:
            QApplication.processEvents()
            self.scroll_to_bottom()
    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        # =================【关键修改：生成临时反馈气泡】=================
        # 不直接生成永久的“Me”气泡。而是生成一个临时的“思考中”提示气泡，提供即时回车反馈
        timestamp_show = datetime.now().strftime('%H:%M')
        self.append_message_to_display("Me", f"{text}  (正在传输...)", timestamp_show, auto_scroll=True, is_loading=True)
        # =========================================================

        # 禁止再次输入
        self.input_field.setDisabled(True)
        self.send_button.setDisabled(True)
        self.input_field.setPlaceholderText("普拉娜正在认真思考中...")
        self.input_field.clear()

        # 异步调用外部命令
        self.runner_thread = CommandRunnerThread(text)
        self.runner_thread.finished_signal.connect(self.on_command_finished)
        self.runner_thread.start()

    def on_command_finished(self, return_code):
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setPlaceholderText("想对普拉娜说点什么...")
        self.input_field.setFocus()

        # 【核心新增】：如果外部进程返回了 1 
        if return_code == 1:
            # 1. 立即销毁正在传输的临时灰色气泡
            if self.loading_widget:
                self.messages_layout.removeWidget(self.loading_widget)
                self.loading_widget.deleteLater()
                self.loading_widget = None
            
            # 2. 强行同步一次历史文件（万一 shittim 在死掉前写了部分信息）
            self.read_new_lines()
            
            # 3. 在界面渲染红色的错误提示
            timestamp_show = datetime.now().strftime('%H:%M')
            self.append_message_to_display(
                sender="Robot", 
                content="[系统提示] ⚠️ API 调用失败，请检查网络或配置。", 
                timestamp=timestamp_show, 
                auto_scroll=True, 
                is_error=True
            )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("sans-serif")
    app.setFont(font)
    chat = ChatWindow()
    chat.show()
    sys.exit(app.exec())