# 📦 SimpleNFE - Sistema Inteligente de Gestão de Notas Fiscais

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**Automatize a extração, organização e análise de Notas Fiscais Eletrônicas (NF-e) direto do seu Gmail**

[Instalação](#-instalação) • [Recursos](#-recursos-principais) • [Como Usar](#-como-usar) • [Plugins](#-sistema-de-plugins) • [Documentação](#-documentação)

</div>

---

## 🎯 O que é o SimpleNFE?

O **SimpleNFE** é um sistema profissional de gestão e análise de notas fiscais eletrônicas desenvolvido em Python. Ele conecta ao seu Gmail, busca automaticamente e-mails com anexos de NF-e (XML e PDF), extrai todos os itens de compra e oferece ferramentas avançadas de análise e relatórios.

**⚡ Processe centenas de notas fiscais em minutos ao invés de horas!**

### 💡 Por que usar?

- ⏱️ **Economize Tempo**: Automatiza tarefas que levariam 20+ horas manualmente
- 💰 **Reduza Custos**: Identifique oportunidades de economia e negociação
- 📊 **Decisões Inteligentes**: Análise com IA opcional para insights estratégicos
- 🎨 **Relatórios Profissionais**: Exportação HTML formatada pronta para apresentação
- 🔒 **Seguro**: Todos os dados ficam no seu computador
- 🆓 **Gratuito**: Open source, sem custos de licença

---

## ✨ Recursos Principais

### 🔍 **Extração Automática**
- Conexão IMAP com Gmail
- Busca inteligente de e-mails com NF-e
- Suporta XML (parsing direto) e PDF (extração de texto + OCR awareness)
- Processamento em lote com barra de progresso
- Detecção automática de PDFs escaneados

### 📊 **Análise de Dados**
- **Busca avançada** por palavra-chave em qualquer campo
- **Filtros profissionais** por fornecedor, valor, período
- **Agrupamentos** por fornecedor ou produto
- **Rankings** automáticos (Top 10 mais caros, maior quantidade)
- **Estatísticas rápidas** (totais, médias, frequências)

### 🤖 **Análise com IA (Opcional)**
- Integração com LM Studio ou qualquer API OpenAI-compatible
- Instruções customizadas (templates inclusos: financeiro, estoque, fornecedores, negociação)
- Insights estratégicos: "Fornecedor X cobra 18% mais caro", "Economia potencial de R$ 3.500/ano"
- Recomendações automáticas de otimização
- **Funciona perfeitamente sem IA** - todos os recursos essenciais disponíveis offline

### 📄 **Exportação e Relatórios**
- **HTML profissional** com CSS moderno e gradientes
- **CSV** para planilhas
- **Excel** via plugin (formatação automática)
- Markdown convertido para HTML formatado
- Relatórios executivos com análise da IA

### 🧩 **Sistema de Plugins**
- API extensível para a comunidade
- Plugin de exemplo incluído (Exportador Excel)
- Guia completo de desenvolvimento
- Descoberta e carregamento automáticos
- Interface gráfica para gerenciar plugins

### 🖥️ **Interface Profissional**
- Tema moderno com `sv-ttk`
- 6 abas organizadas: Conexão, Pesquisa, Extração, Análise Local, Itens, Configurações
- Visualizador de e-mails com HTML renderizado
- Operações assíncronas com feedback visual
- Toolbar com ícones intuitivos

---

## 🚀 Instalação

### **Pré-requisitos**

- **Python 3.13+** (ou 3.10+)
- **Windows 10/11** (suporte para Linux/Mac em desenvolvimento)
- **Conta Gmail** com IMAP habilitado
- **Senha de App Gmail** (recomendado para segurança)
  - 📖 [Como criar senha de app](https://support.google.com/accounts/answer/185833)

### **Passo a Passo**

1️⃣ **Clone o repositório:**
```powershell
git clone https://github.com/AdemirRed/SimpleNFEScanEmail.git
cd SimpleNFEScanEmail/SimpleNFE
```

2️⃣ **Instale as dependências:**
```powershell
pip install -r requirements.txt
```

3️⃣ **Execute o aplicativo:**
```powershell
python app.py
```

### **Dependências Principais**
```
# Obrigatórias
cryptography>=42.0.0  # Criptografia de senhas

# Recomendadas
sv-ttk>=2.6.0        # Tema moderno
tkinterweb>=3.24.0   # Renderização HTML
pypdf2>=3.0.0        # Extração de PDF

# Opcionais (para LLM)
requests>=2.31.0     # Conexão com LM Studio

# Plugins (instalar sob demanda)
openpyxl>=3.1.0      # Para plugin de Excel
```

---

## 📖 Como Usar

### **1. Configure o Gmail**

1. Abra o SimpleNFE
2. Vá na aba **Configurações**
3. Preencha:
   - **Servidor:** `imap.gmail.com`
   - **Porta:** `993`
   - **E-mail:** seu-email@gmail.com
   - **Senha de App:** (gere no Gmail)
4. Clique em **Salvar Configurações**

### **2. Busque Notas Fiscais**

**Aba "Pesquisa de Notas":**
1. Marque **PDF** e/ou **XML**
2. Defina quantidade (ex: 50 últimos e-mails)
3. Clique em **Buscar**
4. Aguarde a barra de progresso
5. Resultados aparecem na tabela

### **3. Extraia Itens**

**Aba "Extração":**
1. Clique em **Carregar da Pesquisa**
2. Selecione notas (ou **Selecionar Todos**)
3. Clique em **Extrair Selecionados**
4. Arquivos são baixados e processados automaticamente

### **4. Analise os Dados**

**Aba "Itens":**
- 🔍 **Buscar:** Digite palavra-chave para filtrar
- 🏷️ **Por Fornecedor:** Agrupa compras por fornecedor
- 📦 **Por Produto:** Agrupa itens similares
- 💰 **Top 10 +Caros:** Ranking dos produtos mais caros
- 📈 **Top 10 +Qtd:** Ranking dos mais comprados
- 📊 **Estatísticas:** Totais, médias, valores

### **5. Use Análise com IA (Opcional)**

**Configurar LLM:**
1. Baixe e instale [LM Studio](https://lmstudio.ai/)
2. Carregue um modelo (ex: `qwen/qwen3-vl-4b`)
3. Inicie o servidor local (porta 1234)
4. No SimpleNFE, configure:
   - **URL:** `http://127.0.0.1:1234`
   - **Modelo:** nome do modelo carregado

**Gerar Resumo LLM:**
1. Na aba **Itens**, clique em **🤖 Resumo LLM**
2. (Opcional) Adicione instruções personalizadas
3. Aguarde análise
4. Visualize insights e recomendações
5. Exporte relatório HTML com análise

### **6. Exporte Relatórios**

- **📄 CSV:** Exportação básica para Excel/Sheets
- **🌐 HTML:** Relatório profissional formatado
- **📊 Excel:** Via plugin (instale `openpyxl`)

### **7. Análise Local (sem Gmail)**

**Aba "Análise Local":**
1. Clique em **Selecionar Arquivos**
2. Escolha XMLs/PDFs do seu computador
3. Clique em **Processar Arquivos Locais**
4. Análise idêntica à extração por e-mail

---

## 🧩 Sistema de Plugins

### **O que são Plugins?**

Plugins permitem que a comunidade crie funcionalidades customizadas sem modificar o código principal. Qualquer pessoa pode desenvolver e compartilhar!

### **Plugins Inclusos**

#### **📊 Exportador Excel**
- Exporta itens para planilha .xlsx
- Formatação profissional automática
- Cabeçalhos coloridos, bordas, valores monetários
- Congelamento de painéis
- **Requisito:** `pip install openpyxl`

#### **📊 Calculadora de Estatísticas**
- Calcula estatísticas avançadas dos valores
- Média, mediana, desvio padrão, quartis
- Coeficiente de variação
- Análise de dispersão e extremos
- Interpretação automática dos resultados

#### **🏢 Contador por Fornecedor**
- Ranking de fornecedores por valor total
- Contagem de itens e produtos únicos
- Percentual do total de compras
- Destaque visual para top 3 (ouro, prata, bronze)
- Ideal para negociações

#### **🔍 Busca Rápida**
- Interface de busca dedicada
- Busca por palavra-chave em produtos e fornecedores
- Resultados com totalizador
- Não é case-sensitive
- Ideal para consultas rápidas

### **Como Usar Plugins**

**Interface com Duas Abas:**

1. **📋 Todos os Plugins** - Lista todos disponíveis (habilitados e desabilitados)
2. **✅ Plugins Ativos** - Mostra apenas plugins habilitados e prontos para usar

**Passo a Passo:**

1. Na aba **Itens**, clique em **🧩 Plugins**
2. Navegue entre as abas conforme necessidade:
   - **Todos os Plugins:** Para habilitar/desabilitar
   - **Plugins Ativos:** Para ver quais estão rodando
3. Selecione um plugin
4. Clique **✅ Habilitar** (se desabilitado) ou **❌ Desabilitar** (se habilitado)
5. Clique **▶️ Executar Plugin** para usar

**Recursos do Gerenciador:**

- 🔄 Atualizar lista de plugins
- 📖 Abrir guia de desenvolvimento
- ✅/❌ Habilitar/desabilitar plugins com 1 clique
- ▶️ Executar plugins ativos
- ⌨️ **Configurar teclas de atalho**
- Contador de plugins ativos em tempo real

### **⌨️ Teclas de Atalho para Plugins**

Configure atalhos de teclado para executar plugins rapidamente!

**Como Configurar:**

1. No gerenciador de plugins, selecione um plugin
2. Clique no botão **⌨️ Atalho**
3. Digite o atalho desejado (ex: `Control-e`, `F5`, `Alt-p`)
4. Clique em **Salvar**

**Formatos Suportados:**

- `Control-letra` → Ctrl + letra (ex: `Control-e` = Ctrl+E)
- `Control-Shift-letra` → Ctrl + Shift + letra
- `Alt-letra` → Alt + letra (ex: `Alt-p` = Alt+P)
- `F1` a `F12` → Teclas de função

**Exemplos de Uso:**

- `F5` → Calculadora de Estatísticas
- `Control-e` → Exportador Excel
- `Alt-b` → Busca Rápida
- `Control-Shift-f` → Contador de Fornecedores

**Recursos:**

- ✅ Atalhos salvos automaticamente
- ✅ Funcionam em toda a aplicação
- ✅ Validação de conflitos (não permite atalhos duplicados)
- ✅ Exibição visual do atalho ao lado do nome do plugin
- ✅ Remoção fácil de atalhos
- ✅ Plugin precisa estar habilitado para usar o atalho

### **Como Criar Plugins**

📖 **Guia Completo:** [`PLUGIN_DEV_GUIDE.md`](PLUGIN_DEV_GUIDE.md)

**Template Básico:**
```python
from plugins import BasePlugin
from typing import Dict, Any

class MeuPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "Meu Plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Descrição do plugin"
    
    @property
    def author(self) -> str:
        return "Seu Nome"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        self.items = app_context.get('extracted_items', [])
        return True
    
    def execute(self, **kwargs) -> Any:
        # Seu código aqui!
        return {'success': True, 'message': 'Executado!'}
```

**Exemplos no Guia:**
- Filtro por Categoria
- Comparador de Preços
- Gerador de Gráficos
- E muito mais!

---

## 📚 Documentação

### **Arquivos Principais**

| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Aplicativo principal com interface gráfica |
| `cli_extract.py` | Versão linha de comando (sem UI) |
| `config.json` | Configurações (gerado automaticamente) |
| `APRESENTACAO.md` | Apresentação concisa para compartilhar |
| `PLUGIN_DEV_GUIDE.md` | Guia completo de desenvolvimento de plugins |

### **Módulos**

| Módulo | Função |
|--------|--------|
| `modules/email_gmail.py` | Conexão e operações IMAP |
| `modules/xml_pdf_extractor.py` | Extração de XML e PDF |
| `modules/llm_analyzer.py` | Análise com LLM |
| `modules/html_exporter.py` | Geração de relatórios HTML |
| `modules/plugin_manager.py` | Gerenciamento de plugins |
| `modules/email_monitor.py` | Monitoramento de novos e-mails |
| `modules/llm_status.py` | Status da conexão LLM |

### **Interface (UI)**

| Módulo | Função |
|--------|--------|
| `ui/email_viewer.py` | Visualizador de e-mails |
| `ui/theme.py` | Estilos e tema |

---

## 🔧 Modo CLI (sem interface)

Para usar via linha de comando:

```powershell
python cli_extract.py --limit 50 --types pdf,xml
```

**Opções:**
- `--limit N` - Quantidade de e-mails a processar (padrão: 20)
- `--types pdf,xml` - Tipos de anexos (padrão: ambos)
- `--include palavra1,palavra2` - Palavras-chave para incluir
- `--exclude promo,oferta` - Palavras-chave para excluir

**Saída:** `temp/out_items.json` com todos os itens extraídos

---

## 🎯 Casos de Uso

### **🏢 Empresas**
- Controle de orçamento e gastos
- Auditoria de compras
- Relatórios para diretoria

### **💼 Departamento de Compras**
- Comparar preços entre fornecedores
- Negociar melhores condições
- Consolidar compras

### **💰 Financeiro**
- Controlar despesas por categoria
- Projetar gastos futuros
- Identificar desvios orçamentários

### **📊 Analistas de Dados**
- Business intelligence de compras
- Análise de padrões temporais
- Relatórios automatizados

### **🧾 Contadores**
- Organizar documentação fiscal
- Verificar divergências
- Facilitar auditorias

---

## 🔒 Segurança e Privacidade

✅ **Dados Locais:** Todas as NF-e ficam no seu computador  
✅ **Conexão Segura:** IMAP com SSL/TLS  
✅ **Senha Criptografada:** Armazenamento seguro com Fernet  
✅ **LLM Opcional:** Escolha usar local (LM Studio) ou não usar  
✅ **Zero Cloud:** Nenhum dado enviado para servidores externos  
✅ **Open Source:** Código auditável pela comunidade  

---

## ❓ FAQ

<details>
<summary><b>Preciso ter LLM/IA para usar o SimpleNFE?</b></summary>

**Não!** O SimpleNFE funciona perfeitamente sem IA. Você terá:
- Extração automática de XML/PDF
- Buscas, filtros e agrupamentos
- Rankings e estatísticas
- Relatórios HTML profissionais

A IA é **opcional** para análises avançadas.
</details>

<details>
<summary><b>Funciona com Gmail corporativo?</b></summary>

Sim, desde que:
1. IMAP esteja habilitado (verifique com admin)
2. Políticas de segurança permitam
3. Use senha de app se 2FA estiver ativo
</details>

<details>
<summary><b>Como criar senha de app no Gmail?</b></summary>

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Segurança → Verificação em duas etapas
3. Senhas de app → Gerar nova
4. Use a senha gerada no SimpleNFE
</details>

<details>
<summary><b>O sistema funciona offline?</b></summary>

**Parcialmente:**
- ✅ Análise de arquivos locais (aba "Análise Local")
- ✅ Processamento de itens já extraídos
- ✅ Geração de relatórios
- ❌ Busca de novos e-mails (precisa de internet)
- ❌ Análise com LLM (se usar API externa)
</details>

<details>
<summary><b>Posso processar PDFs escaneados?</b></summary>

O sistema **detecta** PDFs escaneados e alerta. Para processar:
1. Use software OCR externo (Adobe, ABBYY)
2. Converta para PDF pesquisável
3. Importe no SimpleNFE
</details>

<details>
<summary><b>Como compartilhar plugins com a comunidade?</b></summary>

1. Crie seu plugin seguindo `PLUGIN_DEV_GUIDE.md`
2. Teste localmente
3. Poste no GitHub como Gist
4. Compartilhe o link no repositório (Issues/Discussions)
5. Ou faça Pull Request para o repo oficial
</details>

---

## 🛠️ Troubleshooting

### **Erro de autenticação Gmail**
- ✅ Verifique se IMAP está habilitado
- ✅ Use senha de app, não senha regular
- ✅ Desative temporariamente antivírus (pode bloquear)

### **LLM não conecta**
- ✅ Verifique se LM Studio está rodando
- ✅ Confirme que servidor local está ativo (porta 1234)
- ✅ Teste URL no navegador: `http://127.0.0.1:1234`

### **Erro "Can't find init.tcl" (Windows)**
- ✅ Reinstale Python oficial de [python.org](https://www.python.org/)
- ✅ Marque opção "tcl/tk and IDLE" na instalação
- ✅ Ou use Anaconda: `conda install tk`

### **Plugin não aparece**
- ✅ Arquivo está na pasta `plugins/`?
- ✅ Herda de `BasePlugin`?
- ✅ Clique em "🔄 Atualizar Lista"
- ✅ Veja erros no console/terminal

---

## 🤝 Contribuindo

Contribuições são bem-vindas! 🎉

### **Como Contribuir**

1. Fork o repositório
2. Crie uma branch: `git checkout -b minha-feature`
3. Commit suas mudanças: `git commit -m 'Adiciona feature X'`
4. Push: `git push origin minha-feature`
5. Abra um Pull Request

### **Áreas para Contribuir**

- 🐛 Reportar e corrigir bugs
- ✨ Propor novas funcionalidades
- 🧩 Criar plugins para a comunidade
- 📖 Melhorar documentação
- 🌍 Traduzir para outros idiomas
- 🎨 Aprimorar interface

---

## 📜 Licença

Este projeto é licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👤 Autor

**Ademir Red**
- GitHub: [@AdemirRed](https://github.com/AdemirRed)
- Repositório: [SimpleNFEScanEmail](https://github.com/AdemirRed/SimpleNFEScanEmail)

---

## ⭐ Apoie o Projeto

Se este projeto foi útil para você:

- ⭐ Dê uma **estrela** no GitHub
- 🐛 Reporte **bugs** ou sugira melhorias
- 🧩 Crie **plugins** para a comunidade
- 📢 **Compartilhe** com colegas e empresas
- 💬 Participe das **discussões**

---

## 🚀 Roadmap

### **Versão Atual (v1.0)**
- ✅ Extração automática XML/PDF
- ✅ Interface gráfica completa
- ✅ Análise com LLM opcional
- ✅ Sistema de plugins
- ✅ Relatórios HTML profissionais

### **Próximas Versões**
- 🔜 Suporte para Linux e macOS
- 🔜 Dashboard com gráficos interativos
- 🔜 Integração com outros provedores (Outlook, etc)
- 🔜 API REST para integrações
- 🔜 Repositório oficial de plugins
- 🔜 Modo multi-usuário/empresa
- 🔜 Análise de tendências temporais
- 🔜 Alertas e notificações automáticas

---

<div align="center">

**🚀 Transforme a gestão de suas notas fiscais hoje mesmo!**

*SimpleNFE - Inteligência em Gestão Fiscal*

[⬆ Voltar ao Topo](#-simplenfe---sistema-inteligente-de-gestão-de-notas-fiscais)

</div>
