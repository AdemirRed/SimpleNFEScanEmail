# Correções Implementadas - Busca e Duplicação

## 🔧 Problemas Corrigidos

### 1. **Busca de Notas no Email Não Encontrando Arquivos**

#### Problema:
- A busca estava usando `self.cfg_include.get()` que não existia
- Deveria usar as configurações carregadas de `config.json`

#### Solução:
```python
# ANTES (errado):
include = [s.strip() for s in (self.cfg_include.get() or '').split(',') if s.strip()]
exclude = [s.strip() for s in (self.cfg_exclude.get() or '').split(',') if s.strip()]

# DEPOIS (correto):
include = self.cfg.get('search', {}).get('include_keywords', [])
exclude = self.cfg.get('search', {}).get('exclude_keywords', [])
```

#### Debug Adicionado:
- Prints no console mostrando:
  - Tipos de arquivo buscados (PDF/XML)
  - Quantidade de emails a verificar
  - Keywords de inclusão e exclusão
  - Cada anexo encontrado e por que foi aceito/rejeitado

**Para ver os logs**: Execute o programa via terminal e veja o console quando clicar em "Buscar"

---

### 2. **Duplicação de Itens ao Analisar PDF e XML da Mesma Nota**

#### Problema:
- Quando analisava PDF e XML da mesma nota fiscal, os itens apareciam duplicados
- Análise local usava `extend()` que adiciona tudo sem verificar duplicatas

#### Solução:
- Implementada deduplicação global na análise local
- Compara itens novos com os já existentes usando chave única:
  - documento + descrição + quantidade + valor_unit + valor_total
- Mostra quantos itens foram realmente adicionados vs. quantos eram duplicados

#### Código:
```python
# Pega chaves já existentes
existing_keys = set()
for it in self.extracted_items:
    key = (documento, descrição, quantidade, valor_unit, valor_total)
    existing_keys.add(key)

# Adiciona apenas itens novos (não duplicados)
for it in all_items:
    key = (...)
    if key not in existing_keys:
        self.extracted_items.append(it)
        new_items_count += 1
```

#### Mensagem:
Agora mostra: "X itens novos adicionados de Y arquivo(s). Z itens duplicados foram ignorados."

---

### 3. **Falta de Opção para Limpar Itens**

#### Problema:
- Não havia como limpar todos os itens extraídos
- Usuário tinha que fechar e reabrir o programa

#### Solução:
- Adicionado botão "Limpar Itens" na aba "Itens"
- Pede confirmação antes de limpar
- Remove todos os itens da lista

---

## 🧪 Como Testar

### Teste 1: Busca de Notas
1. Vá para "Configurações" e confira as palavras-chave
   - Padrão: `nfe, nf-e, nota, xml, danfe`
2. Envie um email para sua conta com anexo PDF ou XML de nota fiscal
3. Vá para "Pesquisa de Notas" e clique "Buscar"
4. **Verifique o console** - deve mostrar:
   ```
   [BUSCA] Tipos: ['PDF', 'XML']
   [BUSCA] Incluir keywords: ['nfe', 'nf-e', 'nota', 'xml', 'danfe']
   [GMAIL] Buscando em X emails mais recentes
   [GMAIL] UID XXX: 1 anexo(s) - ['arquivo.pdf']
   [GMAIL]   ✓ 'arquivo.pdf' ACEITO!
   ```
5. ✅ Deve aparecer na lista de resultados

### Teste 2: Deduplicação
1. Vá para "Análise Local"
2. Selecione um PDF e o XML da **mesma nota fiscal**
3. Clique "Analisar Arquivos"
4. ✅ Deve mostrar: "X itens novos adicionados. Y itens duplicados foram ignorados."
5. ✅ Na aba "Itens", cada produto deve aparecer apenas UMA vez

### Teste 3: Limpar Itens
1. Vá para aba "Itens" (com itens extraídos)
2. Clique "Limpar Itens"
3. ✅ Deve pedir confirmação
4. Clique "Sim"
5. ✅ Todos os itens são removidos

---

## 📋 Verificações se Busca Não Encontrar Nada

Se a busca não encontrar notas, verifique no console:

1. **Emails sendo escaneados?**
   ```
   [GMAIL] Buscando em 100 emails mais recentes
   ```
   Se mostrar 0, pode não ter emails na INBOX

2. **Anexos sendo encontrados?**
   ```
   [GMAIL] UID 12345: 2 anexo(s) - ['nota.pdf', 'boleto.pdf']
   ```
   Se não aparecer nenhum, os emails não têm anexos

3. **Por que foi rejeitado?**
   ```
   [GMAIL]   - 'boleto.pdf' não contém keywords ['nfe', 'nota'], pulando
   ```
   Se aparecer isso, o nome do arquivo não contém as keywords

### Solução: Ajustar Keywords

Se seus arquivos têm nomes diferentes (ex: "danfe", "fiscal", etc):

1. Vá para "Configurações"
2. Adicione na linha "Palavras-chave (incluir)":
   ```
   nfe, nf-e, nota, xml, danfe, fiscal, eletronica
   ```
3. Salve
4. Tente buscar novamente

---

## 🎯 Resumo das Mudanças

### `app.py`
- ✅ Corrigido para usar `self.cfg['search']['include_keywords']` 
- ✅ Adicionada deduplicação na análise local
- ✅ Adicionado botão "Limpar Itens"
- ✅ Adicionado método `_clear_items()`
- ✅ Debug prints na busca

### `modules/email_gmail.py`
- ✅ Simplificada lógica de filtro de keywords
- ✅ Debug prints extensivos mostrando cada passo
- ✅ Aceita arquivos mesmo sem keywords se lista estiver vazia

---

## 💡 Dica: Ver Logs Durante Execução

**Windows (PowerShell):**
```powershell
cd "C:\Users\RedBlack-PC\Desktop\OnnNotaFiscalEletronica\SimpleNFE"
python app.py
```

Deixe o terminal aberto e use o programa. Todas as mensagens de debug aparecerão no terminal.
