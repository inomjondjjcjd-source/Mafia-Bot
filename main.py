import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# Ekran o'lchamini telefonbop qilib sozlaymiz (Kompyuterda tekshirish uchun)
Window.size = (360, 640)

class AjdahoTapOyin(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # O'yin ma'lumotlarini yuklash yoki yaratish
        self.data_file = "game_save.json"
        self.load_data()

        # 🎨 FON RANGI (Chiroyli to'q yashil ferma foni)
        Window.clearcolor = get_color_from_hex('#1b4d3e')

        # 👑 SARLAVHA
        self.title_label = Label(
            text="🐉 AJDAHO FERMASI 🐉\n        (TAP TO EARN)",
            font_size='24sp',
            bold=True,
            color=get_color_from_hex('#f1c40f'),
            size_hint_y=0.15
        )
        self.add_widget(self.title_label)

        # 🪙 BALANS VA KO'RSATKICHLAR
        self.status_label = Label(
            text=f"🪙 Oltinlar: {self.gold}\n⚡️ Har bosishda: +{self.tap_power}",
            font_size='20sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.15
        )
        self.add_widget(self.status_label)

        # 👇 ASOSIY BOSISH TUGMASI (Katta va daxshatli sariq tugma)
        self.tap_button = Button(
            text="👇 BOSISH\n(OLTIN OLISH)",
            font_size='22sp',
            bold=True,
            background_normal='',
            background_color=get_color_from_hex('#f39c12'),
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.4
        )
        self.tap_button.bind(on_press=self.on_tap)
        self.add_widget(self.tap_button)

        # 🚀 KUCHAYTIRISH (UPGRADE) TUGMASI
        self.upgrade_price = 100 * self.tap_power
        self.upgrade_button = Button(
            text=f"🌱 YETISHTIRISH (Ko'paytirish)\nKeyingi LVL narxi: {self.upgrade_price} 🪙",
            font_size='14sp',
            bold=True,
            background_normal='',
            background_color=get_color_from_hex('#2980b9'),
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.15
        )
        self.upgrade_button.bind(on_press=self.on_upgrade)
        self.add_widget(self.upgrade_button)

        # 💾 SAQLASH TUGMASI
        self.save_button = Button(
            text="💾 O'yinni Saqlash",
            font_size='14sp',
            background_normal='',
            background_color=get_color_from_hex('#7f8c8d'),
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.1
        )
        self.save_button.bind(on_press=self.save_data)
        self.add_widget(self.save_button)

    def on_tap(self, instance):
        """Ekranga bosganda oltin qo'shish funksiyasi"""
        self.gold += self.tap_power
        self.update_ui()

    def on_upgrade(self, instance):
        """Tap kuchini sotib olib kuchaytirish"""
        if self.gold >= self.upgrade_price:
            self.gold -= self.upgrade_price
            self.tap_power += 1
            self.upgrade_price = 100 * self.tap_power
            self.update_ui()
            self.save_data_auto()
        else:
            self.upgrade_button.text = "❌ Oltin yetarli emas uka!"

    def update_ui(self):
        """Ekrandagi yozuvlarni yangilab turish"""
        self.status_label.text = f"🪙 Oltinlar: {self.gold}\n⚡️ Har bosishda: +{self.tap_power}"
        self.upgrade_button.text = f"🌱 YETISHTIRISH (Ko'paytirish)\nKeyingi LVL narxi: {self.upgrade_price} 🪙"

    def load_data(self):
        """Telefon xotirasidan saqlangan o'yinni yuklash"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.gold = data.get("gold", 0)
                    self.tap_power = data.get("tap_power", 1)
            except:
                self.gold = 0
                self.tap_power = 1
        else:
            self.gold = 0
            self.tap_power = 1

    def save_data(self, instance=None):
        """O'yinni qo'lda saqlash"""
        self.save_data_auto()
        if instance:
            instance.text = "✅ O'yin saqlandi!"

    def save_data_auto(self):
        """Avtomatik saqlash mexanizmi"""
        data = {"gold": self.gold, "tap_power": self.tap_power}
        with open(self.data_file, "w") as f:
            json.dump(data, f)

class O'yinApp(App):
    def build(self):
        self.title = "Ajdaho Fermasi (Tap to Earn)"
        return AjdahoTapOyin()

if __name__ == '__main__':
    O'yinApp().run()
      
