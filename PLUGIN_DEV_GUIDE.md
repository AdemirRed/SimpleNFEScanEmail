# 🧩 Guia de Desenvolvimento de Plugins - SimpleNFE

## 📌 Introdução

O SimpleNFE possui um **sistema de plugins extensível** que permite à comunidade criar funcionalidades customizadas sem modificar o código principal. Qualquer pessoa pode desenvolver e compartilhar plugins!

---

## 🚀 Como Criar Seu Plugin

### **1. Estrutura Básica**

Todo plugin deve:
- Estar na pasta `plugins/`
- Herdar da classe `BasePlugin`
- Implementar os métodos obrigatórios

### **2. Template Mínimo**

```python
from plugins import BasePlugin
from typing import Dict, Any

class MeuPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "Meu Plugin Incrível"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Descrição curta do que seu plugin faz"
    
    @property
    def author(self) -> str:
        return "Seu Nome"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Inicialização - recebe contexto da aplicação"""
        self.app = app_context.get('app')
        self.items = app_context.get('extracted_items', [])
        self.config = app_context.get('config', {})
        return True  # Retorne True se inicializou com sucesso
    
    def execute(self, **kwargs) -> Any:
        """Executa a funcionalidade principal"""
        # Seu código aqui!
        return {
            'success': True,
            'message': 'Plugin executado com sucesso!'
        }
```

---

## 📦 API Disponível

### **Contexto da Aplicação (app_context)**

Quando seu plugin é inicializado, ele recebe um dicionário com:

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `app` | `SimpleNFEApp` | Instância principal do aplicativo |
| `extracted_items` | `List[Dict]` | Lista de todos os itens extraídos das NF-e |
| `config` | `Dict` | Configurações do sistema (email, LLM, etc) |

### **Estrutura de um Item (`extracted_items`)**

Cada item na lista possui:

```python
{
    'descricao': 'Caneta azul BIC',
    'quantidade': 50,
    'unidade': 'UN',
    'valor_unitario': 1.50,
    'valor_total': 75.00,
    'fornecedor': 'Papelaria Xpto LTDA',
    'data_nota': '2024-01-15',
    'documento': '243250188468812'
}
```

### **Métodos Opcionais**

```python
def get_menu_label(self) -> str:
    """Label personalizada para o menu"""
    return "🎨 Meu Plugin"

def get_toolbar_icon(self) -> str:
    """Emoji para aparecer na toolbar (opcional)"""
    return "🎨"

def cleanup(self) -> None:
    """Executado ao desabilitar o plugin"""
    # Limpe recursos, feche arquivos, etc
    pass

def get_settings_ui(self) -> Dict[str, Any]:
    """Define campos de configuração (futuro)"""
    return {
        'campos': [
            {'nome': 'api_key', 'tipo': 'text', 'label': 'API Key'},
            {'nome': 'ativo', 'tipo': 'checkbox', 'label': 'Ativar'}
        ]
    }
```

---

## 💡 Exemplos de Plugins

### **Exemplo 1: Exportador Excel** (incluído)

Já vem com o sistema! Veja `plugins/exemplo_exportador_excel.py`

**Funcionalidade**: Exporta itens para planilha Excel (.xlsx) formatada

**Uso**:
1. Habilite o plugin no gerenciador
2. Clique em "Executar Plugin"
3. Escolha onde salvar o arquivo

### **Exemplo 2: Filtro por Categoria**

```python
from plugins import BasePlugin
import tkinter as tk
from tkinter import ttk, messagebox

class FiltroCategoria(BasePlugin):
    @property
    def name(self) -> str:
        return "Filtro por Categoria"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Filtra itens por palavras-chave (ex: eletrônicos, papelaria)"
    
    @property
    def author(self) -> str:
        return "Comunidade SimpleNFE"
    
    def initialize(self, app_context):
        self.app = app_context.get('app')
        self.items = app_context.get('extracted_items', [])
        return True
    
    def execute(self, **kwargs):
        """Abre janela para filtrar por categoria"""
        self.items = kwargs.get('items', self.items)
        
        window = tk.Toplevel()
        window.title("Filtrar por Categoria")
        window.geometry("400x200")
        
        ttk.Label(window, text="Digite palavras-chave (ex: caneta, papel):").pack(pady=10)
        
        entry = ttk.Entry(window, width=40)
        entry.pack(pady=5)
        
        def filtrar():
            keywords = entry.get().lower().split(',')
            keywords = [k.strip() for k in keywords if k.strip()]
            
            if not keywords:
                messagebox.showwarning("Filtro", "Digite pelo menos uma palavra-chave.")
                return
            
            filtered = [
                item for item in self.items
                if any(kw in item.get('descricao', '').lower() for kw in keywords)
            ]
            
            messagebox.showinfo(
                "Resultado",
                f"Encontrados {len(filtered)} itens de {len(self.items)} totais\n\n"
                f"Categorias: {', '.join(keywords)}"
            )
            
            # Atualiza a UI principal com itens filtrados
            self.app.extracted_items = filtered
            self.app._refresh_items_tab()
            window.destroy()
        
        ttk.Button(window, text="Filtrar", command=filtrar).pack(pady=20)
        
        return {'success': True}
```

### **Exemplo 3: Comparador de Preços**

