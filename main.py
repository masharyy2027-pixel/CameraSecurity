# Camera Security System - Android port
# Original desktop features preserved and adapted to Android APIs.
import os, time, threading
from datetime import datetime

import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.utils import platform
from camera4kivy import Preview

APP_TITLE = 'Camera Security System'
DEFAULT_PASSWORD = '11227788'


def app_file(name):
    return os.path.join(os.path.dirname(__file__), name)


class SecurityPreview(Preview):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.processed_texture = None
        self._lock = threading.Lock()

    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):
        try:
            rgba = np.frombuffer(pixels, dtype=np.uint8).reshape(image_size[1], image_size[0], 4).copy()
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            faces = self.app.face_cascade.detectMultiScale(gray, scaleFactor=1.4, minNeighbors=4, minSize=(35, 35))

            mode = self.app.current_filter
            if mode == 'Gray':
                shown = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            elif mode == 'Sketch':
                inv = 255 - gray
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                sketch = cv2.divide(gray, 255 - blur, scale=256)
                shown = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
            else:
                shown = bgr.copy()

            for (x, y, w, h) in faces:
                cv2.rectangle(shown, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(shown, 'Enemy', (x, max(22, y-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

            out = cv2.cvtColor(shown, cv2.COLOR_BGR2RGBA)
            self.app.on_faces_detected(len(faces), bgr)
            self._update_processed_texture(out, image_size)
        except Exception as exc:
            print('Frame processing error:', exc)

    @mainthread
    def _update_processed_texture(self, rgba, size):
        if not self.camera_connected:
            return
        if (self.processed_texture is None or self.processed_texture.size != size):
            self.processed_texture = Texture.create(size=size, colorfmt='rgba')
            self.processed_texture.flip_vertical()
        self.processed_texture.blit_buffer(rgba.tobytes(), colorfmt='rgba')
        self.canvas.ask_update()

    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        if self.processed_texture:
            Color(1, 1, 1, 1)
            Rectangle(texture=self.processed_texture, size=tex_size, pos=tex_pos)


class CameraSecurityApp(App):
    def build(self):
        self.title = APP_TITLE
        self.user_data = self.user_data_dir
        os.makedirs(self.user_data, exist_ok=True)
        self.gallery_path = os.path.join(self.user_data, 'Gallery')
        os.makedirs(self.gallery_path, exist_ok=True)
        self.pass_file = os.path.join(self.user_data, 'camera_pass.txt')
        self.password = self.load_password()
        self.security_mode = False
        self.current_filter = 'Normal'
        self.countdown = 0
        self.last_frame = None
        self.last_alert_time = 0
        self.face_count = 0
        self._frame_lock = threading.Lock()
        self.face_cascade = cv2.CascadeClassifier(app_file('haarcascade_frontalface_default.xml'))
        self.alarm = SoundLoader.load(app_file('alarm.mp3'))
        self.root_layout = BoxLayout(orientation='vertical', padding=12, spacing=8)
        self.show_login()
        return self.root_layout

    def load_password(self):
        try:
            if os.path.exists(self.pass_file):
                with open(self.pass_file, 'r', encoding='utf-8') as f:
                    return f.read().strip() or DEFAULT_PASSWORD
        except Exception:
            pass
        return DEFAULT_PASSWORD

    def clear_root(self):
        self.root_layout.clear_widgets()

    def make_button(self, text, callback, color=(0.10, 0.35, 0.58, 1), height=48):
        btn = Button(text=text, size_hint_y=None, height=height, background_normal='', background_color=color,
                     color=(1, 1, 1, 1), font_size='15sp')
        btn.bind(on_release=lambda *_: callback())
        return btn

    def show_login(self):
        self.clear_root()
        self.root_layout.add_widget(Image(source=app_file('icon.png'), size_hint=(1, None), height=190, allow_stretch=True, keep_ratio=True))
        self.root_layout.add_widget(Label(text='🛡️ Camera Security\nنظام الكاميرا الأمنية', font_size='23sp', size_hint_y=None, height=78))
        self.root_layout.add_widget(Label(text='Enter Password / أدخل كلمة المرور', size_hint_y=None, height=38))
        self.password_input = TextInput(password=True, multiline=False, hint_text='Password', size_hint_y=None, height=50)
        self.root_layout.add_widget(self.password_input)
        self.root_layout.add_widget(Label(text=f'Hint: {self.password[:2]}..{self.password[-2:]}', color=(0.65,0.65,0.65,1), size_hint_y=None, height=30))
        self.root_layout.add_widget(self.make_button('Login / دخول', self.check_password))
        self.root_layout.add_widget(self.make_button('About / حول', self.show_about, (0.35,0.35,0.4,1)))

    def check_password(self):
        if self.password_input.text == self.password:
            self.show_main()
        else:
            self.message('Wrong Password / كلمة مرور خاطئة')

    def show_main(self):
        self.clear_root()
        self.root_layout.add_widget(Label(text='🛡️ نظام الكاميرا الأمنية | Security Camera System', size_hint_y=None, height=48, font_size='17sp'))
        self.preview = SecurityPreview(self, aspect_ratio='4:3', size_hint=(1, 1))
        self.root_layout.add_widget(self.preview)
        self.status = Label(text='Security: OFF | الحماية: مطفأة', size_hint_y=None, height=32, color=(1,0.4,0.4,1))
        self.root_layout.add_widget(self.status)
        row1 = BoxLayout(size_hint_y=None, height=48, spacing=6)
        row1.add_widget(self.make_button('Capture / تصوير', self.start_countdown, (0.08,0.42,0.62,1)))
        row1.add_widget(self.make_button('Security OFF', self.toggle_security, (0.5,0.05,0.08,1)))
        self.security_button = row1.children[0]
        # children are inserted in reverse order; retain the security button explicitly
        self.security_button = row1.children[0]
        self.root_layout.add_widget(row1)
        row2 = BoxLayout(size_hint_y=None, height=48, spacing=6)
        self.filter_spinner = Spinner(text='Normal', values=('Normal','Gray','Sketch'), size_hint_x=1)
        self.filter_spinner.bind(text=self.change_filter)
        row2.add_widget(self.filter_spinner)
        row2.add_widget(self.make_button('Gallery / المعرض', self.show_gallery, (0.28,0.3,0.36,1)))
        row2.add_widget(self.make_button('New Password', self.change_password, (0.28,0.3,0.36,1)))
        self.root_layout.add_widget(row2)
        row3 = BoxLayout(size_hint_y=None, height=44)
        row3.add_widget(self.make_button('About / حول', self.show_about, (0.28,0.3,0.36,1)))
        self.root_layout.add_widget(row3)
        Clock.schedule_once(self.connect_camera, 0.7)

    def connect_camera(self, *_):
        try:
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.CAMERA], lambda perms, grants: self._camera_permission_result(grants))
            else:
                self.preview.connect_camera(enable_analyze_pixels=True, analyze_pixels_resolution=640, enable_video=False)
        except Exception as exc:
            self.message('Camera error: ' + str(exc))

    def _camera_permission_result(self, grants):
        if grants and all(grants):
            Clock.schedule_once(lambda dt: self.preview.connect_camera(enable_analyze_pixels=True, analyze_pixels_resolution=640, enable_video=False), 0.4)
        else:
            self.message('Camera permission is required / يجب السماح للكاميرا')

    def on_faces_detected(self, count, frame):
        self.face_count = count
        with self._frame_lock:
            self.last_frame = frame.copy()
        if self.security_mode and count > 0:
            now = time.time()
            if now - self.last_alert_time >= 4.0:
                self.last_alert_time = now
                Clock.schedule_once(lambda dt: self.play_alarm(), 0)
                self.save_frame(frame, 'Alert')
        Clock.schedule_once(lambda dt: self.update_status(), 0)

    @mainthread
    def update_status(self):
        if hasattr(self, 'status'):
            state = 'ON / مفعل' if self.security_mode else 'OFF / مطفأ'
            self.status.text = f'Security: {state}   |   Faces: {self.face_count}'
            self.status.color = (0.25,1,0.35,1) if self.security_mode else (1,0.4,0.4,1)

    def play_alarm(self):
        try:
            if self.alarm and self.alarm.state != 'play':
                self.alarm.stop(); self.alarm.play()
        except Exception as exc:
            print('Alarm playback error:', exc)

    def toggle_security(self):
        self.security_mode = not self.security_mode
        if hasattr(self, 'security_button'):
            self.security_button.text = 'Security ON' if self.security_mode else 'Security OFF'
            self.security_button.background_color = (0.02,0.48,0.12,1) if self.security_mode else (0.5,0.05,0.08,1)
        self.update_status()

    def change_filter(self, _spinner, value):
        self.current_filter = value

    def start_countdown(self):
        self.countdown = 3
        self._countdown_event = Clock.schedule_interval(self.countdown_tick, 1)

    def countdown_tick(self, dt):
        if self.countdown > 0:
            if hasattr(self, 'status'):
                self.status.text = f'Capture in {self.countdown}...'
            self.countdown -= 1
        else:
            if hasattr(self, '_countdown_event'):
                self._countdown_event.cancel()
            with self._frame_lock:
                frame = self.last_frame.copy() if self.last_frame is not None else None
            if frame is not None:
                self.save_frame(frame, 'Manual')
                self.message('Photo saved / تم حفظ الصورة')
            else:
                self.message('Camera is not ready yet / الكاميرا غير جاهزة')
            self.update_status()
            return False
        return True

    def save_frame(self, frame, prefix):
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self.gallery_path, f'{prefix}_{stamp}.jpg')
        try:
            cv2.imwrite(path, frame)
        except Exception as exc:
            print('Save image error:', exc)

    def show_gallery(self):
        files = sorted([f for f in os.listdir(self.gallery_path) if f.lower().endswith(('.jpg','.png','.jpeg'))], reverse=True)
        content = BoxLayout(orientation='vertical', padding=8, spacing=6)
        if not files:
            content.add_widget(Label(text='No photos yet / لا توجد صور'))
        else:
            for name in files[:30]:
                content.add_widget(Label(text=name, size_hint_y=None, height=34))
        content.add_widget(self.make_button('Close / إغلاق', lambda: popup.dismiss()))
        popup = Popup(title='Gallery / المعرض', content=content, size_hint=(0.92,0.82))
        popup.open()

    def change_password(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        entry = TextInput(password=True, multiline=False, hint_text='New password', size_hint_y=None, height=48)
        box.add_widget(Label(text='Enter New Password / أدخل الرمز الجديد'))
        box.add_widget(entry)
        def save():
            value = entry.text.strip()
            if value:
                try:
                    with open(self.pass_file, 'w', encoding='utf-8') as f: f.write(value)
                    self.password = value
                    popup.dismiss(); self.message('Password updated / تم تغيير كلمة المرور')
                except Exception as exc:
                    self.message(str(exc))
        box.add_widget(self.make_button('Save / حفظ', save))
        popup = Popup(title='Change Password', content=box, size_hint=(0.9,0.42))
        popup.open()

    def show_about(self):
        content = BoxLayout(orientation='vertical', padding=12, spacing=8)
        content.add_widget(Label(text='🛡️ نظام الكاميرا الأمنية\nSecurity Camera System', font_size='20sp'))
        content.add_widget(Label(text='Auto Face Detection\nRed Enemy Tagging\nAudio Alarm System\nAdvanced Image Filters\nPassword Protection\nSmart Intruder Gallery\n\nDeveloper: Hussain Al-Bayati\nInstagram: @bgq_v'))
        content.add_widget(self.make_button('Instagram / فتح الحساب', lambda: self.open_instagram(), (0.78,0.12,0.35,1)))
        content.add_widget(self.make_button('Close / إغلاق', lambda: popup.dismiss()))
        popup = Popup(title='About / حول', content=content, size_hint=(0.92,0.82))
        popup.open()

    def open_instagram(self):
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent'); Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse('https://www.instagram.com/bgq_v/'))
            PythonActivity.mActivity.startActivity(intent)
        except Exception:
            import webbrowser; webbrowser.open('https://www.instagram.com/bgq_v/')

    def message(self, text):
        Popup(title='Camera Security', content=Label(text=text), size_hint=(0.85,0.28)).open()

    def on_pause(self):
        try: self.preview.disconnect_camera()
        except Exception: pass
        return True

    def on_resume(self):
        if hasattr(self, 'preview'):
            Clock.schedule_once(self.connect_camera, 0.5)

    def on_stop(self):
        try: self.preview.disconnect_camera()
        except Exception: pass
        try:
            if self.alarm: self.alarm.stop()
        except Exception: pass


if __name__ == '__main__':
    CameraSecurityApp().run()
