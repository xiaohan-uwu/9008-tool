import os
import sys
import subprocess
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform

class EdlToolApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        self.label = Label(text="🔥 9008 Tool (Root)", size_hint=(1, 0.1), font_size='20sp')
        self.layout.add_widget(self.label)

        # 日志窗口
        self.log_box = TextInput(readonly=True, background_color=(0.1, 0.1, 0.1, 1), 
                                 foreground_color=(0, 1, 0, 1), size_hint=(1, 0.6))
        self.layout.add_widget(self.log_box)

        # 按钮
        self.btn_read = Button(text="[ROOT] 读取 Boot", size_hint=(1, 0.15), background_color=(0, 0.5, 1, 1))
        self.btn_read.bind(on_press=self.do_read)
        self.layout.add_widget(self.btn_read)

        return self.layout

    def log(self, text):
        # 必须在主线程更新 UI
        Clock.schedule_once(lambda dt: self._update_log(text))

    def _update_log(self, text):
        self.log_box.text += text + "\n"

    def do_read(self, instance):
        self.log("🚀 正在请求 Root 权限启动...")
        # 在后台线程执行，防止界面卡死
        threading.Thread(target=self.run_edl).start()

    def run_edl(self):
        # 获取 APP 私有路径
        app_dir = os.path.dirname(os.path.abspath(__file__))
        edl_script = os.path.join(app_dir, 'edl', 'edl')
        loader = os.path.join(app_dir, 'edl', 'firehose', '765g.elf')
        output = os.path.join(app_dir, 'boot.img')

        # 核心：使用 su -c 调用 APK 内置的 python 去跑脚本
        # 注意：这里我们利用 APK 自己的环境
        cmd = f"su -c '{sys.executable} {edl_script} r boot {output} --loader={loader} --memory=ufs --lun=4'"
        
        self.log(f"执行: {cmd}")
        
        try:
            # 这里的 shell=True 在安卓上可能需要调整，视 Root 环境而定
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            while True:
                line = process.stdout.readline()
                if not line: break
                self.log(line.decode('utf-8', errors='ignore').strip())
                
            process.wait()
            if process.returncode == 0:
                self.log("✅ 成功！文件保存在: " + output)
            else:
                self.log("❌ 失败，请检查连接或 Root 授权")
        except Exception as e:
            self.log(f"💥 错误: {e}")

if __name__ == '__main__':
    EdlToolApp().run()