```python
from plugins import BasePlugin
from collections import defaultdict

class ComparadorPrecos(BasePlugin):
    @property
    def name(self) -> str:
        return "Comparador de Preços"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Compara preços do mesmo produto entre fornecedores"
    
    @property
    def author(self) -> str:
        return "Comunidade SimpleNFE"
    
    def initialize(self, app_context):
        self.items = app_context.get('extracted_items', [])
        return True
    
    def execute(self, **kwargs):
        self.items = kwargs.get('items', self.items)
        
        # Agrupa por produto
        produtos = defaultdict(list)
        for item in self.items:
            desc = item.get('descricao', '').lower().strip()
            if desc:
                produtos[desc].append(item)
        
        # Encontra produtos com múltiplos fornecedores
        comparacoes = []
        for desc, itens in produtos.items():
            if len(itens) > 1:
                precos = [(i['fornecedor'], i['valor_unitario']) for i in itens]
                precos.sort(key=lambda x: x[1])
                
                mais_barato = precos[0]
                mais_caro = precos[-1]
                diferenca = ((mais_caro[1] - mais_barato[1]) / mais_barato[1]) * 100
                
                if diferenca > 5:  # Diferença > 5%
                    comparacoes.append({
                        'produto': desc,
                        'mais_barato': mais_barato,
                        'mais_caro': mais_caro,
                        'diferenca_pct': diferenca
                    })
        
        # Exibe resultado
        if comparacoes:
            msg = "🔍 Oportunidades de Economia:\n\n"
            for comp in sorted(comparacoes, key=lambda x: x['diferenca_pct'], reverse=True)[:10]:
                msg += f"📦 {comp['produto'][:50]}\n"
                msg += f"   ✅ Mais barato: {comp['mais_barato'][0]} - R$ {comp['mais_barato'][1]:.2f}\n"
                msg += f"   ❌ Mais caro: {comp['mais_caro'][0]} - R$ {comp['mais_caro'][1]:.2f}\n"
                msg += f"   💰 Diferença: {comp['diferenca_pct']:.1f}%\n\n"
            
            from tkinter import messagebox
            messagebox.showinfo("Comparação de Preços", msg)
        else:
            from tkinter import messagebox
            messagebox.showinfo("Comparação", "Nenhuma diferença significativa encontrada.")
        
        return {'success': True, 'comparacoes': len(comparacoes)}
```

---

## 🛠️ Instalando Seu Plugin

1. **Salve o arquivo**: Coloque na pasta `plugins/` com extensão `.py`
   - Exemplo: `plugins/meu_plugin_incrivel.py`

2. **Abra o SimpleNFE**: Execute o programa normalmente

3. **Gerenciador de Plugins**: 
   - Vá na aba "Itens"
   - Clique no botão "🧩 Plugins"
   - Clique em "🔄 Atualizar Lista"

4. **Habilite o Plugin**:
   - Selecione seu plugin na lista
   - Clique em "✅ Habilitar"

5. **Execute**: Clique em "▶️ Executar Plugin"

---

## ⚙️ Boas Práticas

### ✅ **Faça:**

- Use `try/except` para capturar erros
- Retorne dicionários com `{'success': bool, 'message': str}`
- Documente seu código
- Teste com diferentes tipos de dados
- Use `messagebox` para feedback ao usuário

### ❌ **Evite:**

- Modificar `self.app.extracted_items` diretamente (faça cópia)
- Operações muito lentas sem feedback
- Dependências externas não documentadas
- Acessar arquivos fora da pasta do plugin

---

## 📚 Dependências Externas

Se seu plugin precisa de bibliotecas externas, **documente no código**:

```python
"""
Plugin: Meu Plugin

Dependências:
- openpyxl: pip install openpyxl
- requests: pip install requests

Instalação:
pip install openpyxl requests
"""
```

No método `initialize()`, verifique se estão instaladas:

```python
def initialize(self, app_context):
    try:
        import openpyxl
        self.available = True
    except ImportError:
        print("⚠️ openpyxl não instalado. Execute: pip install openpyxl")
        self.available = False
    
    return True  # Ainda retorna True para não bloquear o carregamento
```

---

## 🎁 Compartilhando Plugins

### **1. GitHub Gist**
- Crie um Gist público com seu arquivo `.py`
- Compartilhe o link

### **2. Repositório SimpleNFE-Plugins**
- Faça um Pull Request para o repositório oficial
- Comunidade poderá baixar diretamente

### **3. Fórum/Discord**
- Poste no canal de plugins
- Outros usuários podem testar e dar feedback

---

## 🐛 Debugging

**Ver logs do plugin:**
- Mensagens de `print()` aparecem no console/terminal
- Use `print(f"DEBUG: {variavel}")` para debug

**Plugin não aparece:**
1. Verifique se está na pasta `plugins/`
2. Verifique se herda de `BasePlugin`
3. Veja erros no console

**Plugin não executa:**
1. Verifique se está habilitado
2. Veja se `initialize()` retornou `True`
3. Use `try/except` no `execute()` para capturar erros

---

## 🏆 Ideias de Plugins

- **Gerador de Gráficos**: Visualize gastos com matplotlib
- **Integração WhatsApp**: Envie relatórios via API
- **Backup Automático**: Salve itens periodicamente
- **Análise de Tendências**: Detecte padrões temporais
- **Conversor de Moedas**: Converta valores para USD/EUR
- **Validador de Duplicatas**: Encontre NF-e duplicadas
- **Alertas de Orçamento**: Notifique quando ultrapassar limite
- **Integração ERP**: Sincronize com sistemas externos

---

## 📞 Suporte

**Dúvidas sobre desenvolvimento de plugins?**
- Consulte os exemplos na pasta `plugins/`
- Abra uma issue no GitHub
- Pergunte na comunidade

**Boa sorte desenvolvendo seu plugin! 🚀**
