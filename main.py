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
        
        self.label = Label(text="🔥 9008 Tool (Root Fix)", size_hint=(1, 0.1), font_size='20sp')
        self.layout.add_widget(self.label)

        self.log_box = TextInput(readonly=True, background_color=(0.1, 0.1, 0.1, 1), 
                                 foreground_color=(0, 1, 0, 1), size_hint=(1, 0.6))
        self.layout.add_widget(self.log_box)

        self.btn_read = Button(text="[ROOT] 读取 Boot", size_hint=(1, 0.15), background_color=(0, 0.5, 1, 1))
        self.btn_read.bind(on_press=self.do_read)
        self.layout.add_widget(self.btn_read)

        return self.layout

    def log(self, text):
        Clock.schedule_once(lambda dt: self._update_log(text))

    def _update_log(self, text):
        self.log_box.text += text + "\n"

    def do_read(self, instance):
        self.log("🚀 正在初始化 Root 环境...")
        threading.Thread(target=self.run_edl).start()

    def run_edl(self):
        # 1. 获取当前 APP 的路径
        app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. 准备关键路径
        # 直接使用 edl 文件夹作为模块，而不是找 script 文件
        # 注意：这里假设 edl 文件夹在 APK 解压后的根目录下
        loader_path = os.path.join(app_dir, 'edl', 'firehose', '765g.elf')
        output_path = os.path.join(app_dir, 'boot.img')

        # 3. 【核心修复】构建 Root 用户的 Python 环境
        # 获取当前 APP 的库路径 (LD_LIBRARY_PATH) 和 Python 路径
        current_env = os.environ.copy()
        lib_path = current_env.get('LD_LIBRARY_PATH', '')
        python_home = current_env.get('PYTHONHOME', '')
        python_path = current_env.get('PYTHONPATH', '') + f":{app_dir}" # 把 app 目录加入路径，以便找到 edl 模块
        
        # 获取 Python 解释器的绝对路径
        python_bin = sys.executable

        # 4. 拼接超级命令
        # 语法解释：
        # export ... -> 先给 Root 设置好环境变量
        # cd ... -> 进入 APP 目录
        # python -m edl -> 以模块方式启动 EDL，避开缺少启动脚本的问题
        cmd = (
            f"su -c '"
            f"export LD_LIBRARY_PATH={lib_path} && "
            f"export PYTHONHOME={python_home} && "
            f"export PYTHONPATH={python_path} && "
            f"cd {app_dir} && "
            f"{python_bin} -m edl r boot {output_path} --loader={loader_path} --memory=ufs --lun=4"
            f"'"
        )
        
        self.log(f"执行命令: {cmd}")
        
        try:
            # 执行命令
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            while True:
                line = process.stdout.readline()
                if not line: break
                self.log(line.decode('utf-8', errors='ignore').strip())
                
            process.wait()
            if process.returncode == 0:
                self.log(f"✅ 成功！文件已保存: {output_path}")
            else:
                self.log("❌ 失败，请检查上面的报错信息")
        except Exception as e:
            self.log(f"💥 异常: {e}")

if __name__ == '__main__':
    EdlToolApp().run()
