"""
Script de teste de conexão IMAP Gmail
Testa as credenciais antes de usar no programa
"""
import imaplib
import json

# Carrega config
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

server = config['email']['server']
port = config['email']['port']
email = config['email']['address']
password = config['email']['app_password']

print("="*60)
print("TESTE DE CONEXÃO IMAP GMAIL")
print("="*60)
print(f"\nServidor: {server}")
print(f"Porta: {port}")
print(f"Email: {email}")
print(f"Senha: {'*' * (len(password)-4)}{password[-4:]}")
print(f"Tamanho da senha: {len(password)} caracteres")
print(f"Tem espaços: {' ' in password}")
print()

# Remove espaços
password_clean = password.replace(' ', '')
if password_clean != password:
    print(f"⚠️  AVISO: Senha tinha espaços! Removidos.")
    print(f"Tamanho após remover espaços: {len(password_clean)}")
    password = password_clean
    print()

# Testa conexão
print("Tentando conectar...")
try:
    # Conecta ao servidor
    conn = imaplib.IMAP4_SSL(server, port)
    print("✓ Conexão SSL estabelecida")
    
    # Tenta login
    print(f"Tentando login com: {email}")
    result = conn.login(email, password)
    print(f"✓ LOGIN SUCESSO! Resultado: {result}")
    
    # Seleciona INBOX
    status, data = conn.select('INBOX')
    if status == 'OK':
        count = int(data[0])
        print(f"✓ INBOX selecionada: {count} mensagens")
    
    # Logout
    conn.logout()
    print("✓ Logout OK")
    
    print()
    print("="*60)
    print("✓✓✓ TESTE PASSOU! CREDENCIAIS CORRETAS ✓✓✓")
    print("="*60)
    print("\nSuas credenciais estão corretas!")
    print("Se o programa ainda der erro, o problema é no código.")
    
except imaplib.IMAP4.error as e:
    print(f"\n✗ ERRO DE AUTENTICAÇÃO: {e}")
    print()
    print("="*60)
    print("POSSÍVEIS CAUSAS:")
    print("="*60)
    print("1. Senha de app incorreta ou expirada")
    print("2. Email incorreto")
    print("3. Verificação em 2 etapas não está ativada")
    print("4. IMAP não está habilitado no Gmail")
    print()
    print("SOLUÇÃO:")
    print("1. Vá em: https://myaccount.google.com/apppasswords")
    print("2. Gere uma NOVA senha de app")
    print("3. Copie os 16 caracteres SEM ESPAÇOS")
    print("4. Cole no config.json ou no programa")
    print()
    
except Exception as e:
    print(f"\n✗ ERRO INESPERADO: {e}")
    print(f"Tipo: {type(e).__name__}")

input("\nPressione Enter para sair...")
