import os
import json
import requests
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scatter import Scatter
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# --- CONFIGURAZIONE ---
# GitHub raw content URL per il repository
GITHUB_REPO = "sagara939/Visualizzatore_vignette"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
CONFIG_URL = f"{GITHUB_RAW_BASE}/config.json"
LOCAL_CONFIG = "config.json"
CACHE_DIR = "cache"


class ComicImage(Scatter):
    """Widget per visualizzare l'immagine con zoom e pan"""
    source = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_rotation = False
        self.do_translation = True
        self.do_scale = True
        self.scale_min = 1.0
        self.scale_max = 5.0
        
        self.image = AsyncImage(
            source=self.source,
            allow_stretch=True,
            keep_ratio=True
        )
        self.bind(source=self._update_source)
        self.add_widget(self.image)
    
    def _update_source(self, instance, value):
        self.image.source = value
        self.scale = 1.0
        self.pos = (0, 0)
    
    def on_touch_down(self, touch):
        # Controlla se è un tocco con due dita (zoom)
        if len(touch.grab_list) > 0 or touch.is_double_tap:
            return super().on_touch_down(touch)
        return super().on_touch_down(touch)


class ComicScreen(Screen):
    """Schermata principale per visualizzare le vignette"""
    current_series = StringProperty("")
    current_date = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.series_data = {}
        self.touch_start_x = 0
        self.touch_start_y = 0
        self.swipe_threshold = 100
        self.is_swiping = False
        
        # Layout principale
        self.layout = BoxLayout(orientation='vertical')
        
        # Header con menu serie e data
        self.header = BoxLayout(size_hint_y=0.08, padding=5, spacing=5)
        with self.header.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.header_rect = Rectangle(size=self.header.size, pos=self.header.pos)
        self.header.bind(size=self._update_header_rect, pos=self._update_header_rect)
        
        self.series_spinner = Spinner(
            text='Seleziona Serie',
            values=[],
            size_hint_x=0.5,
            background_color=(0.3, 0.3, 0.8, 1)
        )
        self.series_spinner.bind(text=self.on_series_change)
        
        self.date_label = Label(
            text="",
            size_hint_x=0.35,
            font_size='14sp'
        )
        
        self.refresh_btn = Button(
            text="⟳",
            size_hint_x=0.15,
            background_color=(0.3, 0.6, 0.3, 1)
        )
        self.refresh_btn.bind(on_press=self.refresh_series)
        
        self.header.add_widget(self.series_spinner)
        self.header.add_widget(self.date_label)
        self.header.add_widget(self.refresh_btn)
        
        # Area immagine con scroll verticale
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint_y=0.84,
            bar_width=10,
            scroll_type=['bars', 'content']
        )
        
        self.image_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None
        )
        self.image_container.bind(minimum_height=self.image_container.setter('height'))
        
        self.comic_image = ComicImage(
            size_hint=(1, None),
            height=Window.height * 1.5
        )
        self.image_container.add_widget(self.comic_image)
        self.scroll_view.add_widget(self.image_container)
        
        # Footer con navigazione
        self.footer = BoxLayout(size_hint_y=0.08, padding=5, spacing=10)
        with self.footer.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.footer_rect = Rectangle(size=self.footer.size, pos=self.footer.pos)
        self.footer.bind(size=self._update_footer_rect, pos=self._update_footer_rect)
        
        self.prev_btn = Button(
            text="◀ Precedente",
            background_color=(0.4, 0.4, 0.6, 1)
        )
        self.prev_btn.bind(on_press=self.prev_comic)
        
        self.next_btn = Button(
            text="Successivo ▶",
            background_color=(0.4, 0.4, 0.6, 1)
        )
        self.next_btn.bind(on_press=self.next_comic)
        
        self.footer.add_widget(self.prev_btn)
        self.footer.add_widget(self.next_btn)
        
        self.layout.add_widget(self.header)
        self.layout.add_widget(self.scroll_view)
        self.layout.add_widget(self.footer)
        self.add_widget(self.layout)
        
        # Status popup
        self.status_label = None
        
        # Inizializza
        Clock.schedule_once(self.init_app, 0.5)
    
    def _update_header_rect(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size
    
    def _update_footer_rect(self, instance, value):
        self.footer_rect.pos = instance.pos
        self.footer_rect.size = instance.size
    
    def show_status(self, message, duration=2):
        """Mostra un messaggio di stato temporaneo"""
        popup = Popup(
            title='Info',
            content=Label(text=message),
            size_hint=(0.8, 0.2),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)
    
    def init_app(self, dt):
        """Inizializza l'app caricando la configurazione"""
        # Crea cartella cache se non esiste
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        self.load_config()
    
    def load_config(self):
        """Carica la configurazione delle serie (locale + remota)"""
        # Prova a caricare config remota
        try:
            response = requests.get(CONFIG_URL, timeout=5)
            if response.status_code == 200:
                remote_config = response.json()
                self.save_local_config(remote_config)
                self.apply_config(remote_config)
                print("Config remota caricata con successo")
                return
        except Exception as e:
            print(f"Errore caricamento config remota: {e}")
        
        # Fallback su config locale
        if os.path.exists(LOCAL_CONFIG):
            try:
                with open(LOCAL_CONFIG, 'r', encoding='utf-8') as f:
                    local_config = json.load(f)
                    self.apply_config(local_config)
                    print("Config locale caricata")
            except Exception as e:
                print(f"Errore config locale: {e}")
                self.apply_default_config()
        else:
            self.apply_default_config()
    
    def apply_default_config(self):
        """Applica configurazione di default"""
        default_config = {
            "series": [
                {
                    "name": "Serie Demo",
                    "base_url": "https://tuo-server.com/comics/demo/",
                    "date_format": "%Y-%m-%d",
                    "file_extension": ".png"
                }
            ]
        }
        self.save_local_config(default_config)
        self.apply_config(default_config)
    
    def save_local_config(self, config):
        """Salva la configurazione localmente"""
        try:
            with open(LOCAL_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio config: {e}")
    
    def apply_config(self, config):
        """Applica la configurazione caricata"""
        self.series_data = {s['name']: s for s in config.get('series', [])}
        self.series_spinner.values = list(self.series_data.keys())
        if self.series_spinner.values:
            self.series_spinner.text = self.series_spinner.values[0]
    
    def on_series_change(self, spinner, text):
        """Cambia serie selezionata"""
        if text in self.series_data:
            self.current_series = text
            self.current_date = datetime.now().strftime("%Y-%m-%d")
            self.load_comic()
    
    def load_comic(self):
        """Carica la vignetta corrente"""
        if not self.current_series or self.current_series not in self.series_data:
            return
        
        series = self.series_data[self.current_series]
        base_url = series.get('base_url', '')
        date_format = series.get('date_format', '%Y-%m-%d')
        extension = series.get('file_extension', '.png')
        
        # Costruisci URL immagine
        try:
            date_obj = datetime.strptime(self.current_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime(date_format)
        except:
            formatted_date = self.current_date
        
        image_url = f"{base_url}{formatted_date}{extension}"
        
        print(f"Caricamento: {image_url}")
        self.comic_image.source = image_url
        self.date_label.text = self.current_date
        
        # Reset zoom e scroll
        self.comic_image.scale = 1.0
        self.scroll_view.scroll_y = 1
    
    def next_comic(self, instance=None):
        """Vai alla vignetta successiva (giorno dopo)"""
        try:
            date_obj = datetime.strptime(self.current_date, "%Y-%m-%d")
            new_date = date_obj + timedelta(days=1)
            if new_date <= datetime.now():
                self.current_date = new_date.strftime("%Y-%m-%d")
                self.load_comic()
            else:
                self.show_status("Nessuna vignetta futura disponibile")
        except Exception as e:
            print(f"Errore navigazione: {e}")
    
    def prev_comic(self, instance=None):
        """Vai alla vignetta precedente (giorno prima)"""
        try:
            date_obj = datetime.strptime(self.current_date, "%Y-%m-%d")
            new_date = date_obj - timedelta(days=1)
            self.current_date = new_date.strftime("%Y-%m-%d")
            self.load_comic()
        except Exception as e:
            print(f"Errore navigazione: {e}")
    
    def refresh_series(self, instance=None):
        """Ricarica la configurazione delle serie dal server"""
        self.show_status("Aggiornamento serie...", 1)
        Clock.schedule_once(lambda dt: self.load_config(), 0.5)
    
    def on_touch_down(self, touch):
        """Rileva inizio swipe"""
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        self.is_swiping = False
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Rileva movimento swipe"""
        diff_x = abs(touch.x - self.touch_start_x)
        diff_y = abs(touch.y - self.touch_start_y)
        # Se movimento orizzontale > verticale, è uno swipe
        if diff_x > diff_y and diff_x > 50:
            self.is_swiping = True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        """Rileva fine swipe e cambia vignetta"""
        diff = touch.x - self.touch_start_x
        if self.is_swiping and abs(diff) > self.swipe_threshold:
            if diff > 0:
                self.prev_comic()
            else:
                self.next_comic()
            self.is_swiping = False
            return True
        return super().on_touch_up(touch)


class ComicViewerApp(App):
    """App principale"""
    
    def build(self):
        self.title = "Comic Viewer"
        
        # Imposta colore di sfondo
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        
        sm = ScreenManager()
        sm.add_widget(ComicScreen(name='comic'))
        return sm
    
    def on_pause(self):
        """Chiamato quando l'app va in pausa (Android)"""
        return True
    
    def on_resume(self):
        """Chiamato quando l'app riprende (Android)"""
        pass


if __name__ == '__main__':
    ComicViewerApp().run()
