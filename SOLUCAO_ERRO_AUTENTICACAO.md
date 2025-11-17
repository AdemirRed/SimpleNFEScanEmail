# 🔧 Solução: Erro de Autenticação IMAP Gmail

## ❌ Erro que Você Está Vendo

```
Falha ao conectar/listar: [AUTHENTICATIONFAILED] Invalid credentials (Failure)
```

## ✅ SOLUÇÃO PASSO A PASSO

### 1. Verificar se a Senha de App Está Correta

A senha de app do Gmail:
- ✅ Tem **exatamente 16 caracteres**
- ✅ Não tem espaços
- ✅ É diferente da sua senha normal do Gmail
- ✅ Formato: `aaaa bbbb cccc dddd` (mas você deve digitar **sem espaços**)

**Sua senha atual no config.json:** `nzerswzdpqfxxkbv`
- ✅ Tem 16 caracteres
- ✅ Sem espaços

Se essa senha não funcionar, você precisa **gerar uma nova**.

---

### 2. Gerar Nova Senha de App (Método Correto)

#### Opção A: Via Link Direto
1. Abra: https://myaccount.google.com/apppasswords
2. Faça login com sua conta Gmail
3. Em "Nome do app", digite: `SimpleNFE`
4. Clique em "Criar"
5. **COPIE A SENHA** (16 caracteres, sem espaços)
6. Cole no SimpleNFE na aba "Configurações"

#### Opção B: Via Segurança do Google
1. Acesse: https://myaccount.google.com/security
2. Role até "Como fazer login no Google"
3. Clique em "Senhas de app"
4. Pode pedir para fazer login novamente
5. Selecione app: "Outro (nome personalizado)"
6. Digite: `SimpleNFE`
7. Clique em "Gerar"
8. **COPIE A SENHA** (aparecerá sem espaços)

---

### 3. Verificar se a Verificação em 2 Etapas Está Ativa

**IMPORTANTE:** Senhas de app só funcionam se você tiver a verificação em 2 etapas ativada!

#### Verificar:
1. Vá em: https://myaccount.google.com/security
2. Procure por "Verificação em duas etapas"
3. Deve estar **ATIVADA**

#### Se estiver DESATIVADA:
1. Clique em "Verificação em duas etapas"
2. Siga o processo para ativar
3. Depois volte e gere a senha de app

---

### 4. Configurar no SimpleNFE

1. Abra o SimpleNFE
2. Vá para aba **"Configurações"**
3. Preencha:
   ```
   Servidor IMAP: imap.gmail.com
   Porta: 993
   Endereço de Email: seu_email@gmail.com
   Senha de App: [cole aqui a senha de 16 caracteres]
   ```
4. **Use o botão "👁️ Mostrar"** para ver se copiou corretamente
5. Clique em "Salvar Configurações"

---

### 5. Testar Conexão

1. Vá para aba **"Conexão"**
2. Clique em "Conectar e Listar"
3. Deve aparecer: "Total na INBOX: XXX"

---

## 🚨 Erros Comuns e Soluções

### Erro: "Invalid credentials"
**Causa:** Senha incorreta ou não é uma senha de app
**Solução:** Gere uma NOVA senha de app seguindo o passo 2

### Erro: "Too many login failures"
**Causa:** Muitas tentativas com senha errada
**Solução:** Aguarde 15 minutos e tente novamente com senha correta

### Erro: Não consigo acessar "Senhas de app"
**Causa:** Verificação em 2 etapas não está ativada
**Solução:** Ative a verificação em 2 etapas primeiro (passo 3)

### Erro: Senha some ou fica vazia no config.json
**Causa:** Arquivo sendo editado manualmente com erro
**Solução:** Use APENAS a interface do programa para salvar a senha

---

## 📝 Checklist Completo

- [ ] Verificação em 2 etapas está **ATIVADA**
- [ ] Gerei uma **NOVA** senha de app
- [ ] A senha tem **16 caracteres SEM ESPAÇOS**
- [ ] Copiei e colei a senha (não digitei manualmente)
- [ ] Usei o botão "👁️ Mostrar" para verificar se está correta
- [ ] Email está correto (com @gmail.com)
- [ ] Servidor é `imap.gmail.com` e porta é `993`
- [ ] Cliquei em "Salvar Configurações"
- [ ] Testei na aba "Conexão"

---

## 🔐 Exemplo de Config.json Correto

```json
{
  "email": {
    "server": "imap.gmail.com",
    "port": 993,
    "address": "seu_email@gmail.com",
    "app_password": "abcdefghijklmnop"  ← 16 caracteres, sem espaços
  }
}
```

---

## ❓ Ainda Não Funciona?

1. **Revogue senhas antigas:**
   - Vá em https://myaccount.google.com/apppasswords
   - Remova senhas antigas do SimpleNFE
   - Gere uma NOVA

2. **Teste com outro programa:**
   - Use Thunderbird ou Outlook para testar as mesmas credenciais
   - Se não funcionar lá também, o problema é com o Gmail

3. **Verifique se o IMAP está habilitado:**
   - Acesse Gmail pelo navegador
   - Configurações → Ver todas as configurações
   - Aba "Encaminhamento e POP/IMAP"
   - "Ativar IMAP" deve estar marcado

4. **Conta de trabalho/escola?**
   - Contas corporativas podem ter IMAP desabilitado
   - Entre em contato com o administrador

---

## 💡 Dica: Botão "Mostrar Senha"

O programa agora tem um botão **"👁️ Mostrar"** ao lado do campo de senha!

- Clique para **ver** a senha digitada
- Clique novamente para **ocultar**
- Use para verificar se copiou corretamente

---

**Última atualização:** 17/11/2025
