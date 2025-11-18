import os
import json
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
import base64
from cryptography.fernet import Fernet

from modules.email_gmail import GmailClient
from modules.llm_status import get_monitor as get_llm_monitor
from modules.llm_analyzer import LLMAnalyzer
from modules.html_exporter import HTMLExporter
from modules.email_monitor import EmailMonitor
from modules.plugin_manager import PluginManager

# Configurações salvas em memória (priorizadas)
_CONFIG_CACHE = None

# Apenas se usuário quiser persistir, salva em pasta do sistema
CONFIG_DIR = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'SimpleNFE')
CONFIG_PATH = os.path.join(CONFIG_DIR, '.config')


def _get_machine_key():
    """Gera uma chave única baseada na máquina (sem arquivo externo)"""
    try:
        import platform
        import hashlib
        # Usa informações da máquina para gerar chave consistente
        machine_id = f"{platform.node()}-{platform.machine()}-{os.path.expanduser('~')}"
        # Gera hash SHA256
        key_material = hashlib.sha256(machine_id.encode()).digest()
        # Converte para formato Fernet
        return base64.urlsafe_b64encode(key_material)
    except Exception:
        # Fallback: chave fixa (menos seguro mas funciona)
        return base64.urlsafe_b64encode(b'SimpleNFE_Default_Key_32byte!')


def _encrypt_password(password: str) -> str:
    """Criptografa a senha para salvar no config"""
    try:
        if not password:
            return ""
        key = _get_machine_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception:
        # Se falhar, retorna em base64 simples (melhor que plain text)
        return base64.b64encode(password.encode()).decode()


def _decrypt_password(encrypted: str) -> str:
    """Descriptografa a senha do config"""
    try:
        if not encrypted:
            return ""
        key = _get_machine_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception:
        # Tenta base64 simples (compatibilidade com configs antigos)
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except Exception:
            # Retorna como está (pode ser senha não criptografada antiga)
            return encrypted


def load_config():
    global _CONFIG_CACHE
    
    # Se já está em memória, usa direto
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    
    default = {
        "email": {
            "server": "imap.gmail.com",
            "port": 993,
            "address": "",
            "app_password": ""
        },
        "lmstudio": {
            "url": "http://127.0.0.1:1234",
            "model": "qwen/qwen3-vl-4b"
        },
        "search": {
            "include_keywords": ["nfe", "nf-e", "nota", "xml", "danfe", "fiscal", "fatura", "invoice", "eletronica", "nfce", "cupom"],
            "exclude_keywords": ["promo", "oferta", "newsletter"]
        }
    }
    
    # Tenta carregar do arquivo (se existir)
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Descriptografa a senha se estiver criptografada
                if 'email' in data and 'app_password' in data['email']:
                    encrypted_pwd = data['email']['app_password']
                    if encrypted_pwd:
                        data['email']['app_password'] = _decrypt_password(encrypted_pwd)
                # merge raso
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                    elif isinstance(v, dict):
                        for k2, v2 in v.items():
                            data[k].setdefault(k2, v2)
                _CONFIG_CACHE = data
                return data
    except Exception as e:
        print(f"Aviso ao carregar config: {e}")
    
    # Usa default e salva em memória
    _CONFIG_CACHE = default
    return default


def save_config(cfg, persist=True):
    """Salva config na memória e opcionalmente persiste em disco
    
    Args:
        cfg: Configuração a salvar
        persist: Se True, salva em disco também (padrão: True)
    """
    global _CONFIG_CACHE
    
    # Sempre salva em memória
    _CONFIG_CACHE = cfg
    
    # Se persist=False, apenas mantém em memória (reinicia perde)
    if not persist:
        return True
    
    # Persiste em disco se solicitado
    try:
        # Cria diretório se não existir
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Cria cópia para não modificar o original
        cfg_to_save = json.loads(json.dumps(cfg))
        # Criptografa a senha antes de salvar
        if 'email' in cfg_to_save and 'app_password' in cfg_to_save['email']:
            password = cfg_to_save['email']['app_password']
            if password:
                cfg_to_save['email']['app_password'] = _encrypt_password(password)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg_to_save, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        # Se falhar em salvar no disco, ainda está em memória
        print(f"Aviso: Não foi possível persistir config em disco: {e}")
        return True  # Retorna True porque está em memória


class SimpleNFEApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simple NFE - Gmail")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.cfg = load_config()
        self.gmail: GmailClient | None = None
        self._item_uid: dict[str, str] = {}
        self.search_results = []  # resultados de notas encontradas
        self.extracted_items = []  # itens extraídos
        
        # Controle de operações concorrentes
        self._operation_lock = threading.Lock()
        self._email_operation_running = False
        self._extraction_operation_running = False
        
        # Flags de cancelamento
        self._cancel_search = False
        self._cancel_extraction = False
        self._cancel_local_analysis = False
        
        # Arquivos locais selecionados
        self.local_files = []
        
        # Monitores e módulos auxiliares
        self.llm_monitor = None
        self.email_monitor = None
        self.llm_analyzer = None
        
        # Gerenciador de plugins
        self.plugin_manager = PluginManager("plugins")

        self._build_ui()
        
        # Auto-save ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ---------------- UI -----------------
    def _build_ui(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Abas
        self.tab_conn = ttk.Frame(self.nb)
        self.tab_search = ttk.Frame(self.nb)
        self.tab_cfg = ttk.Frame(self.nb)
        self.tab_extract = ttk.Frame(self.nb)
        self.tab_local = ttk.Frame(self.nb)
        self.tab_items = ttk.Frame(self.nb)

        self.nb.add(self.tab_conn, text="Conexão")
        self.nb.add(self.tab_search, text="Pesquisa de Notas")
        self.nb.add(self.tab_extract, text="Extração")
        self.nb.add(self.tab_local, text="Análise Local")
        self.nb.add(self.tab_items, text="Itens")
        self.nb.add(self.tab_cfg, text="Configurações")

        self._build_tab_conn()
        self._build_tab_search()
        self._build_tab_extract()
        self._build_tab_local()
        self._build_tab_items()
        self._build_tab_cfg()

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status = ttk.Frame(self.root)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status, textvariable=self.status_var).pack(side=tk.LEFT, padx=10, pady=4)
        
        # Inicializa monitores após UI estar pronta
        self._init_monitors()

    # ---- Aba Conexão ----
    def _build_tab_conn(self):
        top = ttk.Frame(self.tab_conn)
        top.pack(fill=tk.X, padx=16, pady=12)

        ttk.Label(top, text="Quantidade a listar:").pack(side=tk.LEFT)
        self.conn_qty_var = tk.IntVar(value=10)
        ttk.Entry(top, textvariable=self.conn_qty_var, width=6).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Conectar e Listar", command=self.on_connect_and_list).pack(side=tk.LEFT, padx=8)

        # Info total da INBOX
        info_frame = ttk.Frame(self.tab_conn)
        info_frame.pack(fill=tk.X, padx=16)
        self.total_label_var = tk.StringVar(value="Total na INBOX: -")
        ttk.Label(info_frame, textvariable=self.total_label_var).pack(side=tk.LEFT)

        self.conn_tree = ttk.Treeview(self.tab_conn, columns=("date", "from", "subject"), show="headings")
        self.conn_tree.heading("date", text="Data")
        self.conn_tree.heading("from", text="De")
        self.conn_tree.heading("subject", text="Assunto")
        self.conn_tree.column("date", width=180)
        self.conn_tree.column("from", width=280)
        self.conn_tree.column("subject", width=600)
        self.conn_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self.conn_tree.bind('<Double-1>', self._on_open_selected_from_conn)

    # ---- Aba Pesquisa ----
    def _build_tab_search(self):
        controls = ttk.Frame(self.tab_search)
        controls.pack(fill=tk.X, padx=16, pady=12)

        ttk.Label(controls, text="Tipo de nota:").pack(side=tk.LEFT)
        # Agora pode selecionar ambos
        self.note_pdf_var = tk.BooleanVar(value=True)
        self.note_xml_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="PDF", variable=self.note_pdf_var).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(controls, text="XML", variable=self.note_xml_var).pack(side=tk.LEFT, padx=6)

        ttk.Label(controls, text="Quantidade a buscar:").pack(side=tk.LEFT, padx=(16, 0))
        self.search_qty_var = tk.IntVar(value=50)
        ttk.Entry(controls, textvariable=self.search_qty_var, width=6).pack(side=tk.LEFT, padx=6)

        self.btn_search = ttk.Button(controls, text="Buscar", command=self.on_search_notes)
        self.btn_search.pack(side=tk.LEFT, padx=8)
        
        self.btn_cancel_search = ttk.Button(controls, text="Cancelar", command=self._cancel_search_operation, state=tk.DISABLED)
        self.btn_cancel_search.pack(side=tk.LEFT, padx=8)

        # Progress
        prog_frame = ttk.Frame(self.tab_search)
        prog_frame.pack(fill=tk.X, padx=16)
        self.progress = ttk.Progressbar(prog_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, pady=(0, 8))
        # status local da aba de pesquisa
        self.search_status_var = tk.StringVar(value="Pronto")
        ttk.Label(prog_frame, textvariable=self.search_status_var).pack(anchor=tk.W, pady=(0, 6))

        # Resultados
        self.results_tree = ttk.Treeview(self.tab_search,
                                         columns=("date", "from", "subject", "filename", "type"),
                                         show="headings")
        for col, text, w in [
            ("date", "Data", 160),
            ("from", "De", 260),
            ("subject", "Assunto", 420),
            ("filename", "Arquivo", 200),
            ("type", "Tipo", 80),
        ]:
            self.results_tree.heading(col, text=text)
            self.results_tree.column(col, width=w, anchor=tk.W)
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self.results_tree.bind('<Double-1>', self._on_open_selected_from_results)

    # ---- Aba Config ----
    def _build_tab_cfg(self):
        form = ttk.Frame(self.tab_cfg)
        form.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Email config
        ttk.Label(form, text="Servidor IMAP:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.cfg_server = tk.StringVar(value=self.cfg['email']['server'])
        ttk.Entry(form, textvariable=self.cfg_server, width=30).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(form, text="Porta:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.cfg_port = tk.IntVar(value=self.cfg['email']['port'])
        ttk.Entry(form, textvariable=self.cfg_port, width=8).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(form, text="Endereço de Email:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.cfg_address = tk.StringVar(value=self.cfg['email']['address'])
        ttk.Entry(form, textvariable=self.cfg_address, width=40).grid(row=1, column=1, sticky=tk.W, columnspan=3)

        ttk.Label(form, text="Senha de App (Gmail):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.cfg_password = tk.StringVar(value=self.cfg['email']['app_password'])
        
        # Frame para senha + botão mostrar/ocultar
        pwd_frame = ttk.Frame(form)
        pwd_frame.grid(row=2, column=1, sticky=tk.W, columnspan=2)
        
        self.pwd_entry = ttk.Entry(pwd_frame, textvariable=self.cfg_password, width=30, show='•')
        self.pwd_entry.pack(side=tk.LEFT)
        
        self.show_password_var = tk.BooleanVar(value=False)
        self.btn_toggle_pwd = ttk.Button(pwd_frame, text="👁️ Mostrar", width=10, command=self._toggle_password_visibility)
        self.btn_toggle_pwd.pack(side=tk.LEFT, padx=6)

        # Keywords
        ttk.Label(form, text="Palavras-chave (incluir):").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.cfg_include = tk.StringVar(value=", ".join(self.cfg['search']['include_keywords']))
        ttk.Entry(form, textvariable=self.cfg_include, width=70).grid(row=3, column=1, sticky=tk.W, columnspan=3)

        ttk.Label(form, text="Palavras-chave (ignorar):").grid(row=4, column=0, sticky=tk.W, pady=4)
        self.cfg_exclude = tk.StringVar(value=", ".join(self.cfg['search']['exclude_keywords']))
        ttk.Entry(form, textvariable=self.cfg_exclude, width=70).grid(row=4, column=1, sticky=tk.W, columnspan=3)

        # LM Studio
        ttk.Label(form, text="LM Studio URL:").grid(row=5, column=0, sticky=tk.W, pady=8)
        self.cfg_lm_url = tk.StringVar(value=self.cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234'))
        ttk.Entry(form, textvariable=self.cfg_lm_url, width=40).grid(row=5, column=1, sticky=tk.W, columnspan=3)

        ttk.Label(form, text="LM Studio Modelo:").grid(row=6, column=0, sticky=tk.W, pady=4)
        self.cfg_lm_model = tk.StringVar(value=self.cfg.get('lmstudio', {}).get('model', 'openai/gpt-oss-20b'))
        ttk.Entry(form, textvariable=self.cfg_lm_model, width=40).grid(row=6, column=1, sticky=tk.W, columnspan=3)

        # Opção para persistir configurações
        ttk.Label(form, text="").grid(row=7, column=0)
        self.persist_config_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            form, 
            text="Salvar configurações no disco (C:\\ProgramData\\SimpleNFE)",
            variable=self.persist_config_var
        ).grid(row=7, column=0, columnspan=4, sticky=tk.W, pady=8)
        ttk.Label(form, text="(Desmarcado = apenas na memória RAM, perde ao fechar)", font=('Segoe UI', 8)).grid(row=8, column=0, columnspan=4, sticky=tk.W)

        # Save button
        ttk.Button(form, text="Salvar Configurações", command=self.on_save_config).grid(row=9, column=0, pady=(16, 0))

        # Grid config
        for i in range(10):
            form.grid_rowconfigure(i, weight=0)
        for j in range(4):
            form.grid_columnconfigure(j, weight=1)

    # --------------- Actions -----------------
    def _toggle_password_visibility(self):
        """Alterna entre mostrar e ocultar a senha"""
        if self.show_password_var.get():
            # Ocultar senha
            self.pwd_entry.configure(show='•')
            self.btn_toggle_pwd.configure(text="👁️ Mostrar")
            self.show_password_var.set(False)
        else:
            # Mostrar senha
            self.pwd_entry.configure(show='')
            self.btn_toggle_pwd.configure(text="🚫 Ocultar")
            self.show_password_var.set(True)
    
    def _get_client(self) -> GmailClient:
        if self.gmail is None:
            self.gmail = GmailClient(
                self.cfg['email']['server'],
                int(self.cfg['email']['port']),
                self.cfg['email']['address'],
                self.cfg['email']['app_password'],
            )
        return self.gmail

    def on_connect_and_list(self):
        # Verifica se já há operação de email em andamento
        if self._email_operation_running:
            messagebox.showwarning("Operação em andamento", "Já existe uma operação de email em execução. Aguarde a conclusão.")
            return
            
        qty = max(1, int(self.conn_qty_var.get() or 10))
        self.status_var.set("Conectando e listando...")
        self.conn_tree.delete(*self.conn_tree.get_children())

        def on_item_loaded(item: dict):
            """Callback progressivo: adiciona item à UI conforme é processado"""
            def add():
                iid = str(item['uid'])
                self.conn_tree.insert('', tk.END, iid=iid, values=(item['date'], item['from'], item['subject']))
                self._item_uid[iid] = str(item['uid'])
            self.root.after(0, add)

        def run():
            self._email_operation_running = True
            try:
                client = self._get_client()
                total = client.count_inbox()
                self.root.after(0, lambda: self.total_label_var.set(f"Total na INBOX: {total}"))
                # Carregamento progressivo com callback
                recent = client.list_recent(qty, result_callback=on_item_loaded)
                self.root.after(0, lambda: self.status_var.set(f"Listados {len(recent)} emails (de {total})"))
            except Exception as e:
                error_msg = str(e)
                if "AUTHENTICATION" in error_msg.upper() or "credentials" in error_msg.lower():
                    error_msg = (
                        "Falha na autenticação!\n\n"
                        "Verifique:\n"
                        "1. Email está correto\n"
                        "2. Senha de App está correta (16 caracteres sem espaços)\n"
                        "3. Gere nova senha em: https://myaccount.google.com/apppasswords\n\n"
                        f"Erro técnico: {e}"
                    )
                self.root.after(0, lambda: self.status_var.set("Erro de autenticação"))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Erro de Conexão", msg))
            finally:
                self._email_operation_running = False
        threading.Thread(target=run, daemon=True).start()

    def on_search_notes(self):
        # Verifica se já há operação de email em andamento
        if self._email_operation_running:
            messagebox.showwarning("Operação em andamento", "Já existe uma operação de email em execução. Aguarde a conclusão.")
            return
            
        qty = max(1, int(self.search_qty_var.get() or 10))
        note_types = []
        if self.note_pdf_var.get():
            note_types.append('PDF')
        if self.note_xml_var.get():
            note_types.append('XML')
        # Usar keywords das configurações
        include = self.cfg.get('search', {}).get('include_keywords', [])
        exclude = self.cfg.get('search', {}).get('exclude_keywords', [])

        self.results_tree.delete(*self.results_tree.get_children())
        self.progress['value'] = 0
        self.status_var.set("Buscando notas...")
        self.search_status_var.set("Iniciando busca...")
        self._cancel_search = False
        try:
            self.btn_search.configure(state=tk.DISABLED)
            self.btn_cancel_search.configure(state=tk.NORMAL)
        except Exception:
            pass

        def progress_cb(done: int, total: int):
            val = int((done / max(1, total)) * 100)
            # atualizar UI de forma thread-safe
            self.root.after(0, lambda: (
                self.progress.configure(value=val),
                self.search_status_var.set(f"Buscando... {done}/{total}")
            ))

        def on_result_found(r: dict):
            """Callback progressivo: adiciona resultado à UI conforme é encontrado"""
            def add():
                iid = f"{r['uid']}::{r['filename']}::{len(self._item_uid)}"
                self.results_tree.insert('', tk.END, iid=iid, values=(r['date'], r['from'], r['subject'], r['filename'], r['type']))
                self._item_uid[iid] = str(r['uid'])
            self.root.after(0, add)

        def run():
            self._email_operation_running = True
            try:
                client = self._get_client()
                # Debug: mostra o que está buscando
                print(f"\n[BUSCA] Tipos: {note_types}")
                print(f"[BUSCA] Quantidade: {qty}")
                print(f"[BUSCA] Incluir keywords: {include}")
                print(f"[BUSCA] Excluir keywords: {exclude}")
                # Carregamento progressivo com callback
                # Passa lambda para verificar cancelamento
                results = client.search_notes(
                    note_types, qty, include, exclude, 
                    progress_cb, 
                    result_callback=on_result_found,
                    cancel_check=lambda: self._cancel_search
                )
                
                if self._cancel_search:
                    self.root.after(0, lambda: (
                        self.status_var.set("Busca cancelada"),
                        self.search_status_var.set("Cancelada"),
                        self.btn_search.configure(state=tk.NORMAL),
                        self.btn_cancel_search.configure(state=tk.DISABLED)
                    ))
                    return
                    
                self.search_results = results
                # reconstroi a aba de extração (lista de selecionáveis)
                self._load_extract_from_results()
                self.root.after(0, lambda: (
                    self.status_var.set(f"Busca concluída: {len(results)} resultados"),
                    self.search_status_var.set("Concluída"),
                    self.progress.configure(value=100),
                    self.btn_search.configure(state=tk.NORMAL),
                    self.btn_cancel_search.configure(state=tk.DISABLED)
                ))
            except Exception as e:
                error_msg = str(e)
                if "AUTHENTICATION" in error_msg.upper() or "credentials" in error_msg.lower():
                    error_msg = (
                        "Falha na autenticação!\n\n"
                        "Verifique suas credenciais na aba Configurações.\n"
                        f"Erro: {e}"
                    )
                self.root.after(0, lambda: self.status_var.set("Erro de autenticação"))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Erro na busca", msg))
                try:
                    self.root.after(0, lambda: (
                        self.btn_search.configure(state=tk.NORMAL),
                        self.btn_cancel_search.configure(state=tk.DISABLED)
                    ))
                except Exception:
                    pass
            finally:
                self._email_operation_running = False
                self._cancel_search = False

        threading.Thread(target=run, daemon=True).start()

    def _cancel_search_operation(self):
        """Cancela a operação de busca em andamento"""
        self._cancel_search = True
        self.search_status_var.set("Cancelando busca...")
        self.status_var.set("Busca cancelada pelo usuário")

    # ---- Aba Extração ----
    def _build_tab_extract(self):
        top = ttk.Frame(self.tab_extract)
        top.pack(fill=tk.X, padx=16, pady=12)

        self.btn_load_from_search = ttk.Button(top, text="Carregar da Pesquisa", command=self._load_extract_from_results)
        self.btn_load_from_search.pack(side=tk.LEFT)
        self.btn_mark_all = ttk.Button(top, text="Marcar Todos", command=lambda: self._extract_mark_all(True))
        self.btn_mark_all.pack(side=tk.LEFT, padx=8)
        self.btn_unmark_all = ttk.Button(top, text="Desmarcar Todos", command=lambda: self._extract_mark_all(False))
        self.btn_unmark_all.pack(side=tk.LEFT)
        self.btn_extract = ttk.Button(top, text="Extrair Marcados", command=self._extract_selected)
        self.btn_extract.pack(side=tk.LEFT, padx=8)
        
        self.btn_cancel_extract = ttk.Button(top, text="Cancelar", command=self._cancel_extraction_operation, state=tk.DISABLED)
        self.btn_cancel_extract.pack(side=tk.LEFT, padx=8)
        
        # Status da LLM
        self.extract_llm_status_var = tk.StringVar(value="LLM: Verificando...")
        ttk.Label(top, textvariable=self.extract_llm_status_var, foreground="gray").pack(side=tk.RIGHT, padx=8)

        # progresso
        self.extract_progress = ttk.Progressbar(self.tab_extract, mode='determinate', maximum=100)
        self.extract_progress.pack(fill=tk.X, padx=16)
        self.extract_status_var = tk.StringVar(value="Pronto")
        ttk.Label(self.tab_extract, textvariable=self.extract_status_var).pack(anchor=tk.W, padx=16, pady=(6, 0))

        cols = ("sel", "date", "from", "subject", "filename", "type")
        self.extract_tree = ttk.Treeview(self.tab_extract, columns=cols, show='headings', selectmode='none')
        for col, text, w in [
            ("sel", "Selecionar", 100),
            ("date", "Data", 150),
            ("from", "De", 220),
            ("subject", "Assunto", 360),
            ("filename", "Arquivo", 220),
            ("type", "Tipo", 60),
        ]:
            self.extract_tree.heading(col, text=text)
            self.extract_tree.column(col, width=w, anchor=tk.W)
        self.extract_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self.extract_tree.bind('<Button-1>', self._on_extract_click)
        self.extract_selected: dict[str, bool] = {}

    def _load_extract_from_results(self):
        if not hasattr(self, 'extract_tree'):
            return
        self.extract_tree.delete(*self.extract_tree.get_children())
        self.extract_selected.clear()
        for r in self.search_results:
            iid = f"X::{r['uid']}::{r['filename']}::{len(self._item_uid)}"
            self.extract_tree.insert('', tk.END, iid=iid, values=("☐", r['date'], r['from'], r['subject'], r['filename'], r['type']))
            self._item_uid[iid] = str(r['uid'])
            self.extract_selected[iid] = False

    def _extract_mark_all(self, checked: bool):
        for iid in self.extract_tree.get_children():
            self.extract_selected[iid] = checked
            self.extract_tree.set(iid, 'sel', '☑' if checked else '☐')

    def _on_extract_click(self, event):
        # identifica coluna e linha clicada; se for a coluna 'sel', alterna a marcação
        region = self.extract_tree.identify('region', event.x, event.y)
        if region != 'cell':
            return
        col = self.extract_tree.identify_column(event.x)
        # '#1' é a primeira coluna (sel)
        if col != '#1':
            return
        row = self.extract_tree.identify_row(event.y)
        if not row:
            return
        cur = self.extract_selected.get(row, False)
        self.extract_selected[row] = not cur
        self.extract_tree.set(row, 'sel', '☑' if not cur else '☐')

    def _extract_selected(self):
        # Verifica se já há extração em andamento
        if self._extraction_operation_running:
            messagebox.showwarning("Extração em andamento", "Já existe uma extração em execução. Aguarde a conclusão.")
            return
            
        sel = [iid for iid, v in self.extract_selected.items() if v]
        if not sel:
            messagebox.showinfo("Extração", "Selecione pelo menos um item.")
            return
        # reset barra e status
        self._set_extract_progress(0)
        self._set_extract_status("Preparando extração...")
        self._cancel_extraction = False
        try:
            self.extract_progress.configure(mode='determinate', maximum=100)
        except Exception:
            pass
        # desabilita botões durante extração
        for b in (self.btn_extract, self.btn_mark_all, self.btn_unmark_all, self.btn_load_from_search):
            try:
                b.configure(state=tk.DISABLED)
            except Exception:
                pass
        try:
            self.btn_cancel_extract.configure(state=tk.NORMAL)
        except Exception:
            pass
        # monta seleções
        selections = []
        for iid in sel:
            vals = self.extract_tree.item(iid, 'values')
            uid = self._item_uid.get(iid)
            if not uid:
                continue
            # com coluna 'sel', o filename agora está no índice 4 e type no 5
            selections.append({'uid': uid, 'filename': vals[4], 'type': vals[5]})

        # deduplicação: se existir (uid, base) com PDF e XML, preferir XML
        selections = self._dedupe_selections(selections)

        # roda em thread
        def run():
            self._extraction_operation_running = True
            try:
                from modules.xml_pdf_extractor import extract_items_from_xml, extract_text_from_pdf, extract_items_from_pdf_via_llm
                import os

                temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
                os.makedirs(temp_dir, exist_ok=True)

                client = self._get_client()
                # feedback de download
                def dl_cb(d, t):
                    pct = int((d / max(1, t)) * 100)
                    self._set_extract_status(f"Baixando anexos... {d}/{t}")
                    self._set_extract_progress(pct)
                self._set_extract_status("Baixando anexos...")
                downloaded = client.download_attachments(selections, temp_dir, progress_cb=dl_cb)

                all_items = []
                seen = set()
                total_att = len(downloaded)
                for idx, att in enumerate(downloaded, start=1):
                    # Verifica cancelamento
                    if self._cancel_extraction:
                        self._set_extract_status("Extração cancelada")
                        messagebox.showinfo("Extração", f"Extração cancelada. {len(all_items)} itens foram processados antes do cancelamento.")
                        break
                    
                    path = att['path']
                    fname = os.path.basename(path)
                    try:
                        if att.get('type') == 'XML' or path.lower().endswith('.xml'):
                            self._set_extract_status(f"Extraindo XML: {fname}")
                            items = extract_items_from_xml(path)
                        else:
                            self._set_extract_status(f"Extraindo PDF via LM: {fname} (aguarde)")
                            # modo indeterminado enquanto aguarda LM
                            try:
                                self.root.after(0, lambda: (self.extract_progress.configure(mode='indeterminate'), self.extract_progress.start(10)))
                            except Exception:
                                pass
                            text = extract_text_from_pdf(path)
                            print(f"\n[APP] Texto extraído do PDF {fname}: {len(text) if text else 0} caracteres")
                            print(f"[APP] Primeiros 500 chars: {text[:500] if text else 'VAZIO'}")
                            
                            if not text or len(text.strip()) < 50:
                                self._set_extract_status(f"PDF vazio ou com pouco texto: {fname}")
                                print(f"[APP] PDF {fname} rejeitado: texto insuficiente")
                                items = []
                            else:
                                print(f"[APP] Enviando para LM Studio...")
                                print(f"[APP] URL: {self.cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234')}")
                                print(f"[APP] Modelo: {self.cfg.get('lmstudio', {}).get('model', 'openai/gpt-oss-20b')}")
                                try:
                                    items = extract_items_from_pdf_via_llm(
                                        text,
                                        self.cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234'),
                                        self.cfg.get('lmstudio', {}).get('model', 'openai/gpt-oss-20b')
                                    )
                                    print(f"[APP] LM Studio retornou {len(items)} itens")
                                except Exception as e:
                                    error_msg = f"Erro ao extrair PDF {fname}: {str(e)}"
                                    print(f"[APP] {error_msg}")
                                    self._set_extract_status(error_msg)
                                    items = []
                            # volta ao modo determinate e avança proporção
                            try:
                                self.root.after(0, lambda: (self.extract_progress.stop(), self.extract_progress.configure(mode='determinate')))
                            except Exception:
                                pass
                        
                        print(f"[APP] Total de itens antes da dedup: {len(items)}")
                        for it in items:
                            it['documento'] = fname
                            # evita itens duplicados idênticos
                            key = (
                                it.get('documento',''),
                                it.get('descricao','').strip().lower(),
                                round(float(it.get('quantidade', 0) or 0), 6),
                                round(float(it.get('valor_unit', 0) or 0), 6),
                                round(float(it.get('valor_total', 0) or 0), 6),
                            )
                            if key in seen:
                                continue
                            seen.add(key)
                            all_items.append(it)
                    except Exception as e:
                        self._set_extract_status(f"Erro ao processar {fname}: {str(e)}")
                    
                    # avança progresso geral por anexo
                    pct = int((idx / max(1, total_att)) * 100)
                    self._set_extract_progress(pct)

                self.extracted_items = all_items
                self._refresh_items_tab()
                self._set_extract_progress(100)
                self._set_extract_status("Extração concluída.")
                messagebox.showinfo("Extração", f"Extração concluída ({len(all_items)} itens).")
            except Exception as e:
                error_msg = f"Erro na extração: {str(e)}"
                messagebox.showerror("Erro na extração", error_msg)
                self._set_extract_progress(0)
                self._set_extract_status("Erro na extração")
            finally:
                self._extraction_operation_running = False
                self._cancel_extraction = False
                # reabilita botões
                for b in (self.btn_extract, self.btn_mark_all, self.btn_unmark_all, self.btn_load_from_search):
                    try:
                        self.root.after(0, lambda bt=b: bt.configure(state=tk.NORMAL))
                    except Exception:
                        pass
                try:
                    self.root.after(0, lambda: self.btn_cancel_extract.configure(state=tk.DISABLED))
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    def _cancel_extraction_operation(self):
        """Cancela a operação de extração em andamento"""
        self._cancel_extraction = True
        self._set_extract_status("Cancelando extração...")
        self.status_var.set("Extração cancelada pelo usuário")

    def _set_extract_progress(self, v: int):
        # atualizar barra de forma thread-safe
        try:
            self.root.after(0, lambda: self.extract_progress.configure(value=v))
        except Exception:
            pass

    def _set_extract_status(self, msg: str):
        try:
            self.root.after(0, lambda: (self.extract_status_var.set(msg), self.status_var.set(msg)))
        except Exception:
            pass

    def _dedupe_selections(self, selections: list[dict]) -> list[dict]:
        """Se houver (uid, base) com PDF e XML, manter apenas XML.
        base é o nome do arquivo sem extensão, normalizado.
        """
        grouped: dict[tuple[str, str], list[dict]] = {}
        for s in selections:
            uid = str(s.get('uid'))
            fname = str(s.get('filename') or '')
            base = re.sub(r'[^a-z0-9]', '', os.path.splitext(fname.lower())[0])
            key = (uid, base)
            grouped.setdefault(key, []).append(s)
        out: list[dict] = []
        for items in grouped.values():
            xml = [x for x in items if (x.get('type') or '').upper() == 'XML' or str(x.get('filename','')).lower().endswith('.xml')]
            if xml:
                out.append(xml[0])
            else:
                out.append(items[0])
        return out

    # ---- Aba Análise Local ----
    def _build_tab_local(self):
        top = ttk.Frame(self.tab_local)
        top.pack(fill=tk.X, padx=16, pady=12)

        ttk.Button(top, text="Selecionar Arquivos", command=self._select_local_files).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top, text="Selecionar Pasta", command=self._select_local_folder).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top, text="Limpar Seleção", command=self._clear_local_files).pack(side=tk.LEFT, padx=(0, 8))
        self.btn_analyze_local = ttk.Button(top, text="Analisar Arquivos", command=self._analyze_local_files)
        self.btn_analyze_local.pack(side=tk.LEFT, padx=(16, 0))
        
        self.btn_cancel_local = ttk.Button(top, text="Cancelar", command=self._cancel_local_analysis_operation, state=tk.DISABLED)
        self.btn_cancel_local.pack(side=tk.LEFT, padx=8)
        
        # Status da LLM
        self.local_llm_status_var = tk.StringVar(value="LLM: Verificando...")
        ttk.Label(top, textvariable=self.local_llm_status_var, foreground="gray").pack(side=tk.RIGHT, padx=8)

        # Contador
        self.local_count_var = tk.StringVar(value="Arquivos selecionados: 0")
        ttk.Label(top, textvariable=self.local_count_var).pack(side=tk.RIGHT)

        # Progresso
        prog_frame = ttk.Frame(self.tab_local)
        prog_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.local_progress = ttk.Progressbar(prog_frame, mode='determinate', maximum=100)
        self.local_progress.pack(fill=tk.X, pady=(0, 8))
        self.local_status_var = tk.StringVar(value="Pronto")
        ttk.Label(prog_frame, textvariable=self.local_status_var).pack(anchor=tk.W)

        # Lista de arquivos
        cols = ("filename", "type", "size")
        self.local_tree = ttk.Treeview(self.tab_local, columns=cols, show='headings')
        for col, text, w in [
            ("filename", "Arquivo", 600),
            ("type", "Tipo", 80),
            ("size", "Tamanho", 120),
        ]:
            self.local_tree.heading(col, text=text)
            self.local_tree.column(col, width=w, anchor=tk.W)
        self.local_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

    def _select_local_files(self):
        """Seleciona arquivos PDF/XML individuais"""
        files = filedialog.askopenfilenames(
            title="Selecionar arquivos PDF ou XML",
            filetypes=[
                ("Arquivos de Nota Fiscal", "*.pdf *.xml"),
                ("PDF", "*.pdf"),
                ("XML", "*.xml"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if files:
            for f in files:
                if f not in self.local_files:
                    self.local_files.append(f)
            self._refresh_local_tree()

    def _select_local_folder(self):
        """Seleciona uma pasta e adiciona todos os PDF/XML"""
        folder = filedialog.askdirectory(title="Selecionar pasta com arquivos")
        if folder:
            count = 0
            for root, dirs, files in os.walk(folder):
                for fname in files:
                    if fname.lower().endswith(('.pdf', '.xml')):
                        fpath = os.path.join(root, fname)
                        if fpath not in self.local_files:
                            self.local_files.append(fpath)
                            count += 1
            self._refresh_local_tree()
            if count > 0:
                messagebox.showinfo("Pasta selecionada", f"{count} arquivo(s) adicionado(s)")

    def _clear_local_files(self):
        """Limpa a seleção de arquivos"""
        self.local_files.clear()
        self._refresh_local_tree()

    def _refresh_local_tree(self):
        """Atualiza a lista de arquivos selecionados"""
        self.local_tree.delete(*self.local_tree.get_children())
        for fpath in self.local_files:
            fname = os.path.basename(fpath)
            ftype = 'PDF' if fname.lower().endswith('.pdf') else 'XML'
            try:
                size = os.path.getsize(fpath)
                size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
            except Exception:
                size_str = "?"
            self.local_tree.insert('', tk.END, values=(fpath, ftype, size_str))
        self.local_count_var.set(f"Arquivos selecionados: {len(self.local_files)}")

    def _analyze_local_files(self):
        """Analisa os arquivos locais selecionados"""
        if not self.local_files:
            messagebox.showinfo("Análise Local", "Nenhum arquivo selecionado.")
            return

        # Verifica se já há extração em andamento
        if self._extraction_operation_running:
            messagebox.showwarning("Extração em andamento", "Já existe uma extração em execução. Aguarde a conclusão.")
            return

        # Reset progresso
        self.local_progress.configure(value=0, mode='determinate')
        self.local_status_var.set("Preparando análise...")
        self._cancel_local_analysis = False

        # Desabilita botões
        for b in (self.btn_analyze_local,):
            try:
                b.configure(state=tk.DISABLED)
            except Exception:
                pass
        try:
            self.btn_cancel_local.configure(state=tk.NORMAL)
        except Exception:
            pass

        def run():
            self._extraction_operation_running = True
            try:
                from modules.xml_pdf_extractor import extract_items_from_xml, extract_text_from_pdf, extract_items_from_pdf_via_llm

                all_items = []
                seen = set()
                total = len(self.local_files)
                skipped_pdfs = []  # PDFs que não puderam ser lidos

                for idx, fpath in enumerate(self.local_files, start=1):
                    # Verifica cancelamento
                    if self._cancel_local_analysis:
                        self.root.after(0, lambda: self.local_status_var.set("Análise cancelada"))
                        messagebox.showinfo("Análise Local", f"Análise cancelada. {new_items_count} itens foram processados antes do cancelamento.")
                        break
                    
                    fname = os.path.basename(fpath)
                    self.root.after(0, lambda f=fname, i=idx, t=total: (
                        self.local_status_var.set(f"Processando {i}/{t}: {f}"),
                        self.status_var.set(f"Analisando arquivo {i}/{t}")
                    ))

                    try:
                        if fpath.lower().endswith('.xml'):
                            items = extract_items_from_xml(fpath)
                        else:  # PDF
                            self.root.after(0, lambda: self.local_progress.configure(mode='indeterminate'))
                            self.root.after(0, lambda: self.local_progress.start(10))
                            
                            text = extract_text_from_pdf(fpath)
                            print(f"\n[LOCAL] Texto extraído de {fname}: {len(text) if text else 0} caracteres")
                            
                            if not text or len(text.strip()) < 50:
                                print(f"[LOCAL] PDF {fname} rejeitado: texto insuficiente (provavelmente imagem escaneada)")
                                skipped_pdfs.append(fname)
                                self.root.after(0, lambda f=fname: self.local_status_var.set(f"⚠️ PDF escaneado (sem texto): {f}"))
                                items = []
                            else:
                                print(f"[LOCAL] Enviando para LM Studio...")
                                try:
                                    items = extract_items_from_pdf_via_llm(
                                        text,
                                        self.cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234'),
                                        self.cfg.get('lmstudio', {}).get('model', 'openai/gpt-oss-20b')
                                    )
                                    print(f"[LOCAL] LM Studio retornou {len(items)} itens")
                                except Exception as e:
                                    error_msg = f"Erro ao extrair PDF {fname}: {str(e)}"
                                    print(f"[LOCAL] {error_msg}")
                                    self.root.after(0, lambda msg=error_msg: self.local_status_var.set(msg))
                                    items = []
                            
                            self.root.after(0, lambda: self.local_progress.stop())
                            self.root.after(0, lambda: self.local_progress.configure(mode='determinate'))

                        print(f"[LOCAL] Total de itens extraídos: {len(items)}")
                        for it in items:
                            it['documento'] = fname
                            # deduplicação
                            key = (
                                it.get('documento', ''),
                                it.get('descricao', '').strip().lower(),
                                round(float(it.get('quantidade', 0) or 0), 6),
                                round(float(it.get('valor_unit', 0) or 0), 6),
                                round(float(it.get('valor_total', 0) or 0), 6),
                            )
                            if key in seen:
                                continue
                            seen.add(key)
                            all_items.append(it)
                    except Exception as e:
                        error_msg = f"Erro ao processar {fname}: {str(e)}"
                        print(f"[LOCAL] {error_msg}")
                        self.root.after(0, lambda msg=error_msg: self.local_status_var.set(msg))

                    # Atualiza progresso
                    pct = int((idx / max(1, total)) * 100)
                    self.root.after(0, lambda p=pct: self.local_progress.configure(value=p))

                # Adiciona aos itens existentes com deduplicação global
                # Pega chaves já existentes
                existing_keys = set()
                for it in self.extracted_items:
                    key = (
                        it.get('documento', ''),
                        it.get('descricao', '').strip().lower(),
                        round(float(it.get('quantidade', 0) or 0), 6),
                        round(float(it.get('valor_unit', 0) or 0), 6),
                        round(float(it.get('valor_total', 0) or 0), 6),
                    )
                    existing_keys.add(key)
                
                # Adiciona apenas itens novos
                new_items_count = 0
                for it in all_items:
                    key = (
                        it.get('documento', ''),
                        it.get('descricao', '').strip().lower(),
                        round(float(it.get('quantidade', 0) or 0), 6),
                        round(float(it.get('valor_unit', 0) or 0), 6),
                        round(float(it.get('valor_total', 0) or 0), 6),
                    )
                    if key not in existing_keys:
                        self.extracted_items.append(it)
                        existing_keys.add(key)
                        new_items_count += 1
                
                self._refresh_items_tab()
                
                self.root.after(0, lambda: (
                    self.local_progress.configure(value=100),
                    self.local_status_var.set("Análise concluída."),
                    self.status_var.set("Análise local concluída")
                ))
                
                # Monta mensagem de resultado
                msg = f"Análise concluída.\n{new_items_count} itens novos adicionados de {total} arquivo(s)."
                if len(all_items) > new_items_count:
                    msg += f"\n{len(all_items) - new_items_count} itens duplicados foram ignorados."
                
                # Informa sobre PDFs que não puderam ser lidos
                if skipped_pdfs:
                    msg += f"\n\n⚠️ ATENÇÃO: {len(skipped_pdfs)} PDF(s) não puderam ser lidos:"
                    msg += "\n(Provavelmente são imagens escaneadas sem texto)"
                    msg += "\n\nArquivos ignorados:"
                    for pdf_name in skipped_pdfs[:5]:  # Mostra até 5
                        msg += f"\n  • {pdf_name}"
                    if len(skipped_pdfs) > 5:
                        msg += f"\n  ... e mais {len(skipped_pdfs) - 5}"
                    msg += "\n\nSugestão: Use ferramenta de OCR para converter esses PDFs em texto pesquisável."
                
                messagebox.showinfo("Análise Local", msg)
            except Exception as e:
                error_msg = f"Erro na análise: {str(e)}"
                messagebox.showerror("Erro na análise", error_msg)
                self.root.after(0, lambda: (
                    self.local_progress.configure(value=0),
                    self.local_status_var.set("Erro na análise")
                ))
            finally:
                self._extraction_operation_running = False
                self._cancel_local_analysis = False
                # Reabilita botões
                for b in (self.btn_analyze_local,):
                    try:
                        self.root.after(0, lambda bt=b: bt.configure(state=tk.NORMAL))
                    except Exception:
                        pass
                try:
                    self.root.after(0, lambda: self.btn_cancel_local.configure(state=tk.DISABLED))
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

    def _cancel_local_analysis_operation(self):
        """Cancela a operação de análise local em andamento"""
        self._cancel_local_analysis = True
        self.local_status_var.set("Cancelando análise...")
        self.status_var.set("Análise cancelada pelo usuário")

    # ---- Aba Itens ----
    def _build_tab_items(self):
        # Barra superior com resumo e ações principais
        top = ttk.Frame(self.tab_items)
        top.pack(fill=tk.X, padx=16, pady=12)
        self.items_summary_var = tk.StringVar(value="Itens: 0 | Valor total: 0.00")
        ttk.Label(top, textvariable=self.items_summary_var, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(top, text="📊 Resumo LLM", command=self._generate_llm_summary).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="🌐 Exportar HTML", command=self._export_items_html).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="🗑️ Limpar", command=self._clear_items).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="📄 CSV", command=self._export_items_csv).pack(side=tk.RIGHT)
        
        # Barra de ferramentas profissionais
        toolbar = ttk.Frame(self.tab_items)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 8))
        
        # Frame esquerdo - Busca e filtros
        left_tools = ttk.Frame(toolbar)
        left_tools.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_tools, text="🔍 Buscar:").pack(side=tk.LEFT, padx=(0, 4))
        self.items_search_var = tk.StringVar()
        self.items_search_var.trace('w', lambda *args: self._filter_items())
        search_entry = ttk.Entry(left_tools, textvariable=self.items_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(left_tools, text="🏷️ Por Fornecedor", command=self._group_by_supplier).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_tools, text="📦 Por Produto", command=self._group_by_product).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_tools, text="🔄 Ver Tudo", command=self._refresh_items_tab).pack(side=tk.LEFT, padx=2)
        
        # Frame direito - Análises rápidas
        right_tools = ttk.Frame(toolbar)
        right_tools.pack(side=tk.RIGHT)
        
        ttk.Button(right_tools, text="💰 Top 10 +Caros", command=self._show_top_expensive).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_tools, text="📈 Top 10 +Qtd", command=self._show_top_quantity).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_tools, text="📊 Estatísticas", command=self._show_quick_stats).pack(side=tk.LEFT, padx=2)
        ttk.Button(right_tools, text="🧩 Plugins", command=self._show_plugin_manager).pack(side=tk.LEFT, padx=2)

        # Tabela de itens
        cols = ("documento", "descricao", "quantidade", "valor_unit", "valor_total")
        self.items_tree = ttk.Treeview(self.tab_items, columns=cols, show='headings')
        for col, text, w in [
            ("documento", "Documento", 200),
            ("descricao", "Descrição", 420),
            ("quantidade", "Qtd", 80),
            ("valor_unit", "Unitário", 100),
            ("valor_total", "Total", 120),
        ]:
            self.items_tree.heading(col, text=text)
            self.items_tree.column(col, width=w, anchor=tk.W)
        
        # Adiciona scrollbar horizontal
        h_scroll = ttk.Scrollbar(self.tab_items, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(xscrollcommand=h_scroll.set)
        
        self.items_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 0))
        h_scroll.pack(fill=tk.X, padx=16, pady=(0, 16))

    def _refresh_items_tab(self):
        if not hasattr(self, 'items_tree'):
            return
        self.items_tree.delete(*self.items_tree.get_children())
        total = 0.0
        for it in self.extracted_items:
            total += float(it.get('valor_total', 0) or 0)
            self.items_tree.insert('', tk.END, values=(
                it.get('documento',''),
                it.get('descricao',''),
                it.get('quantidade',0),
                it.get('valor_unit',0),
                it.get('valor_total',0),
            ))
        self.items_summary_var.set(f"Itens: {len(self.extracted_items)} | Valor total: {total:.2f}")

    def _clear_items(self):
        """Limpa todos os itens extraídos"""
        if not self.extracted_items:
            messagebox.showinfo("Limpar Itens", "Não há itens para limpar.")
            return
        
        resp = messagebox.askyesno(
            "Limpar Itens",
            f"Tem certeza que deseja limpar todos os {len(self.extracted_items)} itens?\n\nEsta ação não pode ser desfeita."
        )
        if resp:
            self.extracted_items.clear()
            self._refresh_items_tab()
            messagebox.showinfo("Limpar Itens", "Todos os itens foram removidos.")
    
    def _export_items_csv(self):
        if not self.extracted_items:
            messagebox.showinfo("Exportar CSV", "Nenhum item para exportar.")
            return
        path = filedialog.asksaveasfilename(
            title="Salvar como",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="itens_nfe.csv"
        )
        if not path:
            return
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow(["documento", "descricao", "quantidade", "valor_unit", "valor_total"])
                for it in self.extracted_items:
                    w.writerow([
                        it.get('documento',''),
                        it.get('descricao',''),
                        it.get('quantidade',0),
                        it.get('valor_unit',0),
                        it.get('valor_total',0),
                    ])
            messagebox.showinfo("Exportar CSV", f"Arquivo salvo em:\n{path}")
        except Exception as e:
            messagebox.showerror("Exportar CSV", str(e))

    # ---------- Visualização de emails ----------
    def _open_email_viewer(self, uid: str):
        # Verifica se já há operação de email em andamento
        if self._email_operation_running:
            messagebox.showwarning("Operação em andamento", "Já existe uma operação de email em execução. Aguarde a conclusão.")
            return
            
        def run():
            self._email_operation_running = True
            try:
                client = self._get_client()
                data = client.fetch_email(uid)
                self.root.after(0, lambda d=data: self._show_email_window(d))
            except Exception as ex:
                error_msg = f"Erro ao buscar email:\n{str(ex)}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Abrir Email", msg))
            finally:
                self._email_operation_running = False
        threading.Thread(target=run, daemon=True).start()

    def _show_email_window(self, data: dict):
        try:
            from ui.email_viewer import EmailViewer
            EmailViewer(self.root, data, on_download=self._download_attachments_for_email)
        except Exception as e:
            # Fallback: janela simples de texto
            try:
                self._show_email_window_fallback(data)
            except Exception as e2:
                error_msg = f"Erro ao abrir visualizador:\n{str(e)}\n{str(e2)}"
                messagebox.showerror("Erro", error_msg)

    def _show_email_window_fallback(self, data: dict):
        win = tk.Toplevel(self.root)
        win.title("Email")
        win.geometry("800x600")

        header = ttk.Frame(win)
        header.pack(fill=tk.X, padx=12, pady=8)
        ttk.Label(header, text=f"Assunto: {data.get('subject','')}", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text=f"De: {data.get('from','')}").pack(anchor=tk.W)
        ttk.Label(header, text=f"Data: {data.get('date','')}").pack(anchor=tk.W)

        body_frame = ttk.Frame(win)
        body_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        txt = tk.Text(body_frame, wrap='word')
        txt.insert('1.0', data.get('body_text', ''))
        txt.configure(state='disabled')
        txt.pack(fill=tk.BOTH, expand=True)

        attach = data.get('attachments') or []
        if attach:
            att_frame = ttk.Frame(win)
            att_frame.pack(fill=tk.X, padx=12, pady=8)
            ttk.Label(att_frame, text="Anexos:").pack(anchor=tk.W)
            for a in attach:
                ttk.Label(att_frame, text=f"• {a['filename']} ({a['content_type']})").pack(anchor=tk.W)

    def _on_open_selected_from_conn(self, _):
        sel = self.conn_tree.selection()
        if not sel:
            return
        iid = sel[0]
        uid = self._item_uid.get(iid)
        if uid:
            self._open_email_viewer(uid)

    def _on_open_selected_from_results(self, _):
        sel = self.results_tree.selection()
        if not sel:
            return
        iid = sel[0]
        uid = self._item_uid.get(iid)
        if uid:
            self._open_email_viewer(uid)

    # ---------- Download de anexos ----------
    def _download_attachments_for_email(self, email_data: dict):
        """Permite escolher um diretório e baixa todos os anexos do email exibido."""
        attachments = email_data.get('attachments') or []
        uid = str(email_data.get('uid') or '')
        if not attachments or not uid:
            messagebox.showinfo("Anexos", "Este email não possui anexos para baixar.")
            return
        dest = filedialog.askdirectory(title="Escolher pasta para salvar anexos")
        if not dest:
            return

        # Monta selections no formato esperado por GmailClient.download_attachments
        def _guess_type(filename: str) -> str:
            fn = (filename or '').lower()
            if fn.endswith('.pdf'):
                return 'PDF'
            if fn.endswith('.xml'):
                return 'XML'
            return ''

        selections = [{
            'uid': uid,
            'filename': a.get('filename', ''),
            'type': _guess_type(a.get('filename', ''))
        } for a in attachments if a.get('filename')]

        if not selections:
            messagebox.showinfo("Anexos", "Não foi possível identificar os anexos deste email.")
            return

        # Executa em thread para não travar UI
        def run():
            try:
                client = self._get_client()
                total = len({s['uid'] for s in selections})
                def cb(i, t):
                    self.status_var.set(f"Baixando anexos ({i}/{t})...")
                downloaded = client.download_attachments(selections, dest, progress_cb=cb)
                self.root.after(0, lambda: messagebox.showinfo(
                    "Anexos",
                    f"Baixados {len(downloaded)} arquivo(s) em:\n{dest}"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro ao baixar anexos", str(e)))
            finally:
                self.root.after(0, lambda: self.status_var.set("Pronto"))

        threading.Thread(target=run, daemon=True).start()
    def on_save_config(self):
        self.cfg['email']['server'] = self.cfg_server.get().strip() or 'imap.gmail.com'
        self.cfg['email']['port'] = int(self.cfg_port.get() or 993)
        self.cfg['email']['address'] = self.cfg_address.get().strip()
        
        # Remove espaços da senha (erro comum)
        password = self.cfg_password.get().strip().replace(' ', '')
        if password and len(password) != 16:
            resp = messagebox.askyesno(
                "Senha de App",
                f"A senha de app do Gmail geralmente tem 16 caracteres, mas você digitou {len(password)}.\n\n"
                "Continuar mesmo assim?"
            )
            if not resp:
                return
        
        self.cfg['email']['app_password'] = password

        self.cfg['search']['include_keywords'] = [s.strip() for s in self.cfg_include.get().split(',') if s.strip()]
        self.cfg['search']['exclude_keywords'] = [s.strip() for s in self.cfg_exclude.get().split(',') if s.strip()]

        # LM Studio
        self.cfg.setdefault('lmstudio', {})
        self.cfg['lmstudio']['url'] = self.cfg_lm_url.get().strip() or 'http://127.0.0.1:1234'
        self.cfg['lmstudio']['model'] = self.cfg_lm_model.get().strip() or 'openai/gpt-oss-20b'

        persist = self.persist_config_var.get()
        if save_config(self.cfg, persist=persist):
            if persist:
                messagebox.showinfo("Configurações", "Configurações salvas no disco!")
            else:
                messagebox.showinfo("Configurações", "Configurações salvas apenas na memória (serão perdidas ao fechar)!")
            # reset client
            self.gmail = None
    
    def _init_monitors(self):
        """Inicializa os monitores de LLM e emails"""
        try:
            # Monitor de status LLM
            llm_url = self.cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234')
            self.llm_monitor = get_llm_monitor(llm_url, check_interval=15)
            
            # Callback para atualizar UI quando status mudar
            def on_llm_status_change(is_available, message):
                try:
                    # Atualiza status nas abas
                    if hasattr(self, 'extract_llm_status_var'):
                        self.root.after(0, lambda: self.extract_llm_status_var.set(message))
                    if hasattr(self, 'local_llm_status_var'):
                        self.root.after(0, lambda: self.local_llm_status_var.set(message))
                except Exception as e:
                    print(f"Erro atualizando status LLM na UI: {e}")
            
            # Inicia monitoramento
            self.llm_monitor.start_monitoring(on_llm_status_change)
            
            # Inicializa analisador LLM
            llm_model = self.cfg.get('lmstudio', {}).get('model', 'qwen/qwen3-vl-4b')
            self.llm_analyzer = LLMAnalyzer(llm_url, llm_model, max_tokens_per_request=5000)
            
            # Monitor de emails (inicia apenas se conectado)
            self._start_email_monitoring()
            
        except Exception as e:
            print(f"Erro ao inicializar monitores: {e}")
    
    def _start_email_monitoring(self):
        """Inicia monitoramento de novos emails"""
        try:
            # Só inicia se tiver credenciais
            email = self.cfg.get('email', {}).get('address', '')
            password = self.cfg.get('email', {}).get('app_password', '')
            
            if not email or not password:
                return
            
            # Inicializa monitor de emails
            self.email_monitor = EmailMonitor(email, password, check_interval=300)
            
            # Callback para quando novos emails chegarem
            def on_new_emails():
                try:
                    print("Novos emails detectados!")
                    # Atualiza lista se estiver na aba de conexão
                    if hasattr(self, 'nb') and self.nb.select() == self.nb.tabs()[0]:
                        self.root.after(0, self.on_connect_and_list)
                    # Mostra notificação
                    self.root.after(0, lambda: self.status_var.set("✉ Novos emails recebidos!"))
                except Exception as e:
                    print(f"Erro processando novos emails: {e}")
            
            # Inicia monitoramento
            self.email_monitor.start_monitoring(on_new_emails)
            print("Monitor de emails iniciado")
            
        except Exception as e:
            print(f"Erro ao iniciar monitor de emails: {e}")
    
    def _generate_llm_summary(self):
        """Gera resumo inteligente dos itens usando LLM"""
        if not self.extracted_items:
            messagebox.showinfo("Resumo LLM", "Não há itens para analisar.")
            return
        
        if not self.llm_analyzer:
            messagebox.showerror("Erro", "Analisador LLM não inicializado.")
            return
        
        # Verifica se LLM está disponível
        if self.llm_monitor:
            is_available, _ = self.llm_monitor.check_status()
            if not is_available:
                resp = messagebox.askyesno(
                    "LLM Offline",
                    "A LLM parece estar offline. Deseja tentar mesmo assim?"
                )
                if not resp:
                    return
        
        # Janela para instruções personalizadas
        instruction_window = tk.Toplevel(self.root)
        instruction_window.title("Instruções para LLM")
        instruction_window.geometry("650x550")
        instruction_window.minsize(600, 500)
        instruction_window.transient(self.root)
        instruction_window.grab_set()
        
        # Container principal com scroll se necessário
        main_container = ttk.Frame(instruction_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_container, text="💡 Instruções Personalizadas (Opcional)", 
                 font=('Segoe UI', 11, 'bold')).pack(pady=(0, 10))
        
        ttk.Label(main_container, 
                 text="Forneça instruções específicas para a análise.\nExemplos: 'Foque em materiais de escritório', 'Identifique oportunidades de economia'",
                 justify=tk.LEFT).pack(pady=(0, 10))
        
        # Frame com exemplos rápidos
        examples_frame = ttk.LabelFrame(main_container, text="Exemplos Rápidos", padding=10)
        examples_frame.pack(fill=tk.X, pady=(0, 10))
        
        custom_instruction = tk.StringVar()
        
        # Frame para área de texto com label
        text_frame = ttk.LabelFrame(main_container, text="Digite sua instrução personalizada:", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        instruction_text = tk.Text(text_frame, height=6, wrap=tk.WORD, font=('Segoe UI', 10))
        instruction_text.pack(fill=tk.BOTH, expand=True)
        
        def set_example(text):
            instruction_text.delete('1.0', tk.END)
            instruction_text.insert('1.0', text)
        
        examples = [
            ("📊 Gestão de Compras", "Identifique os produtos mais comprados, fornecedores principais e oportunidades de negociação em lote para redução de custos."),
            ("📦 Controle de Estoque", "Analise padrões de consumo, sugira níveis ideais de estoque e identifique produtos com alto giro."),
            ("💰 Redução de Custos", "Encontre produtos com preços variados entre fornecedores e sugira possíveis economias."),
            ("📈 Tendências", "Identifique tendências de compra ao longo do tempo e produtos em crescimento."),
        ]
        
        for i, (label, instruction) in enumerate(examples):
            ttk.Button(examples_frame, text=label, 
                      command=lambda i=instruction: set_example(i),
                      width=22).grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.EW)
        
        examples_frame.columnconfigure(0, weight=1)
        examples_frame.columnconfigure(1, weight=1)
        
        # Botões de ação - agora fixos na parte inferior
        btn_frame = ttk.Frame(instruction_window)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
        
        user_instruction = None
        
        def on_continue():
            nonlocal user_instruction
            user_instruction = instruction_text.get('1.0', tk.END).strip()
            instruction_window.destroy()
            self._run_llm_analysis(user_instruction)
        
        def on_skip():
            instruction_window.destroy()
            self._run_llm_analysis(None)
        
        ttk.Button(btn_frame, text="▶ Continuar com Instruções", command=on_continue).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏭ Pular (Análise Padrão)", command=on_skip).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=instruction_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _run_llm_analysis(self, custom_instruction=None):
        """Executa análise LLM com instruções opcionais"""
        # Cria janela de progresso
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Gerando Resumo LLM")
        progress_window.geometry("500x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="Analisando itens com LLM...").pack(pady=20)
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start(10)
        
        status_var = tk.StringVar(value="Preparando análise...")
        ttk.Label(progress_window, textvariable=status_var).pack(pady=10)
        
        cancel_requested = False
        
        def on_cancel():
            nonlocal cancel_requested
            cancel_requested = True
            status_var.set("Cancelando...")
        
        ttk.Button(progress_window, text="Cancelar", command=on_cancel).pack(pady=10)
        
        def run_analysis():
            try:
                status_var.set("Enviando para LLM...")
                
                # Analisa itens com instrução personalizada
                result = self.llm_analyzer.analyze_items(
                    self.extracted_items,
                    cancel_check=lambda: cancel_requested,
                    custom_instruction=custom_instruction
                )
                
                if cancel_requested:
                    self.root.after(0, progress_window.destroy)
                    return
                
                if not result or 'erro' in result:
                    erro = result.get('erro', 'Erro desconhecido') if result else 'Erro desconhecido'
                    self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao gerar resumo: {erro}"))
                    self.root.after(0, progress_window.destroy)
                    return
                
                # Mostra resultado
                self.root.after(0, lambda: self._show_llm_summary(result))
                self.root.after(0, progress_window.destroy)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao gerar resumo: {str(e)}"))
                self.root.after(0, progress_window.destroy)
        
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def _show_llm_summary(self, analysis):
        """Mostra janela com o resumo LLM"""
        window = tk.Toplevel(self.root)
        window.title("Resumo Inteligente - LLM")
        window.geometry("900x650")
        
        # Frame com estatísticas
        stats_frame = ttk.LabelFrame(window, text="📊 Estatísticas Calculadas", padding=15)
        stats_frame.pack(fill=tk.X, padx=15, pady=10)
        
        stats = analysis.get('estatisticas', {})
        
        # Grid com estatísticas formatadas
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)
        
        # Coluna 1
        col1 = ttk.Frame(stats_container)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(col1, text="Total de itens:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(col1, text=f"{stats.get('total_itens', 0)}", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(col1, text="Tipos diferentes:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(col1, text=f"{stats.get('tipos_diferentes', 0)}", font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # Coluna 2
        col2 = ttk.Frame(stats_container)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(col2, text="Valor total:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(col2, text=f"R$ {stats.get('valor_total', 0):,.2f}", 
                 font=('Segoe UI', 10), foreground='#667eea').pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(col2, text="Valor médio por item:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(col2, text=f"R$ {stats.get('valor_medio_por_item', 0):,.2f}", 
                 font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # Frame com resumo LLM - formatado
        resumo_frame = ttk.LabelFrame(window, text="🤖 Análise Inteligente da LLM", padding=15)
        resumo_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Scrollbar
        scroll = ttk.Scrollbar(resumo_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget com formatação
        text_widget = tk.Text(resumo_frame, wrap=tk.WORD, height=20, 
                            font=('Segoe UI', 10), yscrollcommand=scroll.set,
                            padx=10, pady=10, spacing1=2, spacing2=2, spacing3=4)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=text_widget.yview)
        
        # Configura tags para formatação
        text_widget.tag_config('heading2', font=('Segoe UI', 12, 'bold'), foreground='#667eea', spacing1=15, spacing3=8)
        text_widget.tag_config('heading3', font=('Segoe UI', 11, 'bold'), foreground='#764ba2', spacing1=12, spacing3=6)
        text_widget.tag_config('bold', font=('Segoe UI', 10, 'bold'), foreground='#667eea')
        text_widget.tag_config('normal', font=('Segoe UI', 10))
        text_widget.tag_config('list_item', font=('Segoe UI', 10), lmargin1=20, lmargin2=40)
        
        # Processa e insere o resumo com formatação
        resumo = analysis.get('resumo_llm', 'Nenhum resumo disponível')
        self._insert_formatted_text(text_widget, resumo)
        
        text_widget.configure(state='disabled')
        
        # Botões de ação
        btn_frame = ttk.Frame(window)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def export_with_summary():
            """Exporta HTML incluindo o resumo LLM"""
            try:
                filepath = filedialog.asksaveasfilename(
                    title="Salvar relatório HTML com resumo",
                    defaultextension=".html",
                    filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")]
                )
                
                if filepath:
                    # Exporta com resumo
                    success = HTMLExporter.export_items(
                        analysis.get('itens_agregados', self.extracted_items),
                        filepath,
                        estatisticas=stats,
                        resumo_llm=resumo
                    )
                    
                    if success:
                        messagebox.showinfo("Exportação", f"Relatório exportado com sucesso!\n{filepath}")
                        # Pergunta se quer abrir
                        resp = messagebox.askyesno("Abrir arquivo", "Deseja abrir o relatório agora?")
                        if resp:
                            import webbrowser
                            webbrowser.open(filepath)
                    else:
                        messagebox.showerror("Erro", "Falha ao exportar relatório.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
        
        ttk.Button(btn_frame, text="💾 Exportar HTML com Resumo", command=export_with_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✖ Fechar", command=window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _insert_formatted_text(self, text_widget, content):
        """Insere texto formatado no widget Text com tags"""
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                text_widget.insert(tk.END, '\n')
                continue
            
            # Título nível 2 (##)
            if stripped.startswith('## '):
                text = stripped[3:].strip()
                text_widget.insert(tk.END, text + '\n', 'heading2')
            
            # Título nível 3 (###)
            elif stripped.startswith('### '):
                text = stripped[4:].strip()
                text_widget.insert(tk.END, text + '\n', 'heading3')
            
            # Item de lista
            elif stripped.startswith('- '):
                text = '• ' + stripped[2:].strip()
                # Processa negrito dentro do item
                self._insert_line_with_bold(text_widget, text, 'list_item')
                text_widget.insert(tk.END, '\n')
            
            # Linha normal
            else:
                self._insert_line_with_bold(text_widget, stripped, 'normal')
                text_widget.insert(tk.END, '\n')
    
    def _insert_line_with_bold(self, text_widget, line, default_tag):
        """Insere linha processando **negrito**"""
        import re
        
        # Encontra padrões **texto**
        parts = re.split(r'(\*\*.+?\*\*)', line)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Remove ** e insere com tag bold
                text_widget.insert(tk.END, part[2:-2], 'bold')
            elif part:
                text_widget.insert(tk.END, part, default_tag)
    
    def _filter_items(self):
        """Filtra itens baseado na busca"""
        search_term = self.items_search_var.get().lower().strip()
        
        if not search_term:
            self._refresh_items_tab()
            return
        
        self.items_tree.delete(*self.items_tree.get_children())
        total = 0.0
        count = 0
        
        for it in self.extracted_items:
            # Busca em múltiplos campos
            if (search_term in it.get('descricao', '').lower() or
                search_term in it.get('documento', '').lower() or
                search_term in it.get('codigo', '').lower()):
                
                total += float(it.get('valor_total', 0) or 0)
                count += 1
                self.items_tree.insert('', tk.END, values=(
                    it.get('documento',''),
                    it.get('descricao',''),
                    it.get('quantidade',0),
                    it.get('valor_unit',0),
                    it.get('valor_total',0),
                ))
        
        self.items_summary_var.set(f"Filtrados: {count}/{len(self.extracted_items)} itens | Valor: {total:.2f}")
    
    def _group_by_supplier(self):
        """Agrupa itens por fornecedor (documento)"""
        if not self.extracted_items:
            return
        
        from collections import defaultdict
        suppliers = defaultdict(lambda: {'items': [], 'total': 0.0})
        
        for it in self.extracted_items:
            doc = it.get('documento', 'Sem documento')
            suppliers[doc]['items'].append(it)
            suppliers[doc]['total'] += float(it.get('valor_total', 0) or 0)
        
        # Cria janela com agrupamento
        window = tk.Toplevel(self.root)
        window.title("📊 Agrupamento por Fornecedor")
        window.geometry("900x600")
        
        # Lista de fornecedores
        left_frame = ttk.Frame(window)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(left_frame, text="Fornecedores (Clique para ver itens)", 
                 font=('Segoe UI', 10, 'bold')).pack(pady=5)
        
        supplier_list = tk.Listbox(left_frame, font=('Consolas', 9))
        supplier_list.pack(fill=tk.BOTH, expand=True)
        
        # Preenche lista ordenada por valor
        sorted_suppliers = sorted(suppliers.items(), key=lambda x: x[1]['total'], reverse=True)
        for doc, data in sorted_suppliers:
            supplier_list.insert(tk.END, f"{doc[:40]:40} R$ {data['total']:>12,.2f}  ({len(data['items'])} itens)")
        
        # Detalhes do fornecedor selecionado
        right_frame = ttk.Frame(window)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(right_frame, text="Itens do Fornecedor", 
                 font=('Segoe UI', 10, 'bold')).pack(pady=5)
        
        detail_tree = ttk.Treeview(right_frame, columns=("desc", "qtd", "valor"), show='headings')
        detail_tree.heading("desc", text="Descrição")
        detail_tree.heading("qtd", text="Qtd")
        detail_tree.heading("valor", text="Valor Total")
        detail_tree.column("desc", width=300)
        detail_tree.column("qtd", width=80)
        detail_tree.column("valor", width=100)
        detail_tree.pack(fill=tk.BOTH, expand=True)
        
        def on_supplier_select(event):
            selection = supplier_list.curselection()
            if not selection:
                return
            
            doc, data = sorted_suppliers[selection[0]]
            detail_tree.delete(*detail_tree.get_children())
            
            for item in data['items']:
                detail_tree.insert('', tk.END, values=(
                    item.get('descricao', '')[:50],
                    item.get('quantidade', 0),
                    f"R$ {item.get('valor_total', 0):.2f}"
                ))
        
        supplier_list.bind('<<ListboxSelect>>', on_supplier_select)
    
    def _group_by_product(self):
        """Agrupa itens por produto (descrição)"""
        if not self.extracted_items:
            return
        
        from collections import defaultdict
        products = defaultdict(lambda: {'quantidade': 0, 'valor_total': 0.0, 'docs': set()})
        
        for it in self.extracted_items:
            desc = it.get('descricao', 'Sem descrição').strip().lower()
            products[desc]['quantidade'] += float(it.get('quantidade', 0) or 0)
            products[desc]['valor_total'] += float(it.get('valor_total', 0) or 0)
            products[desc]['docs'].add(it.get('documento', ''))
        
        # Janela com produtos agrupados
        window = tk.Toplevel(self.root)
        window.title("📦 Agrupamento por Produto")
        window.geometry("900x600")
        
        ttk.Label(window, text="Produtos Consolidados (Itens Idênticos Somados)", 
                 font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=("produto", "qtd", "valor", "fornecedores"), show='headings')
        tree.heading("produto", text="Produto")
        tree.heading("qtd", text="Quantidade Total")
        tree.heading("valor", text="Valor Total")
        tree.heading("fornecedores", text="Nº Fornecedores")
        
        tree.column("produto", width=450)
        tree.column("qtd", width=120)
        tree.column("valor", width=120)
        tree.column("fornecedores", width=120)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Preenche ordenado por valor
        sorted_products = sorted(products.items(), key=lambda x: x[1]['valor_total'], reverse=True)
        for desc, data in sorted_products:
            tree.insert('', tk.END, values=(
                desc.capitalize()[:60],
                f"{data['quantidade']:.2f}",
                f"R$ {data['valor_total']:.2f}",
                len(data['docs'])
            ))
    
    def _show_top_expensive(self):
        """Mostra os 10 itens mais caros"""
        if not self.extracted_items:
            return
        
        sorted_items = sorted(self.extracted_items, 
                            key=lambda x: float(x.get('valor_total', 0) or 0), 
                            reverse=True)[:10]
        
        window = tk.Toplevel(self.root)
        window.title("💰 Top 10 Itens Mais Caros")
        window.geometry("800x500")
        
        ttk.Label(window, text="🏆 Top 10 Itens Mais Caros", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=("rank", "desc", "qtd", "unit", "total", "doc"), show='headings')
        tree.heading("rank", text="#")
        tree.heading("desc", text="Descrição")
        tree.heading("qtd", text="Qtd")
        tree.heading("unit", text="Unitário")
        tree.heading("total", text="Total")
        tree.heading("doc", text="Documento")
        
        tree.column("rank", width=40)
        tree.column("desc", width=300)
        tree.column("qtd", width=70)
        tree.column("unit", width=90)
        tree.column("total", width=100)
        tree.column("doc", width=150)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, item in enumerate(sorted_items, 1):
            tree.insert('', tk.END, values=(
                f"#{i}",
                item.get('descricao', '')[:45],
                item.get('quantidade', 0),
                f"R$ {item.get('valor_unit', 0):.2f}",
                f"R$ {item.get('valor_total', 0):.2f}",
                item.get('documento', '')[:25]
            ))
    
    def _show_top_quantity(self):
        """Mostra os 10 itens com maior quantidade"""
        if not self.extracted_items:
            return
        
        sorted_items = sorted(self.extracted_items, 
                            key=lambda x: float(x.get('quantidade', 0) or 0), 
                            reverse=True)[:10]
        
        window = tk.Toplevel(self.root)
        window.title("📈 Top 10 Itens com Maior Quantidade")
        window.geometry("800x500")
        
        ttk.Label(window, text="🏆 Top 10 Itens com Maior Quantidade", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=("rank", "desc", "qtd", "unit", "total", "doc"), show='headings')
        tree.heading("rank", text="#")
        tree.heading("desc", text="Descrição")
        tree.heading("qtd", text="Quantidade")
        tree.heading("unit", text="Unitário")
        tree.heading("total", text="Total")
        tree.heading("doc", text="Documento")
        
        tree.column("rank", width=40)
        tree.column("desc", width=300)
        tree.column("qtd", width=100)
        tree.column("unit", width=90)
        tree.column("total", width=100)
        tree.column("doc", width=150)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, item in enumerate(sorted_items, 1):
            tree.insert('', tk.END, values=(
                f"#{i}",
                item.get('descricao', '')[:45],
                f"{item.get('quantidade', 0):.2f}",
                f"R$ {item.get('valor_unit', 0):.2f}",
                f"R$ {item.get('valor_total', 0):.2f}",
                item.get('documento', '')[:25]
            ))
    
    def _show_quick_stats(self):
        """Mostra estatísticas rápidas dos itens"""
        if not self.extracted_items:
            messagebox.showinfo("Estatísticas", "Não há itens para analisar.")
            return
        
        # Calcula estatísticas
        total_items = len(self.extracted_items)
        total_qtd = sum(float(it.get('quantidade', 0) or 0) for it in self.extracted_items)
        total_valor = sum(float(it.get('valor_total', 0) or 0) for it in self.extracted_items)
        
        # Itens únicos por descrição
        unique_products = len(set(it.get('descricao', '').lower().strip() for it in self.extracted_items))
        
        # Fornecedores únicos
        unique_suppliers = len(set(it.get('documento', '') for it in self.extracted_items))
        
        # Valor médio
        avg_valor = total_valor / total_items if total_items > 0 else 0
        avg_qtd = total_qtd / total_items if total_items > 0 else 0
        
        # Item mais caro e mais barato
        sorted_by_value = sorted(self.extracted_items, key=lambda x: float(x.get('valor_total', 0) or 0))
        most_expensive = sorted_by_value[-1] if sorted_by_value else {}
        cheapest = sorted_by_value[0] if sorted_by_value else {}
        
        # Janela com estatísticas
        window = tk.Toplevel(self.root)
        window.title("📊 Estatísticas Rápidas")
        window.geometry("600x500")
        
        ttk.Label(window, text="📊 Análise Rápida de Itens", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        # Frame com cards de estatísticas
        stats_frame = ttk.Frame(window)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        stats_text = f"""
═══════════════════════════════════════════════════════════

📦 RESUMO GERAL
   • Total de registros: {total_items}
   • Produtos únicos: {unique_products}
   • Fornecedores diferentes: {unique_suppliers}

💰 VALORES
   • Valor total: R$ {total_valor:,.2f}
   • Valor médio por item: R$ {avg_valor:,.2f}
   • Item mais caro: R$ {float(most_expensive.get('valor_total', 0)):,.2f}
     └─ {most_expensive.get('descricao', 'N/A')[:40]}
   • Item mais barato: R$ {float(cheapest.get('valor_total', 0)):,.2f}
     └─ {cheapest.get('descricao', 'N/A')[:40]}

📊 QUANTIDADES
   • Quantidade total: {total_qtd:,.2f}
   • Quantidade média: {avg_qtd:,.2f}

═══════════════════════════════════════════════════════════
        """
        
        text_widget = tk.Text(stats_frame, wrap=tk.WORD, font=('Consolas', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', stats_text)
        text_widget.configure(state='disabled')
        
        ttk.Button(window, text="Fechar", command=window.destroy).pack(pady=10)
    
    def _export_items_html(self):
        """Exporta itens para HTML"""
        if not self.extracted_items:
            messagebox.showinfo("Exportação HTML", "Não há itens para exportar.")
            return
        
        try:
            filepath = filedialog.asksaveasfilename(
                title="Salvar relatório HTML",
                defaultextension=".html",
                filetypes=[("HTML", "*.html"), ("Todos os arquivos", "*.*")]
            )
            
            if filepath:
                success = HTMLExporter.export_items(self.extracted_items, filepath)
                
                if success:
                    messagebox.showinfo("Exportação", f"Relatório HTML exportado com sucesso!\n{filepath}")
                    # Pergunta se quer abrir
                    resp = messagebox.askyesno("Abrir arquivo", "Deseja abrir o arquivo agora?")
                    if resp:
                        import webbrowser
                        webbrowser.open(filepath)
                else:
                    messagebox.showerror("Erro", "Falha ao exportar relatório HTML.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar HTML: {str(e)}")

    def _show_plugin_manager(self):
        """Mostra janela de gerenciamento de plugins"""
        window = tk.Toplevel(self.root)
        window.title("Gerenciador de Plugins")
        window.geometry("800x600")
        window.minsize(700, 500)
        
        # Frame superior - info e ações
        top_frame = ttk.Frame(window)
        top_frame.pack(fill=tk.X, padx=15, pady=12)
        
        ttk.Label(top_frame, text="🧩 Plugins Disponíveis", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="🔄 Atualizar Lista", command=lambda: self._refresh_plugin_list(tree)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="📖 Guia de Desenvolvimento", command=self._show_plugin_dev_guide).pack(side=tk.RIGHT)
        
        # Lista de plugins
        list_frame = ttk.LabelFrame(window, text="Plugins", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        cols = ("status", "name", "version", "author", "description")
        tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=12)
        
        tree.heading("status", text="Status")
        tree.heading("name", text="Nome")
        tree.heading("version", text="Versão")
        tree.heading("author", text="Autor")
        tree.heading("description", text="Descrição")
        
        tree.column("status", width=80, anchor=tk.CENTER)
        tree.column("name", width=150)
        tree.column("version", width=60, anchor=tk.CENTER)
        tree.column("author", width=150)
        tree.column("description", width=300)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botões de ação
        btn_frame = ttk.Frame(window)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def toggle_plugin():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Plugins", "Selecione um plugin primeiro.")
                return
            
            item = tree.item(selection[0])
            values = item['values']
            status = values[0]
            plugin_name = values[1]
            
            # Busca o arquivo do plugin
            discovered = self.plugin_manager.discover_plugins()
            plugin_file = None
            for p in discovered:
                if p['name'] == plugin_name:
                    plugin_file = p['file']
                    break
            
            if not plugin_file:
                messagebox.showerror("Erro", "Plugin não encontrado.")
                return
            
            plugin_stem = Path(plugin_file).stem
            
            if status == "❌ Desabilitado":
                # Carregar plugin
                app_context = {
                    'app': self,
                    'extracted_items': self.extracted_items,
                    'config': self.cfg
                }
                
                if self.plugin_manager.load_plugin(plugin_file, app_context):
                    messagebox.showinfo("Plugins", f"Plugin '{plugin_name}' carregado com sucesso!")
                    self._refresh_plugin_list(tree)
                else:
                    messagebox.showerror("Erro", f"Falha ao carregar plugin '{plugin_name}'.")
            else:
                # Descarregar plugin
                if self.plugin_manager.unload_plugin(plugin_stem):
                    messagebox.showinfo("Plugins", f"Plugin '{plugin_name}' descarregado.")
                    self._refresh_plugin_list(tree)
                else:
                    messagebox.showerror("Erro", f"Falha ao descarregar plugin '{plugin_name}'.")
        
        def execute_plugin():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Plugins", "Selecione um plugin primeiro.")
                return
            
            item = tree.item(selection[0])
            values = item['values']
            status = values[0]
            plugin_name = values[1]
            
            if status == "❌ Desabilitado":
                messagebox.showwarning("Plugins", f"Plugin '{plugin_name}' está desabilitado. Habilite-o primeiro.")
                return
            
            # Busca o plugin carregado
            discovered = self.plugin_manager.discover_plugins()
            plugin_file = None
            for p in discovered:
                if p['name'] == plugin_name:
                    plugin_file = p['file']
                    break
            
            if not plugin_file:
                messagebox.showerror("Erro", "Plugin não encontrado.")
                return
            
            plugin_stem = Path(plugin_file).stem
            
            # Executa o plugin
            result = self.plugin_manager.execute_plugin(
                plugin_stem,
                items=self.extracted_items,
                config=self.cfg
            )
            
            if isinstance(result, dict) and 'success' in result:
                if result['success']:
                    if 'message' in result:
                        messagebox.showinfo("Plugin", result['message'])
                else:
                    messagebox.showerror("Plugin", result.get('message', 'Erro desconhecido'))
        
        ttk.Button(btn_frame, text="✅ Habilitar / ❌ Desabilitar", command=toggle_plugin).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="▶️ Executar Plugin", command=execute_plugin).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✖ Fechar", command=window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Carrega lista inicial
        self._refresh_plugin_list(tree)
    
    def _refresh_plugin_list(self, tree):
        """Atualiza lista de plugins na UI"""
        tree.delete(*tree.get_children())
        
        discovered = self.plugin_manager.discover_plugins()
        
        for plugin in discovered:
            status = "✅ Habilitado" if plugin['enabled'] else "❌ Desabilitado"
            tree.insert('', tk.END, values=(
                status,
                plugin['name'],
                plugin['version'],
                plugin['author'],
                plugin['description']
            ))
        
        if not discovered:
            tree.insert('', tk.END, values=(
                "ℹ️",
                "Nenhum plugin encontrado",
                "-",
                "-",
                "Coloque arquivos .py na pasta 'plugins/'"
            ))
    
    def _show_plugin_dev_guide(self):
        """Abre guia de desenvolvimento de plugins"""
        guide_path = Path("PLUGIN_DEV_GUIDE.md")
        
        if guide_path.exists():
            import webbrowser
            webbrowser.open(str(guide_path.absolute()))
        else:
            messagebox.showinfo(
                "Guia de Plugins",
                "Arquivo PLUGIN_DEV_GUIDE.md não encontrado.\n\n"
                "Consulte a pasta 'plugins/' para ver exemplos de plugins."
            )

    def _on_closing(self):
        """Chamado ao fechar o programa - salva configurações se persist ativo"""
        try:
            # Para monitores
            if self.llm_monitor:
                self.llm_monitor.stop_monitoring()
            if self.email_monitor:
                self.email_monitor.stop_monitoring()
            
            # Só persiste se checkbox estiver marcado
            if hasattr(self, 'persist_config_var') and self.persist_config_var.get():
                save_config(self.cfg, persist=True)
        except Exception:
            pass
        finally:
            self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    # tema escuro profissional
    try:
        from ui.theme import setup_theme
        setup_theme(root)
    except Exception:
        pass
    app = SimpleNFEApp(root)
    root.mainloop()
