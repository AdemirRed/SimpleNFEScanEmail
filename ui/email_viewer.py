import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import webbrowser
from urllib.parse import quote
from typing import Dict, Optional, Callable


class EmailViewer(tk.Toplevel):
    """Janela dedicada para visualizar email com suporte a HTML renderizado.

    on_download: callback opcional chamado quando o usuário clicar em "Baixar anexos".
                 Assinatura: (email_data: Dict) -> None
    """
    
    def __init__(self, parent: tk.Tk, email_data: Dict, on_download: Optional[Callable[[Dict], None]] = None):
        super().__init__(parent)
        self.title("Visualizador de Email")
        self.geometry("900x700")
        self.minsize(600, 400)
        
        self.email_data = email_data
        self.on_download = on_download
        self._build_ui()
        self._render_email()
        
    def _build_ui(self):
        # Cabeçalho
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=12, pady=8)
        
        ttk.Label(header, text="Assunto:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2)
        subject = self.email_data.get('subject', '')
        subj_label = ttk.Label(header, text=subject, font=("Segoe UI", 10))
        subj_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(6,0))
        
        ttk.Label(header, text="De:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2)
        from_label = ttk.Label(header, text=self.email_data.get('from', ''))
        from_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(6,0))
        
        ttk.Label(header, text="Data:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
        date_label = ttk.Label(header, text=self.email_data.get('date', ''))
        date_label.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(6,0))
        
        header.grid_columnconfigure(1, weight=1)
        # Ações
        actions = ttk.Frame(header)
        actions.grid(row=0, column=2, rowspan=3, sticky=tk.E)
        ttk.Button(actions, text="Abrir no navegador", command=self._open_in_browser).pack(side=tk.RIGHT)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12)
        
        # Corpo (scrollable frame)
        body_frame = ttk.Frame(self)
        body_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))
        
        # Tentar renderizar HTML se disponível
        self.html_widget: Optional[object] = None
        self.text_widget: Optional[scrolledtext.ScrolledText] = None
        
        # Verificar se tem HTML e se há lib disponível
        has_html = bool(self.email_data.get('body_html'))
        html_lib = self._get_html_lib()
        
        if has_html and html_lib == 'tkinterweb':
            try:
                from tkinterweb import HtmlFrame  # type: ignore
                self.html_widget = HtmlFrame(body_frame, messages_enabled=False)
                self.html_widget.pack(fill=tk.BOTH, expand=True)
            except Exception:
                html_lib = None
        
        if has_html and html_lib == 'tkhtmlview':
            try:
                from tkhtmlview import HTMLScrolledText  # type: ignore
                self.html_widget = HTMLScrolledText(body_frame, html="")
                self.html_widget.pack(fill=tk.BOTH, expand=True)
            except Exception:
                html_lib = None
        
        # Fallback: text widget
        if self.html_widget is None:
            self.text_widget = scrolledtext.ScrolledText(body_frame, wrap='word', bg='#1e1e1e', fg='#eaeaea', insertbackground='white')
            self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Anexos
        attachments = self.email_data.get('attachments') or []
        if attachments:
            att_frame = ttk.Frame(self)
            att_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
            row = 0
            ttk.Label(att_frame, text="Anexos:", font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky=tk.W)
            # botão de download
            if self.on_download:
                btn = ttk.Button(att_frame, text="Baixar anexos", command=lambda: self.on_download(self.email_data))
                btn.grid(row=row, column=1, sticky=tk.E, padx=(8,0))
            row += 1
            for idx, a in enumerate(attachments, start=1):
                ttk.Label(att_frame, text=f"• {a['filename']} ({a['content_type']})").grid(row=row, column=0, columnspan=2, sticky=tk.W)
                row += 1
    
    def _get_html_lib(self) -> Optional[str]:
        """Verifica qual biblioteca de renderização HTML está disponível."""
        try:
            import tkinterweb  # type: ignore
            return 'tkinterweb'
        except Exception:
            pass
        try:
            import tkhtmlview  # type: ignore
            return 'tkhtmlview'
        except Exception:
            pass
        return None
    
    def _render_email(self):
        """Renderiza o corpo do email."""
        body_html = self.email_data.get('body_html', '')
        body_text = self.email_data.get('body_text', '')
        cid_map = self.email_data.get('cid_map') or {}
        html_processed = self._prepare_html_for_view(body_html, body_text, cid_map)
        
        if self.html_widget is not None:
            # Renderizar HTML
            if hasattr(self.html_widget, 'load_html'):
                # tkinterweb HtmlFrame
                try:
                    self.html_widget.load_html(html_processed)
                except Exception:
                    pass
            elif hasattr(self.html_widget, 'set_html'):
                # tkhtmlview HTMLScrolledText
                try:
                    self.html_widget.set_html(html_processed)
                except Exception:
                    pass
        elif self.text_widget is not None:
            # Fallback: texto puro
            content = body_text or self._html_to_plain(body_html) if body_html else "Sem conteúdo de corpo."
            self.text_widget.insert('1.0', content)
            self.text_widget.configure(state='disabled')
    
    def _html_to_plain(self, html: str) -> str:
        """Converte HTML básico em texto puro (fallback)."""
        try:
            from html.parser import HTMLParser
            import re
            
            class HTMLToText(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                def handle_data(self, data):
                    self.text.append(data)
            
            parser = HTMLToText()
            parser.feed(html)
            text = ''.join(parser.text)
            # Remove múltiplos espaços/linhas
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html

    # --- Helpers: HTML processing / open in browser ---
    def _prepare_html_for_view(self, body_html: str, body_text: str, cid_map: dict) -> str:
        """Gera HTML final com substituição de cid: por data URI e fallback para texto."""
        html = body_html or ""
        if not html:
            # fallback: cria HTML básico a partir do texto
            safe_text = (body_text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html = f"<html><body><pre style='font-family: Segoe UI, Arial; white-space: pre-wrap;'>{safe_text}</pre></body></html>"
        # substitui cids
        try:
            if cid_map:
                for cid, data_uri in cid_map.items():
                    html = html.replace(f"src=\"cid:{cid}\"", f"src=\"{data_uri}\"")
                    html = html.replace(f"src='cid:{cid}'", f"src='{data_uri}'")
                    # sem prefixo
                    html = html.replace(f"src=\"{cid}\"", f"src=\"{data_uri}\"")
                    html = html.replace(f"src='{cid}'", f"src='{data_uri}'")
        except Exception:
            pass
        return html

    def _open_in_browser(self):
        try:
            html = self._prepare_html_for_view(self.email_data.get('body_html', ''),
                                               self.email_data.get('body_text', ''),
                                               self.email_data.get('cid_map') or {})
            # pasta temp do projeto
            base_dir = os.path.dirname(os.path.dirname(__file__))
            out_dir = os.path.join(base_dir, 'temp', 'email_view')
            os.makedirs(out_dir, exist_ok=True)
            uid = str(self.email_data.get('uid') or 'email')
            path = os.path.join(out_dir, f"{uid}.html")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            url = 'file:///' + quote(path.replace('\\', '/'))
            webbrowser.open_new_tab(url)
        except Exception as e:
            try:
                from tkinter import messagebox
                messagebox.showerror("Abrir no navegador", str(e))
            except Exception:
                pass
