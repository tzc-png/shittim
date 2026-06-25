import sys
import os
# os.environ["G_DEBUG"] = "fatal-warnings"  # 只显示致命错误
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QLineEdit, QPushButton, QLabel,
                             QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl, QFileSystemWatcher, QThread, pyqtSignal, QEvent
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
# AVATAR_ROBOT_PATH = os.path.join(current_dir, "plana.png")    # 对方（普拉娜酱）的头像路径
EMOTIONS_DIR = os.path.join(current_dir, "plana_emotions")

LIVE_VIDEO_PATH = os.path.join(current_dir, "plana.webm") # 侧边动态立绘视频路径

# 外部命令配置
COMMAND_NAME = "shittim"           # 调用的主命令
COMMAND_ROLE = "plana"             # 调用的角色参数

# 窗口的标题
WINDOW_TITLE = "plana"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
LIVE_ZONE_WIDTH = 350

# 历史记录分批加载配置
HISTORY_INIT_COUNT = 6    # 初始加载的历史消息条数
HISTORY_BATCH_COUNT = 12   # 每次向上滚动拉顶时，额外加载的历史消息条数

# 【新增】全局头像大小配置（单位：像素）
AVATAR_SIZE = 65
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
        # 【修改】使用全局尺寸，头像框会自动等比例放大
        avatar_label.setFixedSize(QSize(AVATAR_SIZE, AVATAR_SIZE))
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
        self.avatar_me = get_round_avatar(AVATAR_ME_PATH, size=AVATAR_SIZE)    
        # self.avatar_robot = get_round_avatar(AVATAR_ROBOT_PATH)
        self.robot_avatar_cache = {} 
        
        self.current_line_count = 0
        self.loading_widget = None # 用来保存临时的等待状态气泡控件
        
        self.init_ui()

        self.all_history_lines = []   # 内存缓存：存放 jsonl 文件的所有行文本
        self.history_start_ptr = 0    # 指针：记录当前已经加载到界面的最顶端消息在列表中的索引
        self.is_loading_more = False  # 是否正在加载历史的锁
        self.old_max = 0              # 记录加载前的旧滚动条最大值

        # 【核心：绑定滚动条信号】
        # 1. 监听滚动位置，滑到顶(0)时好触发加载
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll_value_changed)
        # 2. 监听范围变化，加载完新控件后好精准把滚动条推回原位
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self.on_scroll_range_changed)
        # 【监听鼠标拖拽松开信号】为了解决拖拽跳屏问题
        self.scroll_area.verticalScrollBar().sliderReleased.connect(self.on_slider_released)
        # 【安装事件过滤器】为了解决消息太少时滚轮和键盘失效的问题
        self.scroll_area.installEventFilter(self)
        self.scroll_area.viewport().installEventFilter(self)

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

    def get_robot_avatar(self, emotion):
        """动态获取机器人头像，带缓存机制与静默回退逻辑"""
        if not emotion:
            emotion = "default"
            
        if emotion not in self.robot_avatar_cache:
            # 如果缓存里没有，就去硬盘找
            emotion_path = os.path.join(EMOTIONS_DIR, f"{emotion}.png")
            # 如果对应情感的文件不存在，静默回退到 default.png
            if not os.path.exists(emotion_path):
                emotion_path = os.path.join(EMOTIONS_DIR, "default.png")
                
            self.robot_avatar_cache[emotion] = get_round_avatar(emotion_path, size=AVATAR_SIZE)
            
        return self.robot_avatar_cache[emotion]

    def format_smart_datetime(self, raw_time_str):
        """将 2026-06-25 11:22:07 转换为 '今天 11:22:07' 或 '2026-06-25 11:22:07'"""
        now = datetime.now()
        
        if not raw_time_str:
            return now.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 1. 尝试按照标准格式解析（保留秒数）
            dt = datetime.strptime(raw_time_str.strip(), "%Y-%m-%d %H:%M:%S")
            
            # 2. 判断解析出来的日期是否与今天的日期一致
            if dt.date() == now.date():
                return f"今天 {dt.strftime('%H:%M:%S')}"
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
                
        except ValueError:
            # 如果格式特殊或不匹配，原样返回防崩溃
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
        
        try:
            # 1. 一次性把非空行全部读入内存列表缓存
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                self.all_history_lines = [line for line in f if line.strip()]
            
            self.current_line_count = len(self.all_history_lines)
            
            # 2. 计算初始加载的起点指针（比如总共100条，初始加载最后20条，起点就是80）
            self.history_start_ptr = max(0, self.current_line_count - HISTORY_INIT_COUNT)
            
            # 3. 仅正序渲染这最后的初始条数
            for i in range(self.history_start_ptr, self.current_line_count):
                line = self.all_history_lines[i]
                try:
                    data = json.loads(line.strip())
                    role = data.get("role")
                    content = data.get("content", "").strip()
                    raw_time = data.get("time", "")
                    emotion = data.get("emotion", "default") # 【新增】：获取情感字段，默认 fallback 为 "default"
                    
                    sender = "Me" if role == "user" else "Robot"
                    display_time = self.format_smart_datetime(raw_time)
                    self.append_message_to_display(sender, content, display_time,emotion=emotion, auto_scroll=False)
                except Exception:
                    pass
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
                    
                    # 增量处理新行：直接解析每行，再无耦合
                    for line in new_lines:
                        if not line.strip():
                            continue

                        self.all_history_lines.append(line) # 将实时产生的新行也同步塞入内存列表尾部

                        try:
                            data = json.loads(line.strip())
                            role = data.get("role")
                            content = data.get("content", "").strip()
                            raw_time = data.get("time", "") # 直接取当前行的时间
                            emotion = data.get("emotion", "default")
                            
                            sender = "Me" if role == "user" else "Robot"
                            display_time = self.format_smart_datetime(raw_time)
                            
                            self.append_message_to_display(sender, content, display_time,emotion=emotion, auto_scroll=True)
                        except Exception:
                            pass
                    
                    self.current_line_count = len(lines)
        except Exception as e:
            print(f"增量读取新消息失败: {e}")

    # 【修改】：参数增加 emotion 参数，默认为 "default"
    def append_message_to_display(self, sender, content, timestamp, emotion="default", auto_scroll=True, is_loading=False, is_error=False):
        # 【修改】：动态获取头像
        avatar = self.avatar_me if sender == "Me" else self.get_robot_avatar(emotion)
        
        message_widget = MessageWidget(sender, content, timestamp, avatar, is_loading, is_error)
        self.messages_layout.addWidget(message_widget)

        if is_loading:
            self.loading_widget = message_widget

        if auto_scroll:
            QApplication.processEvents()
            self.scroll_to_bottom()

    # 【修改】：同样增加 emotion 参数
    def prepend_message_to_display(self, sender, content, timestamp, emotion="default"):
        """专门负责向聊天布局的最顶部（Index 1，留在弹簧下方）插入老历史气泡"""
        # 【修改】：动态获取头像
        avatar = self.avatar_me if sender == "Me" else self.get_robot_avatar(emotion)
        
        message_widget = MessageWidget(sender, content, timestamp, avatar, is_loading=False, is_error=False)
        self.messages_layout.insertWidget(1, message_widget)

    def on_scroll_value_changed(self, value):
        """当滚动条滑块滑到最顶部（value == 0）时，触发向前加载历史"""
        if value == 0 and not getattr(self, 'is_loading_more', False):
            # 【防跳跃核心】：如果用户当前正用鼠标按住滑块拖拽，绝对不能立刻加载！
            # 否则代码把滑块往下推，但物理鼠标还在顶部，鼠标一动就会立刻产生巨大跳屏。
            if self.scroll_area.verticalScrollBar().isSliderDown():
                return 
            self.load_more_history()

    def eventFilter(self, obj, event):
        """底层事件拦截：处理消息过少时，滚轮和键盘无法触发滚动条信号的问题"""
        # 拦截鼠标滚轮
        if event.type() == QEvent.Type.Wheel:
            if event.angleDelta().y() > 0:  # 滚轮向上滚
                if self.scroll_area.verticalScrollBar().value() == 0 and not getattr(self, 'is_loading_more', False):
                    self.load_more_history()

        # 拦截键盘向上键 / PageUp
        elif event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
                if self.scroll_area.verticalScrollBar().value() == 0 and not getattr(self, 'is_loading_more', False):
                    self.load_more_history()
                    
        return super().eventFilter(obj, event)

    def on_slider_released(self):
        """当用户松开鼠标拖拽滑块时，检查是否停在最顶部，是则加载"""
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar.value() == 0 and not getattr(self, 'is_loading_more', False):
            self.load_more_history()

    def load_more_history(self):
        """向前加载更多历史（仅负责插入气泡与记录边界）"""
        if self.history_start_ptr <= 0:
            return  # 已经加载到最顶头了
        
        scrollbar = self.scroll_area.verticalScrollBar()
        
        # 1. 锁定状态，记录插入前的旧最大滚动范围，并临时屏蔽信号
        self.is_loading_more = True
        self.old_max = scrollbar.maximum()
        scrollbar.blockSignals(True)
        
        # 计算向前多加载后的新起点
        new_start = max(0, self.history_start_ptr - HISTORY_BATCH_COUNT)
        
        # 倒序将老气泡正序 prepend 插入最顶部
        for i in range(self.history_start_ptr - 1, new_start - 1, -1):
            line = self.all_history_lines[i]
            try:
                data = json.loads(line.strip())
                role = data.get("role")
                content = data.get("content", "").strip()
                raw_time = data.get("time", "")
                emotion = data.get("emotion", "default") # 【新增】：获取情感字段，默认 fallback 为 "default"
                
                sender = "Me" if role == "user" else "Robot"
                display_time = self.format_smart_datetime(raw_time)
                self.prepend_message_to_display(sender, content, display_time,emotion=emotion)
            except Exception:
                pass
        
        self.history_start_ptr = new_start
        
        # 2. 气泡塞完了，解除滚动条屏蔽
        scrollbar.blockSignals(False)
        
        # 3. 强制触发 Qt 重新计算内容容器大小，这会立刻激活下面的 rangeChanged 信号
        self.scroll_area.widget().adjustSize()

    def on_scroll_range_changed(self, min_val, max_val):
        """当滚动条范围发生改变时（说明新气泡高度已被 Qt 适配），精准推回原位"""
        if getattr(self, 'is_loading_more', False):
            # max_val 是加载完新气泡后的新最大滚动值
            # 新最大值减去旧最大值，刚好等于新插入的这批老气泡占用的绝对像素高度！
            delta = max_val - self.old_max
            
            # 直接将滚动条往下推对应的像素距离，刚才看的那条消息就会死死钉在屏幕最顶端
            self.scroll_area.verticalScrollBar().setValue(delta)
            
            # 解锁，完成本次加载循环
            self.is_loading_more = False

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        # =================【关键修改：生成临时反馈气泡】=================
        # 生成带秒数且支持“今天”前缀的本地过渡时间
        timestamp_show = self.format_smart_datetime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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