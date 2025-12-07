import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.uix.spinner import Spinner
from kivy.uix.scatter import Scatter
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# --- CONFIGURAZIONE FINESTRA ---
# Dimensioni smartphone Full HD (proporzione 9:16)
Window.size = (405, 720)  # Full HD scalato per test su PC

# --- CONFIGURAZIONE ---
# GitHub repository
GITHUB_REPO = "sagara939/Visualizzatore_vignette"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# Estensioni immagini supportate
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

# Cartella base per le serie
COMICS_FOLDER = "comics"


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
            fit_mode='contain',
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.bind(source=self._update_source)
        self.bind(size=self._update_image_size)
        self.add_widget(self.image)
    
    def _update_source(self, instance, value):
        self.image.source = value
        self.scale = 1.0
        self.pos = (0, 0)
    
    def _update_image_size(self, instance, value):
        self.image.size = self.size


class ComicScreen(Screen):
    """Schermata principale per visualizzare le vignette"""
    current_series = StringProperty("")
    current_index = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Lista immagini della serie corrente
        self.images_list = []
        
        # Dizionario serie (nome -> cartella)
        self.series_config = {}
        
        # Layout principale
        self.layout = BoxLayout(orientation='vertical')
        
        # Header con menu serie e data
        self.header = BoxLayout(size_hint_y=0.08, padding=5, spacing=5)
        with self.header.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.header_rect = Rectangle(size=self.header.size, pos=self.header.pos)
        self.header.bind(size=self._update_header_rect, pos=self._update_header_rect)
        
        self.series_spinner = Spinner(
            text='Caricamento...',
            values=[],
            size_hint_x=0.5,
            background_color=(0.3, 0.3, 0.8, 1)
        )
        self.series_spinner.bind(text=self.on_series_change)
        
        self.counter_label = Label(
            text="0/0",
            size_hint_x=0.35,
            font_size='14sp'
        )
        
        self.refresh_btn = Button(
            text="⟳",
            size_hint_x=0.15,
            background_color=(0.3, 0.6, 0.3, 1)
        )
        self.refresh_btn.bind(on_press=self.refresh_images)
        
        self.header.add_widget(self.series_spinner)
        self.header.add_widget(self.counter_label)
        self.header.add_widget(self.refresh_btn)
        
        # Area immagine - BoxLayout che riempie lo spazio
        self.image_area = BoxLayout(
            orientation='vertical',
            size_hint_y=0.84
        )
        
        self.comic_image = ComicImage(
            size_hint=(1, 1)
        )
        self.image_area.add_widget(self.comic_image)
        
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
        self.layout.add_widget(self.image_area)
        self.layout.add_widget(self.footer)
        self.add_widget(self.layout)
        
        # Inizializza
        Clock.schedule_once(self.init_app, 0.5)
    
    def _update_header_rect(self, instance, value):
        self.header_rect.pos = instance.pos
        self.header_rect.size = instance.size
    
    def _update_footer_rect(self, instance, value):
        self.footer_rect.pos = instance.pos
        self.footer_rect.size = instance.size
    
    def init_app(self, dt):
        """Inizializza l'app caricando le serie da GitHub"""
        self.load_series_list()
    
    def load_series_list(self):
        """Carica la lista delle serie dalla cartella comics su GitHub"""
        api_url = f"{GITHUB_API_BASE}/{COMICS_FOLDER}"
        
        try:
            response = requests.get(api_url, timeout=10, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'ComicViewer-App'
            })
            
            if response.status_code == 200:
                items = response.json()
                
                # Filtra solo le cartelle (type == 'dir')
                self.series_config = {
                    item['name']: f"{COMICS_FOLDER}/{item['name']}"
                    for item in items
                    if item['type'] == 'dir'
                }
                
                # Aggiorna lo spinner con i nomi delle serie
                self.series_spinner.values = list(self.series_config.keys())
                
                if self.series_spinner.values:
                    self.series_spinner.text = self.series_spinner.values[0]
                else:
                    self.series_spinner.text = 'Nessuna serie'
            else:
                self.series_spinner.text = 'Errore caricamento'
                
        except Exception as e:
            print(f"Errore caricamento serie: {str(e)}")
            self.series_spinner.text = 'Errore connessione'
    
    def on_series_change(self, spinner, text):
        """Cambia serie selezionata"""
        if text in self.series_config:
            self.current_series = text
            self.current_index = 0
            self.images_list = []
            self.load_images_list()
    
    def load_images_list(self):
        """Carica la lista delle immagini dalla cartella GitHub"""
        if not self.current_series or self.current_series not in self.series_config:
            return
        
        folder = self.series_config[self.current_series]
        api_url = f"{GITHUB_API_BASE}/{folder}"
        
        print(f"Caricamento lista immagini da: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=10, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'ComicViewer-App'
            })
            
            print(f"Risposta API: {response.status_code}")
            
            if response.status_code == 200:
                files = response.json()
                
                # Filtra solo le immagini e ordina alfabeticamente
                self.images_list = sorted([
                    f['name'] for f in files 
                    if f['type'] == 'file' and 
                    any(f['name'].lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
                ])
                
                print(f"Trovate {len(self.images_list)} immagini: {self.images_list}")
                
                if self.images_list:
                    self.current_index = 0
                    self.load_comic()
                else:
                    self.counter_label.text = "0/0"
            else:
                print(f"Errore API: {response.status_code}")
                
        except Exception as e:
            print(f"Errore connessione: {str(e)}")
    
    def load_comic(self):
        """Carica l'immagine corrente"""
        if not self.images_list:
            return
        
        if 0 <= self.current_index < len(self.images_list):
            folder = self.series_config[self.current_series]
            filename = self.images_list[self.current_index]
            
            # Costruisci URL dell'immagine
            image_url = f"{GITHUB_RAW_BASE}/{folder}/{filename}"
            
            print(f"Caricamento immagine: {image_url}")
            self.comic_image.source = image_url
            
            # Aggiorna contatore
            self.counter_label.text = f"{self.current_index + 1}/{len(self.images_list)}"
            
            # Reset zoom
            self.comic_image.scale = 1.0
            self.comic_image.pos = (0, 0)
    
    def next_comic(self, instance=None):
        """Vai all'immagine successiva"""
        if self.images_list and self.current_index < len(self.images_list) - 1:
            self.current_index += 1
            self.load_comic()
    
    def prev_comic(self, instance=None):
        """Vai all'immagine precedente"""
        if self.images_list and self.current_index > 0:
            self.current_index -= 1
            self.load_comic()
    
    def refresh_images(self, instance=None):
        """Ricarica le serie e le immagini"""
        self.load_series_list()


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
