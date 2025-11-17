"""
Gera um ícone simples para o SimpleNFE
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Tamanhos de ícone padrão
sizes = [16, 32, 48, 64, 128, 256]

# Cria ícone principal (256x256)
img = Image.new('RGB', (256, 256), color='#2C3E50')
draw = ImageDraw.Draw(img)

# Desenha um documento/nota
# Retângulo branco (papel)
draw.rectangle([60, 40, 196, 216], fill='white', outline='#34495E', width=3)

# Linhas do documento
for i in range(4):
    y = 80 + i * 30
    draw.rectangle([80, y, 176, y+4], fill='#3498DB')

# Desenha símbolo $ (fiscal)
try:
    # Tenta usar fonte grande
    font = ImageFont.truetype("arial.ttf", 80)
except:
    font = ImageFont.load_default()

# Desenha $ centralizado
draw.text((128, 128), "$", fill='#E74C3C', font=font, anchor="mm")

# Salva em vários tamanhos
images = []
for size in sizes:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    images.append(resized)

# Salva como .ico
icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
img.save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])

print(f"✓ Ícone criado: {icon_path}")
print(f"  Tamanhos: {sizes}")
