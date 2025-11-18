# ⌨️ Atalhos de Teclado - SimpleNFE

## 📋 Atalhos de Plugins

Configure teclas de atalho para executar plugins rapidamente sem usar o mouse!

### 🎯 Atalhos Sugeridos

Estas são sugestões de atalhos que funcionam bem. Você pode personalizar conforme sua preferência:

| Plugin | Atalho Sugerido | Descrição |
|--------|----------------|-----------|
| 📊 Calculadora de Estatísticas | `F5` | Estatísticas avançadas dos valores |
| 📊 Exportador Excel | `Control-e` | Exporta para planilha Excel |
| 🔍 Busca Rápida | `Control-f` | Abre janela de busca |
| 🏢 Contador por Fornecedor | `Control-Shift-f` | Ranking de fornecedores |

### 📝 Como Configurar

1. **Abra o Gerenciador de Plugins:**
   - Aba "Itens" → Botão "🧩 Plugins"

2. **Selecione um plugin** na lista

3. **Clique no botão "⌨️ Atalho"**

4. **Digite o atalho desejado:**
   - Formato: `Control-letra`, `Alt-letra`, ou `F1-F12`
   - Exemplo: `Control-e` (para Ctrl+E)

5. **Clique em "Salvar"**

6. **Pronto!** Use o atalho em qualquer lugar do app

### 🎹 Formatos de Atalho Aceitos

#### **Teclas Control (Ctrl)**
```
Control-a → Ctrl+A
Control-e → Ctrl+E
Control-s → Ctrl+S
Control-p → Ctrl+P
```

#### **Teclas Shift + Control**
```
Control-Shift-a → Ctrl+Shift+A
Control-Shift-e → Ctrl+Shift+E
Control-Shift-s → Ctrl+Shift+S
```

#### **Teclas Alt**
```
Alt-a → Alt+A
Alt-p → Alt+P
Alt-b → Alt+B
```

#### **Teclas de Função**
```
F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12
```

### ⚠️ Atalhos Reservados pelo Sistema

**Evite usar estes atalhos** (já usados pelo Windows/sistema):

- `Control-c` (Copiar)
- `Control-v` (Colar)
- `Control-x` (Recortar)
- `Control-z` (Desfazer)
- `Control-a` (Selecionar tudo)
- `Alt-F4` (Fechar janela)
- `Alt-Tab` (Trocar janelas)

### ✨ Dicas

1. **Use F5-F12** para atalhos rápidos sem conflitos

2. **Combine Control+Shift** para funções avançadas
   - Ex: `Control-e` = exportar normal
   - Ex: `Control-Shift-e` = exportar avançado

3. **Alt + letra** é bom para ações menos frequentes

4. **Letras mnemônicas** ajudam a lembrar:
   - `Control-e` = **E**xportar
   - `Control-f` = **F**iltar/Buscar (**F**ind)
   - `Control-s` = E**s**tatísticas/Salvar (**S**ave)

### 🔄 Gerenciar Atalhos

#### **Ver atalhos configurados:**
- Abra o gerenciador de plugins
- Atalhos aparecem ao lado do nome: `Plugin (Control-e)`

#### **Remover um atalho:**
1. Selecione o plugin
2. Clique em "⌨️ Atalho"
3. Clique em "🗑️ Remover"

#### **Alterar um atalho:**
1. Selecione o plugin
2. Clique em "⌨️ Atalho"
3. Digite o novo atalho
4. Clique em "Salvar" (substitui o anterior)

### 🛡️ Validações de Segurança

O sistema **valida automaticamente**:

- ✅ Formato correto do atalho
- ✅ Conflitos com outros plugins (não permite duplicatas)
- ✅ Plugin precisa estar **habilitado** para usar atalho
- ✅ Aviso se tentar usar atalho de plugin desabilitado

### 📊 Configuração Avançada

Os atalhos são salvos em:
```
plugins/plugin_config.json
```

Formato:
```json
{
  "exemplo_exportador_excel": {
    "enabled": true,
    "shortcut": "Control-e"
  },
  "calculadora_simples": {
    "enabled": true,
    "shortcut": "F5"
  }
}
```

Você pode editar manualmente, mas **use o gerenciador** para evitar erros.

### 🎯 Casos de Uso

#### **Workflow Rápido:**

1. Extraia itens de NF-e
2. Pressione `F5` → Estatísticas instantâneas
3. Pressione `Control-f` → Busca rápida de produto
4. Pressione `Control-e` → Exporta para Excel

**Tempo total: ~10 segundos sem tocar no mouse!** 🚀

#### **Análise Express:**

1. `Control-Shift-f` → Ranking de fornecedores
2. `F5` → Estatísticas detalhadas
3. `Control-e` → Exportar tudo

### 💡 Sugestões da Comunidade

Compartilhe seus atalhos favoritos!

**Para analistas financeiros:**
- `F5` = Estatísticas
- `F6` = Gráficos (se criar plugin)
- `F7` = Exportar relatório

**Para gestores de compras:**
- `Control-f` = Busca fornecedor
- `Control-Shift-f` = Ranking fornecedores
- `Control-p` = Comparador de preços (se criar plugin)

**Para contadores:**
- `Control-e` = Excel
- `Control-h` = HTML
- `Control-t` = Totalizador (se criar plugin)

---

## 🔥 Produtividade Máxima

**Antes (sem atalhos):**
1. Clicar em "Plugins"
2. Procurar plugin na lista
3. Selecionar
4. Clicar em "Executar"
5. Esperar janela abrir

⏱️ Tempo: ~5-7 segundos

**Depois (com atalhos):**
1. Pressionar `F5`

⏱️ Tempo: **0.2 segundos** 

**Ganho: 25x mais rápido!** ⚡

---

## 📞 Suporte

Dúvidas sobre atalhos?
- Veja exemplos no gerenciador de plugins
- Consulte este guia
- Abra uma issue no GitHub

**Bom trabalho com atalhos! 🚀**
