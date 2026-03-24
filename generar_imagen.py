import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import json
import os
from datetime import datetime

# Conectar a Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Leer credenciales desde variable de entorno (GitHub Actions)
creds_json = os.environ.get('GOOGLE_CREDENTIALS')
if creds_json:
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
else:
    # Para correr localmente
    creds = Credentials.from_service_account_file("credenciales.json", scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("Rifa").sheet1

# Leer datos
datos = sheet.get_all_values()
numeros = datos[1:]

# Crear diccionario de estados
estados = {}
for fila in numeros:
    numero = fila[0]
    estado = fila[1] if fila[1] else "Disponible"
    estados[numero] = estado

# Configurar imagen
img = Image.new('RGB', (1200, 1400), 'white')
draw = ImageDraw.Draw(img)

# Colores
colores = {
    "Disponible": (76, 175, 80),   # Verde
    "Reservado": (255, 152, 0),    # Naranja
    "Vendido": (244, 67, 54)       # Rojo
}

# Tamaños
ancho_celda = 100
alto_celda = 100
inicio_x = 100
inicio_y = 150

# Título
draw.text((450, 30), "SUPER RIFA - PARA EQUIPAR MI BARBERÍA", fill=(30, 58, 95))
draw.text((480, 70), "NÚMEROS DEL 00 AL 99", fill=(201, 160, 61))

# Cuadrícula
for i in range(100):
    numero = f"{i:02d}"
    fila = i // 10
    columna = i % 10
    
    x = inicio_x + columna * ancho_celda
    y = inicio_y + fila * alto_celda
    
    color = colores.get(estados.get(numero, "Disponible"), (200, 200, 200))
    
    # Dibujar celda
    draw.rectangle([x, y, x + ancho_celda, y + alto_celda], fill=color, outline=(0, 0, 0))
    
    # Dibujar número
    draw.text((x + 35, y + 35), numero, fill=(255, 255, 255))

# Leyenda
leyenda_y = inicio_y + 10 * alto_celda + 30
draw.text((100, leyenda_y), "Leyenda:", fill=(0, 0, 0))
draw.rectangle([200, leyenda_y - 5, 250, leyenda_y + 25], fill=(76, 175, 80), outline=(0, 0, 0))
draw.text((260, leyenda_y), "= Disponible", fill=(0, 0, 0))
draw.rectangle([200, leyenda_y + 30, 250, leyenda_y + 60], fill=(255, 152, 0), outline=(0, 0, 0))
draw.text((260, leyenda_y + 35), "= Reservado", fill=(0, 0, 0))
draw.rectangle([200, leyenda_y + 65, 250, leyenda_y + 95], fill=(244, 67, 54), outline=(0, 0, 0))
draw.text((260, leyenda_y + 70), "= Vendido", fill=(0, 0, 0))

# Link a Streamlit
draw.text((100, leyenda_y + 120), "¡Elegí tu número acá!", fill=(30, 58, 95))
draw.text((100, leyenda_y + 150), "https://super-rifa.streamlit.app", fill=(201, 160, 61))

# Guardar
img.save("rifa_actualizada.png")
print(f"✅ Imagen generada: rifa_actualizada.png")
print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Estadísticas
disponibles = sum(1 for e in estados.values() if e == "Disponible")
reservados = sum(1 for e in estados.values() if e == "Reservado")
vendidos = sum(1 for e in estados.values() if e == "Vendido")

print(f"📊 Estadísticas:")
print(f"   🟢 Disponibles: {disponibles}")
print(f"   🟠 Reservados: {reservados}")
print(f"   🔴 Vendidos: {vendidos}")
