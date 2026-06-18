#!/usr/bin/env python3
import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import DatabaseManager
from app.auth import load_session, clear_session
from app.views.auth import AuthWindow

class DNDAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_default_color_theme("dark-blue")
        self.default_font = ctk.CTkFont(family="Segoe UI", size=12)
        self.option_add("*Font", self.default_font)
        self.title("D&D Ассистент")
        self.geometry("1200x750")
        self.minsize(1200, 750)
        ctk.set_appearance_mode("dark")

        
        self.db = DatabaseManager(password='1996')
        self.current_user_id = None
        self.main_frame = None
        self.sidebar = None
        self.campaign_label = None
        self.character_sheet_window = None
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        saved_uid = load_session(self.db)
        if saved_uid:
            self.current_user_id = saved_uid
            self._build_main_interface()
        else:
            self._open_auth_window()

    def _build_main_interface(self):
        """Создает основной интерфейс приложения"""
        # Очищаем старый интерфейс если был
        for widget in self.winfo_children():
            widget.destroy()
            
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text="🎲 D&D 5e", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        nav = [
            ("👥 Персонажи", 'characters'), ("⚔️ Бой", 'combat'), ("🎲 Кости", 'dice'),
            ("📝 Заметки", 'notes'), ("👹 Бестиарий", 'bestiary'), ("💰 Сокровища", 'treasury'),
            ("🎲 Генератор", 'generator'), ("⚙️ Настройки", 'settings')
        ]
        for text, key in nav:
            ctk.CTkButton(self.sidebar, text=text, command=lambda k=key: self._switch_view(k), anchor="w", height=40).pack(fill="x", padx=10, pady=2)
        
        self.campaign_label = ctk.CTkLabel(self.sidebar, text="", font=ctk.CTkFont(size=10), wraplength=180)
        self.campaign_label.pack(side="bottom", pady=10)
        
        self._init_views()
        
        campaign_name = self.db.get_config("campaign_name", "")
        if campaign_name: 
            self.campaign_label.configure(text=f"📜 {campaign_name}")
        
        self._switch_view('characters')

    def _init_views(self):
        uid = self.current_user_id
        self.views = {}
        
        self.views['characters'] = CharactersView(self.main_frame, self.db, uid, self._open_character_sheet)
        self.views['combat'] = CombatView(self.main_frame, self.db, uid)
        self.views['dice'] = DiceView(self.main_frame, self.db, uid)
        self.views['notes'] = NotesView(self.main_frame, self.db, uid)
        self.views['bestiary'] = BestiaryView(self.main_frame, self.db, uid)
        self.views['treasury'] = TreasuryView(self.main_frame, self.db, uid)
        self.views['generator'] = GeneratorView(self.main_frame)  # Генератору не нужен user_id
        self.views['settings'] = SettingsView(self.main_frame, self.db, self._save_campaign_name, uid, self._logout)
        
        for v in self.views.values(): 
            v.pack(fill="both", expand=True); v.pack_forget()

    def _switch_view(self, key):
        if hasattr(self, 'current_view') and self.current_view: 
            try: self.current_view.pack_forget()
            except: pass
            
        self.current_view = self.views[key]
        self.current_view.pack(fill="both", expand=True)
        if key == 'combat': 
            try: self.views['combat']._load_combat()
            except: pass

    def _open_character_sheet(self, char_id):
        if self.character_sheet_window: 
            try: self.character_sheet_window.destroy()
            except: pass
            
        from app.views.character_sheet import CharacterSheetView
        self.character_sheet_window = ctk.CTkToplevel(self)
        self.character_sheet_window.title("📋 Лист персонажа")
        self.character_sheet_window.geometry("1000x800")
        self.character_sheet_window.attributes("-topmost", True)
        self.character_sheet_window.lift()
        
        sheet = CharacterSheetView(self.character_sheet_window, self.db, self.current_user_id)
        sheet.pack(fill="both", expand=True)
        sheet.load_character(char_id)
        
        def on_close():
            if self.character_sheet_window:
                try: self.character_sheet_window.destroy()
                except: pass
            self.character_sheet_window = None
        self.character_sheet_window.protocol("WM_DELETE_WINDOW", on_close)

    def _save_campaign_name(self, name): 
        self.campaign_label.configure(text=f"📜 {name}")

    def _open_auth_window(self):
        """Показывает окно авторизации"""
        if hasattr(self, 'main_frame'):
            for widget in self.winfo_children(): widget.destroy()
            
        self.auth_win = AuthWindow(self, self.db, self._on_login_success)

    def _on_login_success(self, user_id: int):
        """Вызывается после успешного входа"""
        self.current_user_id = user_id
        if hasattr(self, 'auth_win') and self.auth_win.winfo_exists():
            self.auth_win.destroy()
        self._build_main_interface()

    def _logout(self):
        """Выход из аккаунта"""
        self.current_user_id = None
        clear_session()
        self._open_auth_window()
    
    def _on_closing(self):
        if self.character_sheet_window: 
            try: self.character_sheet_window.destroy()
            except: pass
        self.db.close(); self.destroy()

from app.views.characters import CharactersView
from app.views.combat import CombatView
from app.views.dice import DiceView
from app.views.notes import NotesView
from app.views.bestiary import BestiaryView
from app.views.treasury import TreasuryView
from app.views.generator import GeneratorView
from app.views.settings import SettingsView

def main(): 
    app = DNDAssistantApp(); app.mainloop()

if __name__ == "__main__": 
    main()