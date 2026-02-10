import os
import sys
import subprocess
import threading
from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# ================= 1. 字体配置 (解决乱码) =================
# 注册我们在 build.yml 里下载的字体
try:
    LabelBase.register(name='CustomFont', fn_regular='font.ttf')
    FONT_NAME = 'CustomFont'
except:
    FONT_NAME = 'Roboto' # 如果字体下载失败，回退到默认

# ================= 2. 颜色配置 (高仿 Web 版) =================
Window.clearcolor = (0.08, 0.1, 0.12, 1)  # 背景色：深蓝黑
COLOR_BTN_READ = (0.2, 0.6, 1, 1)         # 按钮：亮蓝
COLOR_BTN_WRITE = (0.8, 0.2, 0.2, 1)      # 按钮：深红
COLOR_INPUT_BG = (0.15, 0.18, 0.22, 1)    # 输入框背景：稍亮一点的黑

# ================= 3. 界面代码 =================

class EdlToolApp(App):
    def build(self):
        self.loader_path = ""
        
        # 主容器：垂直布局
        root = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # --- 标题栏 ---
        root.add_widget(Label(text="🛠️ 9008 Termux Pro", size_hint=(1, 0.08), 
                              font_size='22sp', bold=True, font_name=FONT_NAME, color=(1,1,1,1)))

        # --- 第一块：Loader 选择 ---
        loader_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=10)
        btn_loader = Button(text="📂 选择引导 (Loader)", size_hint=(0.35, 1), 
                            background_color=(0.2, 0.2, 0.2, 1), font_name=FONT_NAME)
        btn_loader.bind(on_press=self.show_loader_chooser)
        self.input_loader = TextInput(text="默认: 765g.elf", readonly=True, size_hint=(0.65, 1), 
                                      background_color=COLOR_INPUT_BG, foreground_color=(1,1,1,1), font_name=FONT_NAME)
        loader_box.add_widget(btn_loader)
        loader_box.add_widget(self.input_loader)
        root.add_widget(loader_box)

        # --- 第二块：读取分区 (模仿图二的蓝色条) ---
        root.add_widget(Label(text="选择分区 (Partition):", size_hint=(1, 0.05), halign='left', text_size=(Window.width, None), font_name=FONT_NAME))
        self.input_part = TextInput(hint_text="例如: boot", multiline=False, size_hint=(1, 0.08), 
                                    background_color=COLOR_INPUT_BG, foreground_color=(1,1,1,1), font_name=FONT_NAME)
        root.add_widget(self.input_part)
        
        # 蓝色长条按钮
        btn_read = Button(text="📥 备份 / 读取 (Read)", size_hint=(1, 0.08), 
                          background_color=COLOR_BTN_READ, background_normal='', font_name=FONT_NAME, bold=True)
        btn_read.bind(on_press=lambda x: self.do_task('read'))
        root.add_widget(btn_read)

        # --- 第三块：写入文件 (模仿图二的红色条) ---
        root.add_widget(Label(text="输入文件名 (输出/输入):", size_hint=(1, 0.05), halign='left', text_size=(Window.width, None), font_name=FONT_NAME))
        self.input_file = TextInput(hint_text="例如: boot.img", multiline=False, size_hint=(1, 0.08), 
                                    background_color=COLOR_INPUT_BG, foreground_color=(1,1,1,1), font_name=FONT_NAME)
        root.add_widget(self.input_file)
        
        # 红色长条按钮
        btn_write = Button(text="📤 写入 / 刷入 (Write)", size_hint=(1, 0.08), 
                           background_color=COLOR_BTN_WRITE, background_normal='', font_name=FONT_NAME, bold=True)
        btn_write.bind(on_press=lambda x: self.do_task('write'))
        root.add_widget(btn_write)

        # --- 第四块：黑色日志窗口 ---
        root.add_widget(Label(text="运行日志 (Log):", size_hint=(1, 0.05), halign='left', text_size=(Window.width, None), font_name=FONT_NAME))
        self.log_box = TextInput(readonly=True, background_color=(0, 0, 0, 1), 
                                 foreground_color=(0, 1, 0, 1), size_hint=(1, 0.35), font_name=FONT_NAME, font_size='12sp')
        root.add_widget(self.log_box)

        return root

    # ================= 4. 逻辑功能 (保持不变) =================

    def log(self, text):
        Clock.schedule_once(lambda dt: self._update_log(text))

    def _update_log(self, text):
        self.log_box.text += text + "\n"

    def show_loader_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        initial_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edl', 'firehose')
        if not os.path.exists(initial_path): initial_path = "/"
        filechooser = FileChooserIconView(path=initial_path, filters=['*.elf', '*.bin', '*.mbn'])
        btn_layout = BoxLayout(size_hint_y=0.1)
        btn_select = Button(text="确定", on_release=lambda x: self.select_loader(filechooser.selection, popup), font_name=FONT_NAME)
        btn_cancel = Button(text="取消", on_release=lambda x: popup.dismiss(), font_name=FONT_NAME)
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        popup = Popup(title="选择 Loader", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def select_loader(self, selection, popup):
        if selection:
            self.loader_path = selection[0]
            self.input_loader.text = os.path.basename(self.loader_path)
        popup.dismiss()

    def find_su_binary(self):
        possible_paths = ["/system/bin/su", "/system/xbin/su", "/data/adb/ksu/bin/su", "/data/adb/ap/bin/su", "/sbin/su", "/bin/su"]
        for path in possible_paths:
            if os.path.exists(path): return path
        return "su" 

    def do_task(self, mode):
        part = self.input_part.text.strip()
        filename = self.input_file.text.strip()
        threading.Thread(target=self.run_edl, args=(mode, part, filename)).start()

    def run_edl(self, mode, part, filename):
        app_dir = os.path.dirname(os.path.abspath(__file__))
        loader = self.loader_path if self.loader_path else os.path.join(app_dir, "edl/firehose/765g.elf")
        
        if not filename: 
            # 智能补全文件名
            if mode == 'read': filename = f"{part}.img" if part else "dump.img"
            if mode == 'write': return self.log("❌ 写入模式必须指定文件名！")

        if not filename.startswith("/"): file_path = os.path.join(app_dir, filename)
        else: file_path = filename

        base_cmd = f"-m edl --loader={loader} --memory=ufs --lun=4"
        
        if mode == 'read':
            if not part: return self.log("❌ 请填写分区名")
            self.log(f"🔵 准备读取: {part} -> {file_path}")
            action_cmd = f"r {part} {file_path}"
        elif mode == 'write':
            if not part: return self.log("❌ 请填写分区名")
            self.log(f"🔴 警告：正在写入: {file_path} -> {part}")
            action_cmd = f"w {part} {file_path}"
        
        su_path = self.find_su_binary()
        python_bin = sys.executable
        current_env = os.environ.copy()
        
        full_cmd = (
            f"{su_path} -c '"
            f"export PYTHONPATH={current_env.get('PYTHONPATH', '')}:{app_dir} && "
            f"export LD_LIBRARY_PATH={current_env.get('LD_LIBRARY_PATH', '')} && "
            f"cd {app_dir} && "
            f"{python_bin} {base_cmd} {action_cmd}"
            f"'"
        )

        try:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                line = process.stdout.readline()
                if not line: break
                self.log(line.decode('utf-8', errors='ignore').strip())
            process.wait()
            if process.returncode == 0: self.log("✅ 操作成功！")
            else: self.log("❌ 操作失败 (检查授权或连接)")
        except Exception as e:
            self.log(f"💥 错误: {e}")

if __name__ == '__main__':
    EdlToolApp().run()
            "/system/bin/su",
            "/system/xbin/su",
            "/data/adb/ksu/bin/su",  # KernelSU 专用路径
            "/data/adb/ap/bin/su",   # APatch 专用路径
            "/sbin/su",
            "/bin/su"
        ]
        # 即使没授权，KernelSU 的专用路径有时也是存在的，只是没权限执行
        # 所以我们优先检测标准路径
        for path in possible_paths:
            if os.path.exists(path):
                return path
        # 如果都找不到，大概率是没授权，导致文件不可见，但我们还是返回 'su' 碰运气
        return "su" 

    def do_task(self, instance):
        mode = self.spinner_mode.text
        part = self.input_part.text.strip()
        filename = self.input_file.text.strip()
        threading.Thread(target=self.run_edl, args=(mode, part, filename)).start()

    def run_edl(self, mode, part, filename):
        app_dir = os.path.dirname(os.path.abspath(__file__))
        loader = self.loader_path if self.loader_path else os.path.join(app_dir, DEFAULT_LOADER)
        
        # 路径处理
        if not filename.startswith("/"):
            file_path = os.path.join(app_dir, filename)
        else:
            file_path = filename

        # 基础命令
        # 强制使用 --sectorsize=4096 (或者你可以根据需要去掉)
        base_cmd = f"-m edl --loader={loader} --memory=ufs --lun=4"
        
        if 'GPT' in mode:
            action_cmd = "printgpt"
        elif '读取' in mode:
            if not part: return self.log("❌ 缺分区名")
            action_cmd = f"r {part} {file_path}"
        elif '写入' in mode:
            if not part: return self.log("❌ 缺分区名")
            action_cmd = f"w {part} {file_path}"
        elif 'XML' in mode:
            action_cmd = f"printgpt --xml {file_path}"
        else:
            return self.log("❌ 请选择模式")

        # 获取 su 路径
        su_path = self.find_su_binary()
        python_bin = sys.executable
        current_env = os.environ.copy()
        
        # 拼接命令
        full_cmd = (
            f"{su_path} -c '"
            f"export PYTHONPATH={current_env.get('PYTHONPATH', '')}:{app_dir} && "
            f"export LD_LIBRARY_PATH={current_env.get('LD_LIBRARY_PATH', '')} && "
            f"cd {app_dir} && "
            f"{python_bin} {base_cmd} {action_cmd}"
            f"'"
        )

        self.log(f"尝试 Root 路径: {su_path}")
        self.log(f"执行中...")

        try:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                line = process.stdout.readline()
                if not line: break
                self.log(line.decode('utf-8', errors='ignore').strip())
            process.wait()
            if process.returncode == 0:
                self.log("✅ 成功！")
            else:
                self.log("❌ 失败！(如果你看到 inaccessible，请去 KernelSU APP 授权)")
        except Exception as e:
            self.log(f"💥 错误: {e}")

if __name__ == '__main__':
    EdlToolApp().run()
