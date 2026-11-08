from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window


class CameraSecurityTest(App):

    def build(self):
        self.title = "Camera Security Test"

        layout = BoxLayout(
            orientation="vertical",
            padding=25,
            spacing=20
        )

        title = Label(
            text="Camera Security",
            font_size="28sp",
            bold=True
        )

        message = Label(
            text="Kivy is working!\nواجهة الاختبار تعمل بنجاح",
            font_size="20sp"
        )

        button = Button(
            text="Test Button",
            font_size="20sp",
            size_hint=(1, 0.25)
        )

        button.bind(
            on_press=lambda instance: setattr(
                message,
                "text",
                "Button works!\nالزر يعمل بنجاح"
            )
        )

        layout.add_widget(title)
        layout.add_widget(message)
        layout.add_widget(button)

        return layout


if __name__ == "__main__":
    CameraSecurityTest().run()
