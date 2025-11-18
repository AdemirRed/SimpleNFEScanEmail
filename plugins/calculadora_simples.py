"""
Plugin de Teste: Calculadora de Estatísticas Simples

Plugin de exemplo para demonstrar o sistema de plugins do SimpleNFE.
Calcula estatísticas básicas dos itens extraídos.

Autor: SimpleNFE Community
Versão: 1.0.0
"""

from plugins import BasePlugin
from typing import Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox

class CalculadoraSimples(BasePlugin):
    """Plugin que calcula estatísticas simples dos itens"""
    
    @property
    def name(self) -> str:
        return "Calculadora de Estatísticas"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Calcula estatísticas detalhadas: média, mediana, desvio padrão, quartis"
    
    @property
    def author(self) -> str:
        return "SimpleNFE Community"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Inicializa o plugin"""
        self.app = app_context.get('app')
        self.items = app_context.get('extracted_items', [])
        return True
    
    def get_menu_label(self) -> str:
        return "📊 Estatísticas Avançadas"
    
    def get_toolbar_icon(self) -> str:
        return "📊"
    
    def execute(self, **kwargs) -> Any:
        """Executa cálculo de estatísticas"""
        # Atualiza itens do contexto
        self.items = kwargs.get('items', self.items)
        
        if not self.items:
            messagebox.showinfo(
                "Calculadora",
                "Nenhum item disponível para calcular.\n\nExtraia alguns itens primeiro!"
            )
            return {'success': False, 'message': 'Nenhum item disponível'}
        
        # Calcula estatísticas
        valores = [float(item.get('valor_total', 0) or 0) for item in self.items]
        valores = [v for v in valores if v > 0]  # Remove zeros
        
        if not valores:
            messagebox.showwarning(
                "Calculadora",
                "Não há valores válidos para calcular estatísticas."
            )
            return {'success': False, 'message': 'Valores inválidos'}
        
        # Ordena valores para cálculos
        valores_ord = sorted(valores)
        n = len(valores_ord)
        
        # Cálculos básicos
        total = sum(valores)
        media = total / n
        maximo = max(valores)
        minimo = min(valores)
        
        # Mediana
        if n % 2 == 0:
            mediana = (valores_ord[n//2 - 1] + valores_ord[n//2]) / 2
        else:
            mediana = valores_ord[n//2]
        
        # Quartis
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = valores_ord[q1_idx]
        q3 = valores_ord[q3_idx]
        
        # Desvio padrão
        variancia = sum((x - media) ** 2 for x in valores) / n
        desvio_padrao = variancia ** 0.5
        
        # Coeficiente de variação
        coef_variacao = (desvio_padrao / media) * 100 if media > 0 else 0
        
        # Amplitude
        amplitude = maximo - minimo
        
        # Itens acima/abaixo da média
        acima_media = sum(1 for v in valores if v > media)
        abaixo_media = sum(1 for v in valores if v < media)
        
        # Mostra janela com resultados
        self._show_results_window(
            total, media, mediana, desvio_padrao, coef_variacao,
            minimo, maximo, amplitude, q1, q3, n, acima_media, abaixo_media
        )
        
        return {
            'success': True,
            'message': f'Estatísticas calculadas para {n} itens',
            'statistics': {
                'total': total,
                'media': media,
                'mediana': mediana,
                'desvio_padrao': desvio_padrao,
                'n': n
            }
        }
    
    def _show_results_window(self, total, media, mediana, desvio, cv, 
                            minimo, maximo, amplitude, q1, q3, n, acima, abaixo):
        """Mostra janela com resultados das estatísticas"""
        window = tk.Toplevel()
        window.title("📊 Estatísticas Avançadas")
        window.geometry("600x900")
        window.resizable(False, False)
        
        # Frame principal com padding
        main_frame = ttk.Frame(window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            main_frame, 
            text="📊 Análise Estatística dos Valores Totais",
            font=('Segoe UI', 14, 'bold'),
            foreground='#667eea'
        ).pack(pady=(0, 20))
        
        # Frame para estatísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Função helper para adicionar estatística
        def add_stat(label, value, unit="R$", color='black'):
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=8)
            
            ttk.Label(
                frame,
                text=label,
                font=('Segoe UI', 10, 'bold')
            ).pack(side=tk.LEFT)
            
            if unit == "R$":
                value_text = f"{unit} {value:,.2f}"
            elif unit == "":
                value_text = f"{value:,.0f}"
            elif unit == "%":
                value_text = f"{value:.2f}{unit}"
            else:
                value_text = f"{value:,.2f} {unit}"
            
            ttk.Label(
                frame,
                text=value_text,
                font=('Segoe UI', 11),
                foreground=color
            ).pack(side=tk.RIGHT)
        
        # Seção: Resumo Geral
        ttk.Label(
            stats_frame,
            text="📈 Resumo Geral",
            font=('Segoe UI', 11, 'bold'),
            foreground='#764ba2'
        ).pack(anchor=tk.W, pady=(10, 8))
        
        ttk.Separator(stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        add_stat("Total de Itens:", n, unit="", color='#667eea')
        add_stat("Valor Total:", total, color='#667eea')
        add_stat("Valor Médio:", media, color='green')
        add_stat("Valor Mediano:", mediana, color='green')
        
        # Seção: Dispersão
        ttk.Label(
            stats_frame,
            text="📊 Dispersão dos Dados",
            font=('Segoe UI', 11, 'bold'),
            foreground='#764ba2'
        ).pack(anchor=tk.W, pady=(20, 8))
        
        ttk.Separator(stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        add_stat("Desvio Padrão:", desvio)
        add_stat("Coef. de Variação:", cv, unit="%")
        add_stat("Amplitude:", amplitude)
        
        # Seção: Extremos
        ttk.Label(
            stats_frame,
            text="🔍 Valores Extremos",
            font=('Segoe UI', 11, 'bold'),
            foreground='#764ba2'
        ).pack(anchor=tk.W, pady=(20, 8))
        
        ttk.Separator(stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        add_stat("Valor Mínimo:", minimo, color='blue')
        add_stat("1º Quartil (Q1):", q1)
        add_stat("3º Quartil (Q3):", q3)
        add_stat("Valor Máximo:", maximo, color='red')
        
        # Seção: Distribuição
        ttk.Label(
            stats_frame,
            text="📉 Distribuição",
            font=('Segoe UI', 11, 'bold'),
            foreground='#764ba2'
        ).pack(anchor=tk.W, pady=(20, 8))
        
        ttk.Separator(stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        add_stat("Itens acima da média:", acima, unit="", color='green')
        add_stat("Itens abaixo da média:", abaixo, unit="", color='orange')
        
        # Interpretação
        interp_frame = ttk.LabelFrame(main_frame, text="💡 Interpretação", padding=15)
        interp_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Interpreta coeficiente de variação
        if cv < 15:
            variabilidade = "baixa (dados homogêneos)"
            cor_var = "green"
        elif cv < 30:
            variabilidade = "moderada"
            cor_var = "orange"
        else:
            variabilidade = "alta (dados heterogêneos)"
            cor_var = "red"
        
        interpretacao = f"• Variabilidade dos valores: {variabilidade}\n"
        interpretacao += f"• 50% dos itens custam entre R$ {q1:,.2f} e R$ {q3:,.2f}\n"
        
        if media > mediana:
            interpretacao += f"• Distribuição assimétrica à direita (poucos itens muito caros)\n"
        elif media < mediana:
            interpretacao += f"• Distribuição assimétrica à esquerda (poucos itens muito baratos)\n"
        else:
            interpretacao += f"• Distribuição simétrica\n"
        
        text_widget = tk.Text(interp_frame, height=4, wrap=tk.WORD, 
                             font=('Segoe UI', 9), relief=tk.FLAT,
                             background='#f0f0f0')
        text_widget.insert('1.0', interpretacao)
        text_widget.configure(state='disabled')
        text_widget.pack(fill=tk.X)
        
        # Botão fechar
        ttk.Button(
            main_frame,
            text="✖ Fechar",
            command=window.destroy
        ).pack(pady=(20, 0))
    
    def cleanup(self) -> None:
        """Limpeza ao desabilitar plugin"""
        pass
