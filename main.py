from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
import math

# ข้อมูลขีดจำกัดความปลอดภัย (PSI) 
EXPLOSIVE_DATA = {
    'C4': {'limit': 15000, 'hex_color': '#3498db'},
    'PETN': {'limit': 8000, 'hex_color': '#e74c3c'},
    'TNT': {'limit': 20000, 'hex_color': '#f1c40f'}
}

class BoosterSafetyApp(App):
    def build(self):
        # ตั้งค่าสีพื้นหลังของ App เป็นสีดำ
        Window.clearcolor = get_color_from_hex('#1a1a1a')
        self.title = "Booster Safety Monitor v2"
        self.selected_explosive = 'C4'

        # Main Layout (Vertical) พร้อม padding
        root = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # 1. ส่วนเลือกประเภทสาร (Label + Horizontal Layout for Buttons)
        root.add_widget(Label(text='เลือกประเภทสาร:', size_hint_y=None, height=dp(30), font_size='18sp', halign='left', valign='middle'))
        
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(5))
        
        # สร้าง ToggleButton สำหรับสารแต่ละชนิด
        self.btn_c4 = ToggleButton(text='C4', group='explosive', state='down', allow_no_selection=False)
        self.btn_c4.bind(on_press=self.on_explosive_change)
        
        self.btn_petn = ToggleButton(text='PETN', group='explosive', allow_no_selection=False)
        self.btn_petn.bind(on_press=self.on_explosive_change)
        
        self.btn_tnt = ToggleButton(text='TNT', group='explosive', allow_no_selection=False)
        self.btn_tnt.bind(on_press=self.on_explosive_change)
        
        type_layout.add_widget(self.btn_c4)
        type_layout.add_widget(self.btn_petn)
        type_layout.add_widget(self.btn_tnt)
        root.add_widget(type_layout)

        # 2. ช่องกรอกเส้นผ่านศูนย์กลาง (mm)
        root.add_widget(Label(text='เส้นผ่านศูนย์กลาง (mm):', size_hint_y=None, height=dp(30), font_size='16sp'))
        self.entry_dia = TextInput(multiline=False, input_type='number', input_filter='float', font_size='20sp', size_hint_y=None, height=dp(50))
        self.entry_dia.bind(text=self.calculate)
        root.add_widget(self.entry_dia)

        # 3. ช่องกรอกแรงอัดเครื่อง (tons)
        root.add_widget(Label(text='แรงอัดเครื่อง (Metric Tons):', size_hint_y=None, height=dp(30), font_size='16sp'))
        self.entry_ton = TextInput(multiline=False, input_type='number', input_filter='float', font_size='20sp', size_hint_y=None, height=dp(50))
        self.entry_ton.bind(text=self.calculate)
        root.add_widget(self.entry_ton)

        # 4. แสดงผล PSI (ตัวใหญ่)
        self.label_psi = Label(text='0 PSI', font_size='48sp', color=get_color_from_hex('#2ecc71'), size_hint_y=None, height=dp(100))
        root.add_widget(self.label_psi)

        # 5. แถบสีแสดงความอันตราย (Gauge)
        self.gauge_container = BoxLayout(size_hint_y=None, height=dp(40))
        with self.gauge_container.canvas.before:
            Color(rgb=get_color_from_hex('#333333'))
            self.gauge_bg_rect = Rectangle(pos=self.gauge_container.pos, size=self.gauge_container.size)
        
        # แถบสีจริงที่จะยืดหดได้
        self.gauge_fill = Widget(size_hint_x=0)
        with self.gauge_fill.canvas.before:
            self.gauge_fill_color = Color(rgb=get_color_from_hex('#2ecc71'))
            self.gauge_fill_rect = Rectangle(pos=self.gauge_fill.pos, size=self.gauge_fill.size)
            
        self.gauge_container.add_widget(self.gauge_fill)
        # Widget เปล่าเพื่อดัน gauge_fill ไปทางซ้าย
        self.gauge_container.add_widget(Widget(size_hint_x=1))
        
        root.add_widget(self.gauge_container)
        
        # ผูกฟังก์ชันเพื่ออัปเดตตำแหน่ง gauge เมื่อมีการเปลี่ยนแปลง layout
        self.gauge_container.bind(pos=self.update_gauge_rect, size=self.update_gauge_rect)

        # 6. ข้อมูลสถานะและขีดจำกัด
        self.label_info = Label(text='ระบุข้อมูล (mm) เพื่อคำนวณ', color=get_color_from_hex('#aaaaaa'), size_hint_y=None, height=dp(60), font_size='14sp', halign='center')
        root.add_widget(self.label_info)

        return root

    def on_explosive_change(self, instance):
        if instance.state == 'down':
            self.selected_explosive = instance.text
            self.calculate()

    def update_gauge_rect(self, instance, value):
        # อัปเดตตำแหน่งและขนาดของ Rectangle ตาม BoxLayout ของ Gauge
        self.gauge_bg_rect.pos = instance.pos
        self.gauge_bg_rect.size = instance.size
        # อัปเดต gauge_fill_rect ด้วย (แต่ size_x จะถูกกำหนดใน calculate)
        self.gauge_fill_rect.pos = instance.pos
        self.gauge_fill_rect.size = (self.gauge_fill.width, instance.height)

    def calculate(self, *args):
        try:
            d_val = self.entry_dia.text
            t_val = self.entry_ton.text
            
            if not d_val or not t_val: return

            dia_mm = float(d_val)
            tons = float(t_val)
            
            if dia_mm <= 0 or tons < 0: return

            # สูตรการคำนวณ (แปลง mm เป็น inch ก่อน)
            dia_inch = dia_mm / 25.4
            area_sq_inch = math.pi * (dia_inch / 2)**2
            force_lbs = tons * 2204.62
            current_psi = force_lbs / area_sq_inch
            
            # อัปเดตตัวเลข PSI
            self.label_psi.text = f'{int(current_psi):,} PSI'
            
            # คำนวณความเสี่ยงและอัปเดต Gauge
            limit_psi = EXPLOSIVE_DATA[self.selected_explosive]['limit']
            risk_ratio = current_psi / limit_psi
            
            # ปรับความกว้างของ Gauge (size_hint_x)
            self.gauge_fill.size_hint_x = min(1.0, risk_ratio)
            self.update_gauge_fill_rect_size() # อัปเดต Rectangle ทันที

            # เปลี่ยนสีตามระดับความอันตราย
            if risk_ratio < 0.6:
                color_hex = '#2ecc71' # Green
                status = "SAFE (ปลอดภัย)"
            elif risk_ratio < 0.9:
                color_hex = '#f1c40f' # Yellow
                status = "WARNING (ใกล้ขีดจำกัด)"
            else:
                color_hex = '#e74c3c' # Red
                status = "DANGER (อันตราย!)"
            
            final_color = get_color_from_hex(color_hex)
            self.label_psi.color = final_color
            self.gauge_fill_color.rgb = final_color
            self.label_info.text = f'สถานะ: {status}\n(Limit: {limit_psi:,} PSI)'

        except ValueError:
            pass

    def update_gauge_fill_rect_size(self):
        # อัปเดตขนาด Rectangle ของสี Gauge โดยอ้างอิงจาก size hint ที่เปลี่ยนไป
        self.gauge_fill_rect.size = (self.gauge_fill.width, self.gauge_container.height)

from kivy.uix.widget import Widget # เพิ่ม import Widget ที่ขาดไป

if __name__ == '__main__':
    BoosterSafetyApp().run()