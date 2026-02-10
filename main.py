import os
import sys
import subprocess
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock

# =================配置区域=================
DEFAULT_LOADER = "edl/firehose/765g.elf"
# =========================================

class EdlToolApp(App):
    def build(self):
        self.loader_path = "" 
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        main_layout.add_widget(Label(text="🔥 9008 Tool (KernelSU 适配版)", size_hint=(1, 0.05), font_size='18sp', bold=True))

        # Loader 选择
        loader_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=5)
        self.btn_loader = Button(text="📂 选择引导 (Loader)", size_hint=(0.4, 1), background_color=(0, 0.5, 0.8, 1))
        self.btn_loader.bind(on_press=self.show_loader_chooser)
        self.lbl_loader = TextInput(text="默认: 765g.elf", readonly=True, size_hint=(0.6, 1))
        loader_layout.add_widget(self.btn_loader)
        loader_layout.add_widget(self.lbl_loader)
        main_layout.add_widget(loader_layout)

        # 功能选择
        self.spinner_mode = Spinner(
            text='🔍 选择功能模式',
            values=('打印分区表 (Print GPT)', '读取分区 (Read)', '写入分区 (Write)', '生成 RawProgram XML'),
            size_hint=(1, 0.08),
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.spinner_mode.bind(text=self.on_mode_select)
        main_layout.add_widget(self.spinner_mode)

        # 参数输入
        params_layout = GridLayout(cols=2, size_hint=(1, 0.15), spacing=5)
        params_layout.add_widget(Label(text="分区名:"))
        self.input_part = TextInput(multiline=False, hint_text="如 boot (仅读写模式)")
        params_layout.add_widget(self.input_part)
        params_layout.add_widget(Label(text="文件名:"))
        self.input_file = TextInput(multiline=False, hint_text="如 boot.img")
        params_layout.add_widget(self.input_file)
        main_layout.add_widget(params_layout)

        # 日志
        self.log_box = TextInput(readonly=True, background_color=(0.05, 0.05, 0.05, 1), 
                                 foreground_color=(0, 1, 0, 1), size_hint=(1, 0.5))
        main_layout.add_widget(self.log_box)

        # 按钮
        self.btn_run = Button(text="🚀 执行 (需在管理器授权)", size_hint=(1, 0.12), background_color=(0.8, 0, 0, 1))
        self.btn_run.bind(on_press=self.do_task)
        main_layout.add_widget(self.btn_run)

        return main_layout

    def on_mode_select(self, spinner, text):
        if 'GPT' in text:
            self.input_part.disabled = True
            self.input_file.text = ""
        elif 'XML' in text:
            self.input_part.disabled = True
            self.input_file.text = "rawprogram.xml"
        else:
            self.input_part.disabled = False
            self.input_file.text = "boot.img"

    def show_loader_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        initial_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edl', 'firehose')
        if not os.path.exists(initial_path): initial_path = "/"
        
        filechooser = FileChooserIconView(path=initial_path, filters=['*.elf', '*.bin', '*.mbn'])
        btn_layout = BoxLayout(size_hint_y=0.1)
        btn_select = Button(text="确定", on_release=lambda x: self.select_loader(filechooser.selection, popup))
        btn_cancel = Button(text="取消", on_release=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        popup = Popup(title="选择 Loader", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def select_loader(self, selection, popup):
        if selection:
            self.loader_path = selection[0]
            self.lbl_loader.text = os.path.basename(self.loader_path)
        popup.dismiss()

    def log(self, text):
        Clock.schedule_once(lambda dt: self._update_log(text))

    def _update_log(self, text):
        self.log_box.text += text + "\n"

    def find_su_binary(self):
        # 🔥 专为 KernelSU / Kitsune / APatch 优化的路径寻找
        possible_paths = [
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
