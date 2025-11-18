"""
Plugin de Teste: Contador de Itens por Fornecedor

Plugin simples para demonstrar funcionalidades básicas.
Conta quantos itens foram comprados de cada fornecedor.

Autor: SimpleNFE Community
Versão: 1.0.0
"""

from plugins import BasePlugin
from typing import Dict, Any
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox

class ContadorFornecedor(BasePlugin):
    """Plugin que conta itens por fornecedor"""
    
    @property
    def name(self) -> str:
        return "Contador por Fornecedor"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Conta quantos itens diferentes foram comprados de cada fornecedor"
    
    @property
    def author(self) -> str:
        return "SimpleNFE Community"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Inicializa o plugin"""
        self.items = app_context.get('extracted_items', [])
        return True
    
    def get_menu_label(self) -> str:
        return "🏢 Contador de Fornecedores"
    
    def get_toolbar_icon(self) -> str:
        return "🏢"
    
    def execute(self, **kwargs) -> Any:
        """Executa contagem por fornecedor"""
        self.items = kwargs.get('items', self.items)
        
        if not self.items:
            messagebox.showinfo(
                "Contador",
                "Nenhum item disponível.\n\nExtraia itens de NF-e primeiro!"
            )
            return {'success': False, 'message': 'Nenhum item'}
        
        # Agrupa por fornecedor
        fornecedores = defaultdict(lambda: {'itens': 0, 'valor': 0.0, 'produtos': set()})
        
        for item in self.items:
            fornecedor = item.get('fornecedor', 'Desconhecido').strip()
            if not fornecedor:
                fornecedor = 'Sem Fornecedor'
            
            valor = float(item.get('valor_total', 0) or 0)
            produto = item.get('descricao', '').strip()
            
            fornecedores[fornecedor]['itens'] += 1
            fornecedores[fornecedor]['valor'] += valor
            if produto:
                fornecedores[fornecedor]['produtos'].add(produto.lower())
        
        # Ordena por valor total
        ranking = sorted(
            fornecedores.items(),
            key=lambda x: x[1]['valor'],
            reverse=True
        )
        
        # Mostra janela com resultados
        self._show_results_window(ranking)
        
        return {
            'success': True,
            'message': f'Analisados {len(ranking)} fornecedores',
            'total_fornecedores': len(ranking)
        }
    
    def _show_results_window(self, ranking):
        """Mostra janela com ranking de fornecedores"""
        window = tk.Toplevel()
        window.title("🏢 Contador por Fornecedor")
        window.geometry("900x600")
        
        # Frame principal
        main_frame = ttk.Frame(window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            main_frame,
            text="🏢 Análise de Compras por Fornecedor",
            font=('Segoe UI', 13, 'bold'),
            foreground='#667eea'
        ).pack(pady=(0, 15))
        
        # Info resumo
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        total_fornecedores = len(ranking)
        total_itens = sum(f[1]['itens'] for f in ranking)
        total_valor = sum(f[1]['valor'] for f in ranking)
        
        ttk.Label(
            info_frame,
            text=f"Total: {total_fornecedores} fornecedores | {total_itens} itens | R$ {total_valor:,.2f}",
            font=('Segoe UI', 10, 'bold'),
            foreground='#764ba2'
        ).pack()
        
        # Tabela
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Colunas
        cols = ("rank", "fornecedor", "itens", "produtos", "valor", "percentual")
        tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=20)
        
        tree.heading("rank", text="#")
        tree.heading("fornecedor", text="Fornecedor")
        tree.heading("itens", text="Itens")
        tree.heading("produtos", text="Produtos Únicos")
        tree.heading("valor", text="Valor Total")
        tree.heading("percentual", text="% do Total")
        
        tree.column("rank", width=50, anchor=tk.CENTER)
        tree.column("fornecedor", width=350, anchor=tk.W)
        tree.column("itens", width=80, anchor=tk.CENTER)
        tree.column("produtos", width=120, anchor=tk.CENTER)
        tree.column("valor", width=120, anchor=tk.E)
        tree.column("percentual", width=100, anchor=tk.CENTER)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Preenche dados
        for idx, (fornecedor, dados) in enumerate(ranking, 1):
            percentual = (dados['valor'] / total_valor * 100) if total_valor > 0 else 0
            
            # Destaca top 3
            tag = ''
            if idx == 1:
                tag = 'gold'
            elif idx == 2:
                tag = 'silver'
            elif idx == 3:
                tag = 'bronze'
            
            tree.insert('', tk.END, values=(
                f"{idx}º",
                fornecedor,
                dados['itens'],
                len(dados['produtos']),
                f"R$ {dados['valor']:,.2f}",
                f"{percentual:.1f}%"
            ), tags=(tag,))
        
        # Cores para top 3
        tree.tag_configure('gold', background='#FFD700')
        tree.tag_configure('silver', background='#C0C0C0')
        tree.tag_configure('bronze', background='#CD7F32')
        
        # Rodapé com dicas
        tips_frame = ttk.LabelFrame(main_frame, text="💡 Dicas", padding=10)
        tips_frame.pack(fill=tk.X, pady=(10, 0))
        
        dicas = "• Os 3 primeiros fornecedores estão destacados (ouro, prata, bronze)\n"
        dicas += "• Use esta análise para negociar descontos por volume\n"
        dicas += "• Fornecedores com muitos produtos únicos podem ter catálogo mais diversificado"
        
        ttk.Label(tips_frame, text=dicas, font=('Segoe UI', 9), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Botão fechar
        ttk.Button(main_frame, text="✖ Fechar", command=window.destroy).pack(pady=(10, 0))
    
    def cleanup(self) -> None:
        """Limpeza ao desabilitar"""
        pass
