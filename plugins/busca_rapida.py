"""
Plugin de Teste: Busca Rápida

Plugin super simples para demonstrar a API básica.
Permite buscar produtos por palavra-chave e mostra resultados.

Autor: SimpleNFE Community
Versão: 1.0.0
"""

from plugins import BasePlugin
from typing import Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox

class BuscaRapida(BasePlugin):
    """Plugin de busca rápida em itens"""
    
    @property
    def name(self) -> str:
        return "Busca Rápida"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Busca rápida de produtos por palavra-chave com resultados detalhados"
    
    @property
    def author(self) -> str:
        return "SimpleNFE Community"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Inicializa o plugin"""
        self.items = app_context.get('extracted_items', [])
        return True
    
    def get_menu_label(self) -> str:
        return "🔍 Busca Rápida"
    
    def get_toolbar_icon(self) -> str:
        return "🔍"
    
    def execute(self, **kwargs) -> Any:
        """Abre janela de busca"""
        self.items = kwargs.get('items', self.items)
        
        if not self.items:
            messagebox.showinfo(
                "Busca Rápida",
                "Nenhum item disponível para buscar.\n\nExtraia itens primeiro!"
            )
            return {'success': False, 'message': 'Nenhum item'}
        
        # Abre janela de busca
        self._show_search_window()
        
        return {'success': True, 'message': 'Janela de busca aberta'}
    
    def _show_search_window(self):
        """Mostra janela de busca"""
        window = tk.Toplevel()
        window.title("🔍 Busca Rápida")
        window.geometry("800x550")
        
        # Frame principal
        main_frame = ttk.Frame(window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            main_frame,
            text="🔍 Busca Rápida de Produtos",
            font=('Segoe UI', 13, 'bold'),
            foreground='#667eea'
        ).pack(pady=(0, 15))
        
        # Frame de busca
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Palavra-chave:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 8))
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40, font=('Segoe UI', 10))
        search_entry.pack(side=tk.LEFT, padx=(0, 8))
        search_entry.focus()
        
        # Resultado contador
        result_var = tk.StringVar(value="Digite uma palavra-chave e pressione Enter ou clique em Buscar")
        result_label = ttk.Label(main_frame, textvariable=result_var, font=('Segoe UI', 9, 'italic'))
        result_label.pack(pady=(0, 8))
        
        # Tabela de resultados
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        cols = ("descricao", "qtd", "valor_unit", "valor_total", "fornecedor")
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)
        
        tree.heading("descricao", text="Descrição")
        tree.heading("qtd", text="Quantidade")
        tree.heading("valor_unit", text="Valor Unit.")
        tree.heading("valor_total", text="Valor Total")
        tree.heading("fornecedor", text="Fornecedor")
        
        tree.column("descricao", width=300, anchor=tk.W)
        tree.column("qtd", width=80, anchor=tk.CENTER)
        tree.column("valor_unit", width=100, anchor=tk.E)
        tree.column("valor_total", width=100, anchor=tk.E)
        tree.column("fornecedor", width=200, anchor=tk.W)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        def do_search(*args):
            """Executa a busca"""
            keyword = search_var.get().strip().lower()
            
            if not keyword:
                result_var.set("Digite uma palavra-chave para buscar")
                tree.delete(*tree.get_children())
                return
            
            # Busca nos itens
            results = []
            for item in self.items:
                descricao = item.get('descricao', '').lower()
                fornecedor = item.get('fornecedor', '').lower()
                
                if keyword in descricao or keyword in fornecedor:
                    results.append(item)
            
            # Limpa tabela
            tree.delete(*tree.get_children())
            
            if not results:
                result_var.set(f"❌ Nenhum resultado encontrado para '{keyword}'")
                return
            
            # Preenche resultados
            total_valor = 0.0
            for item in results:
                valor_total = float(item.get('valor_total', 0) or 0)
                total_valor += valor_total
                
                tree.insert('', tk.END, values=(
                    item.get('descricao', '')[:60],
                    item.get('quantidade', 0),
                    f"R$ {float(item.get('valor_unitario', 0) or 0):.2f}",
                    f"R$ {valor_total:.2f}",
                    item.get('fornecedor', '')[:30]
                ))
            
            result_var.set(
                f"✅ Encontrados {len(results)} item(s) | "
                f"Valor total: R$ {total_valor:,.2f}"
            )
        
        # Botão buscar
        ttk.Button(search_frame, text="🔍 Buscar", command=do_search).pack(side=tk.LEFT)
        
        # Enter também busca
        search_entry.bind('<Return>', do_search)
        
        # Frame de dicas
        tips_frame = ttk.LabelFrame(main_frame, text="💡 Dicas", padding=10)
        tips_frame.pack(fill=tk.X, pady=(10, 0))
        
        dicas = "• Digite parte do nome do produto (ex: 'papel', 'caneta', 'toner')\n"
        dicas += "• Também busca no nome do fornecedor\n"
        dicas += "• Não é case-sensitive (não diferencia maiúsculas de minúsculas)"
        
        ttk.Label(tips_frame, text=dicas, font=('Segoe UI', 9), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Botão fechar
        ttk.Button(main_frame, text="✖ Fechar", command=window.destroy).pack(pady=(10, 0))
    
    def cleanup(self) -> None:
        """Limpeza ao desabilitar"""
        pass
