# 📦 SimpleNFE - Sistema Inteligente de Gestão de Notas Fiscais

## 🎯 O que é o SimpleNFE?

O SimpleNFE é um **sistema profissional de gestão e análise de notas fiscais eletrônicas (NF-e)** desenvolvido em Python. Ele automatiza a extração, organização e análise de informações de compras a partir de e-mails com anexos XML e PDF de notas fiscais.

O sistema oferece duas modalidades de uso: **com inteligência artificial (LLM)** para análises avançadas, ou **sem LLM** para funcionalidades essenciais de gestão.

---

## 💡 Por que usar o SimpleNFE?

### **Benefícios Principais:**

1. **Economia de Tempo**: Automatiza a leitura de dezenas/centenas de notas fiscais que levaria horas manualmente
2. **Organização Centralizada**: Todos os itens de compra em um único lugar, fácil de buscar e filtrar
3. **Análise Profissional**: Relatórios HTML formatados prontos para apresentação gerencial
4. **Tomada de Decisão**: Identifica padrões de compra, produtos mais caros, fornecedores principais
5. **Controle Financeiro**: Monitora gastos por categoria, fornecedor ou período

---

## 🤖 Casos de Uso COM Inteligência Artificial (LLM)

Quando conectado a uma LLM (via LM Studio ou similar), o SimpleNFE se torna uma **ferramenta de business intelligence avançada**:

### **1. Análise Inteligente de Compras**
- **O que faz**: A IA analisa todos os itens extraídos e gera insights estratégicos
- **Exemplo prático**: 
  - "Detectamos que você compra papel A4 de 3 fornecedores diferentes. O Fornecedor X oferece 15% mais barato que os outros."
  - "Seus gastos com material de limpeza aumentaram 40% nos últimos 3 meses."

### **2. Recomendações de Otimização**
- **O que faz**: A IA sugere formas de economizar ou melhorar processos
- **Exemplo prático**:
  - "Recomendamos consolidar compras de canetas no Fornecedor Y para obter desconto por volume"
  - "Itens eletrônicos têm margem de negociação: produtos similares variam até 25% de preço"

### **3. Instruções Personalizadas**
- **O que faz**: Você pode configurar instruções customizadas para a IA analisar aspectos específicos
- **Exemplos de templates inclusos**:
  - **Análise Financeira**: Foca em custos, valores médios, tendências de preços
  - **Gestão de Estoque**: Identifica produtos com baixa rotação ou estoque crítico
  - **Análise de Fornecedores**: Compara fornecedores por preço, qualidade, prazo
  - **Oportunidades de Negociação**: Encontra onde você pode negociar melhores condições

### **4. Relatórios Executivos**
- **O que faz**: Gera resumos profissionais em HTML com análise da IA
- **Exemplo prático**: Relatório mostrando:
  - Estatísticas calculadas (total gasto, número de itens, valores médios)
  - Análise interpretativa da IA (tendências, alertas, recomendações)
  - Formatação profissional pronta para compartilhar com gestores

### **5. Identificação de Padrões**
- **O que faz**: A IA detecta padrões que seriam difíceis de perceber manualmente
- **Exemplo prático**:
  - "Você compra toner de impressora sempre no final do mês quando os preços estão 10% mais altos"
  - "O produto X está sendo comprado em quantidades decrescentes nos últimos 6 meses"

---

## 📊 Casos de Uso SEM Inteligência Artificial

**Importante**: Mesmo sem LLM, o SimpleNFE continua sendo uma ferramenta valiosa! Ele oferece funcionalidades essenciais de gestão:

### **1. Extração Automática**
- Lê e-mails com anexos de NF-e (XML e PDF)
- Extrai automaticamente: produtos, quantidades, valores, fornecedores, datas
- Suporta PDFs escaneados (detecta e alerta para processamento manual)

### **2. Visualização Organizada**
- Tabela completa com todos os itens extraídos
- Colunas: Descrição, Quantidade, Unidade, Valor Unitário, Valor Total, Fornecedor, Data
- Interface profissional e intuitiva

### **3. Busca Avançada**
- Busca por palavra-chave em qualquer campo
- Encontre rapidamente produtos específicos
- Exemplo: Buscar "toner" para ver todas as compras de toner

### **4. Filtros Inteligentes**
- Filtre por fornecedor específico
- Filtre por faixa de valor (ex: itens entre R$ 100 e R$ 500)
- Filtre por período (ex: compras de janeiro a março)

### **5. Agrupamentos**
- **Por Fornecedor**: Veja tudo que você comprou de cada fornecedor
- **Por Produto**: Agrupe itens similares e veja totais
- Útil para negociações e análise de gastos

### **6. Rankings**
- **Top 10 Mais Caros**: Identifique produtos de maior impacto no orçamento
- **Top 10 Maior Quantidade**: Veja os produtos mais comprados
- Perfeito para priorizar negociações

### **7. Estatísticas Rápidas**
- Total de itens extraídos
- Valor total gasto
- Número de fornecedores
- Valor médio por item
- Item mais caro e mais frequente

### **8. Exportação HTML**
- Gera relatórios HTML profissionais
- Formatação com CSS moderno
- Pronto para imprimir ou compartilhar
- Inclui todas as estatísticas e dados

---

## 🔧 Funcionalidades Técnicas

