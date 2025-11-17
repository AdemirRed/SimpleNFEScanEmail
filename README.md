# SimpleNFE (Gmail)

Aplicativo simples em Tkinter para:
- Conectar ao Gmail via IMAP
- Listar os últimos emails (aba Conexão)
- Buscar notas (PDF e/ou XML) com filtros por palavras-chave (aba Pesquisa)
- Carregar resultados, baixar anexos e extrair itens (XML via parser; PDF via LM Studio) (aba Extração)
- Visualizar itens extraídos com totais (aba Itens)
- Ajustar credenciais, palavras-chave e parâmetros do LM Studio (aba Configurações)

## Pré-requisitos
- Python 3.10+
- IMAP habilitado no Gmail
- Recomenda-se usar senha de app (2FA habilitado). Veja: https://support.google.com/accounts/answer/185833

## Como executar
No Windows (PowerShell):

```powershell
python .\SimpleNFE\app.py
```

A UI abrirá com 5 abas:
- Conexão: informe a quantidade e clique "Conectar e Listar" para ver os últimos emails. Dê duplo clique para abrir o visualizador do email.
- Pesquisa de Notas: marque PDF e/ou XML, escolha a quantidade, clique "Buscar". Os resultados aparecem na tabela, com barra de progresso. Duplo clique abre o email.
- Extração: clique "Carregar da Pesquisa", selecione alguns ou use "Selecionar Todos" e então "Extrair Selecionados". Os anexos serão baixados e os itens extraídos.
- Itens: mostra a tabela de itens com totalização.
- Configurações: ajuste servidor/porta/email/senha de app, listas de palavras-chave (incluir/ignorar) e também a URL/modelo do LM Studio. Clique "Salvar Configurações".

Para extração de PDF é necessário ter o LM Studio em execução (Local Server):
- URL padrão: http://127.0.0.1:1234
- Modelo sugerido: openai/gpt-oss-20b

Instale as dependências opcionais (PDF, HTTP, tema escuro e renderização HTML):

```powershell
pip install -r .\SimpleNFE\requirements.txt
```

Notas sobre as bibliotecas opcionais:
- `sv-ttk`: tema escuro moderno (recomendado)
- `tkinterweb` ou `tkhtmlview`: renderização HTML em emails (recomendado para visualização rica)
- Se essas libs não estiverem instaladas, o app usará fallbacks (tema escuro básico e texto puro em emails).

## Observações
- Para Gmail corporativo, confirme permissões de IMAP e políticas do admin.
- Erros de autenticação são comuns se a senha de app não estiver configurada corretamente.
- Se houver problemas com Tkinter/Tcl no Windows (erro "Can't find a usable init.tcl"), reinstale o Python oficial de https://www.python.org/ e marque a opção "tcl/tk and IDLE" durante a instalação. Alternativamente, use um ambiente Conda e instale `tk`.

## Modo CLI (sem interface)
Se quiser testar sem o Tkinter, use o script de linha de comando:

```powershell
python .\SimpleNFE\cli_extract.py --limit 20 --types pdf,xml
```

Opções úteis:
- `--limit` quantidade de emails a varrer (padrão 20)
- `--types` "pdf,xml" (padrão ambos)
- `--include` e `--exclude` listas separadas por vírgula; se omitidas, usa as da `config.json`

O resultado é salvo em `SimpleNFE/temp/out_items.json` com os itens extraídos e um resumo no console.
