import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# ========== CONFIGURACIÓN ==========
REFRESH_INTERVAL_SECONDS = 600  # 10 minutos = 600 segundos

# ========== FUNCIÓN PARA GENERAR LA IMAGEN ==========
@st.cache_data(ttl=REFRESH_INTERVAL_SECONDS)
def generar_imagen_rifa():
    """
    Genera una imagen PNG con la cuadrícula de números actualizada.
    Se recarga automáticamente cada 10 minutos.
    """
    # Conectar a Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rifa").sheet1
    except Exception as e:
        return None, f"Error de conexión: {e}"
    
    # Leer datos actualizados
    datos = sheet.get_all_values()
    df = pd.DataFrame(datos[1:], columns=datos[0])
    
    # Crear diccionario de estados
    estados = {}
    for _, row in df.iterrows():
        estados[str(row['Número']).strip()] = row['Estado']
    
    # Configuración de la imagen
    ancho_celda = 60
    alto_celda = 60
    columnas = 10
    filas = 10
    
    ancho_total = ancho_celda * columnas + 40
    alto_total = alto_celda * filas + 80
    
    # Crear imagen
    img = Image.new('RGB', (ancho_total, alto_total), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Fuentes (usar fuente por defecto)
    try:
        fuente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        fuente_pequeña = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        fuente = ImageFont.load_default()
        fuente_pequeña = ImageFont.load_default()
    
    # Dibujar título
    draw.text((ancho_total//2 - 80, 10), "🎲 SUPER RIFA 🎲", fill='#1e3a5f', font=fuente)
    draw.text((ancho_total//2 - 100, 35), "Números disponibles", fill='#4a5568', font=fuente_pequeña)
    
    # Dibujar cuadrícula y números
    for fila in range(filas):
        for col in range(columnas):
            numero = f"{fila * columnas + col:02d}"
            estado = estados.get(numero, "Disponible")
            
            x0 = 20 + col * ancho_celda
            y0 = 70 + fila * alto_celda
            x1 = x0 + ancho_celda - 2
            y1 = y0 + alto_celda - 2
            
            # Color según estado
            if estado == "Disponible":
                color_fondo = '#10b981'  # Verde
                color_texto = 'white'
            elif estado == "Reservado":
                color_fondo = '#f59e0b'  # Naranja
                color_texto = 'white'
            else:
                color_fondo = '#ef4444'  # Rojo
                color_texto = 'white'
            
            # Dibujar celda
            draw.rectangle([x0, y0, x1, y1], fill=color_fondo, outline='white', width=1)
            
            # Dibujar número
            draw.text((x0 + ancho_celda//3, y0 + alto_celda//3), numero, fill=color_texto, font=fuente)
    
    # Guardar imagen en bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes, "Imagen generada correctamente"

# ========== FRAGMENTO QUE SE ACTUALIZA CADA 10 MINUTOS ==========
@st.fragment(run_every=REFRESH_INTERVAL_SECONDS)
def mostrar_imagen_actualizada():
    """
    Este fragmento se actualiza automáticamente cada 10 minutos.
    Muestra la imagen con los números actualizados.
    """
    st.markdown("### 📸 Imagen de la rifa (actualizada cada 10 minutos)")
    
    with st.spinner("Generando imagen actualizada..."):
        imagen_bytes, mensaje = generar_imagen_rifa()
    
    if imagen_bytes:
        st.image(imagen_bytes, caption="Números disponibles en tiempo real", use_container_width=True)
        st.caption(f"🕐 Última actualización: {time.strftime('%H:%M:%S')} - {mensaje}")
    else:
        st.error(mensaje)

# ========== RESTO DE LA APP (TABLA DE NÚMEROS INTERACTIVA) ==========
st.markdown('<div class="main-title">✂️ SUPER RIFA! ✂️</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">PARA EQUIPAR MI BARBERÍA</div>', unsafe_allow_html=True)

# ... (acá va el resto de tu código con los botones interactivos)

# ========== MOSTRAR LA IMAGEN QUE SE ACTUALIZA ==========
mostrar_imagen_actualizada()