### **Monitoramento de E-mail**
- Conecta via IMAP ao Gmail
- Busca e-mails com anexos XML/PDF de NF-e
- Filtra por remetentes específicos (configurável)
- Processa automaticamente novos e-mails

### **Processamento de Documentos**
- **XML**: Extração direta da estrutura da NF-e
- **PDF**: Extração de texto com pypdf2
- **PDFs Escaneados**: Detecta e alerta para processamento manual/OCR

### **Interface Gráfica (Tkinter)**
- Toolbar profissional com ícones
- Tabelas responsivas
- Diálogos de filtro e configuração
- Janelas dedicadas para análises específicas

### **Integração com LLM**
- Conecta via API HTTP (LM Studio)
- Configuração de URL, modelo e contexto
- Processamento em chunks para grandes volumes
- Combina análises parciais em resumo final

---

## 📋 Arquitetura do Sistema

```
SimpleNFE/
├── app.py                      # Interface principal e lógica de negócio
├── cli_extract.py              # Extração via linha de comando
├── config.json                 # Configurações (e-mail, LLM, etc)
├── modules/
│   ├── email_gmail.py          # Monitoramento de e-mail
│   ├── xml_pdf_extractor.py    # Extração de XML/PDF
│   ├── llm_analyzer.py         # Análise com IA
│   └── html_exporter.py        # Geração de relatórios
└── ui/
    ├── email_viewer.py         # Visualizador de e-mails
    └── theme.py                # Estilos da interface
```

---

## 🚀 Fluxo de Trabalho

### **Com LLM:**
1. Conectar ao e-mail → Extrair NF-e → Visualizar itens
2. Clicar em "🤖 Gerar Resumo LLM"
3. (Opcional) Adicionar instruções personalizadas
4. Aguardar análise da IA
5. Visualizar insights e recomendações
6. Exportar relatório HTML profissional com análise

### **Sem LLM:**
1. Conectar ao e-mail → Extrair NF-e → Visualizar itens
2. Usar buscas, filtros e agrupamentos
3. Analisar rankings (Top 10)
4. Ver estatísticas rápidas
5. Exportar relatório HTML com dados organizados

---

## 🎯 Quem deve usar?

### **Empresas de Pequeno e Médio Porte**
- Gerenciar compras e controlar gastos
- Identificar oportunidades de economia
- Gerar relatórios para diretoria

### **Departamentos de Compras**
- Comparar fornecedores
- Negociar melhores condições
- Consolidar compras

### **Departamentos Financeiros**
- Controlar orçamento
- Auditar despesas
- Projetar gastos futuros

### **Analistas de Dados**
- Analisar padrões de compra
- Gerar insights estratégicos
- Automatizar relatórios periódicos

### **Contadores e Consultores**
- Organizar documentação fiscal
- Analisar custos de clientes
- Fornecer consultoria baseada em dados

---

## 💪 Principais Diferenciais

1. **Gratuito e Open Source**: Sem custos de licença
2. **Funciona Offline**: Dados não saem do seu computador (exceto conexão LLM opcional)
3. **Personalizável**: Código aberto para adaptar às suas necessidades
4. **Sem Dependência de IA**: Funcional mesmo sem LLM
5. **Relatórios Profissionais**: HTML moderno e bem formatado
6. **Interface Amigável**: Fácil de usar, sem necessidade de programação

---

## 📈 Exemplo Real de Uso

**Cenário**: Empresa com 150 NF-e de compras em 3 meses

**Sem SimpleNFE**:
- Tempo manual: ~20 horas para abrir, ler e tabular
- Análise limitada: Planilhas básicas sem insights
- Erros: Risco de digitação incorreta

**Com SimpleNFE (sem LLM)**:
- Tempo: ~15 minutos para processar tudo automaticamente
- Análise: Agrupamentos, rankings, estatísticas instantâneas
- Precisão: Dados extraídos diretamente dos XMLs

**Com SimpleNFE (com LLM)**:
- Tempo total: ~20 minutos (15 min extração + 5 min análise IA)
- Análise: Insights estratégicos como:
  - "Fornecedor X cobra 18% mais caro que a média do mercado em materiais de escritório"
  - "Recomendamos renegociar contrato com Fornecedor Y devido ao volume de compras"
  - "Oportunidade: Consolidar compras de produto Z pode gerar economia de R$ 3.500/ano"

---

## 🔒 Segurança e Privacidade

- **Dados locais**: Todas as NF-e ficam no seu computador
- **E-mail seguro**: Conexão IMAP com senha de app do Gmail
- **LLM opcional**: Você escolhe se envia dados para análise (pode usar LM Studio local)
- **Sem cloud forçado**: Nenhum dado é enviado para servidores externos sem seu controle

---

## 📝 Conclusão

O **SimpleNFE** é uma solução completa para gestão inteligente de notas fiscais eletrônicas. Seja você uma pequena empresa querendo organizar compras, ou um analista buscando insights avançados com IA, o sistema oferece ferramentas profissionais para:

- ✅ **Economizar tempo** com automação
- ✅ **Reduzir custos** com análise de compras
- ✅ **Melhorar decisões** com dados organizados
- ✅ **Profissionalizar gestão** com relatórios executivos

**Use COM LLM para inteligência avançada, ou SEM LLM para gestão essencial. Em ambos os casos, você terá uma ferramenta poderosa de business intelligence para suas notas fiscais!** 🚀
