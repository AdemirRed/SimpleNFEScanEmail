import tkinter as tk
from tkinter import ttk


def setup_theme(root: tk.Tk) -> None:
    """Aplica tema escuro profissional usando sv-ttk se disponível,
    senão configura 'clam' com cores escuras personalizadas.
    """
    try:
        import sv_ttk  # type: ignore
        sv_ttk.set_theme("dark")
        return
    except Exception:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Cores base
    bg = '#1e1e1e'
    bg2 = '#252526'
    fg = '#eaeaea'
    accent = '#0e639c'
    sel_bg = '#094771'

    root.configure(bg=bg)

    # Defaults
    style.configure('.',
                    background=bg,
                    foreground=fg,
                    fieldbackground=bg2)

    # Frames/Labels/Buttons
    style.configure('TFrame', background=bg)
    style.configure('TLabel', background=bg, foreground=fg)
    style.configure('TButton', background='#333333', foreground=fg, relief='flat')
    style.map('TButton', background=[('active', '#3c3c3c')])

    # Entry
    style.configure('TEntry', fieldbackground=bg2, foreground=fg)

    # Progressbar
    style.configure('Horizontal.TProgressbar', troughcolor=bg2, background=accent)

    # Treeview
    style.configure('Treeview', background=bg2, fieldbackground=bg2, foreground=fg, bordercolor=bg)
    style.map('Treeview', background=[('selected', sel_bg)], foreground=[('selected', '#ffffff')])
    style.configure('Treeview.Heading', background=bg, foreground=fg)

    # Notebook
    style.configure('TNotebook', background=bg)
    style.configure('TNotebook.Tab', background='#2d2d30', foreground=fg)
    style.map('TNotebook.Tab', background=[('selected', bg2)])

    # Fonte padrão (opcional)
    try:
        import tkinter.font as tkfont
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(family='Segoe UI', size=10)
        text_font = tkfont.nametofont('TkTextFont')
        text_font.configure(family='Segoe UI', size=10)
    except Exception:
        pass
