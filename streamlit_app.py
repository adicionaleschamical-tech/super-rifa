import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# ========== CSS ==========
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%); }
.main-title { text-align: center; font-size: 2.2em; font-weight: 800; background: linear-gradient(135deg, #1e3a5f, #2c5282); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.sub-title { text-align: center; font-size: 1.2em; color: #4a5568; margin-top: -10px; }
.premio-card { background: white; border-radius: 20px; padding: 15px 10px; text-align: center; box-shadow: 0 5px 20px rgba(0,0,0,0.08); margin: 5px; }
.premio-numero { background: #1e3a5f; color: white; width: 35px; height: 35px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 10px; font-size: 14px; }
.info-card { background: #1e3a5f; border-radius: 20px; padding: 20px; color: white; text-align: center; margin: 15px 0; }
.precio-destacado { font-size: 1.8em; font-weight: bold; color: #c9a03d; }
.promo-oferta { background: #c9a03d; border-radius: 20px; padding: 15px; text-align: center; margin: 15px 0; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
.sorteo-texto { text-align: center; margin-top: 20px; padding: 12px; background: #1e3a5f; border-radius: 15px; color: white; font-size: 14px; }
.pago-texto { text-align: center; margin-top: 15px; padding: 15px; background: #1e3a5f; border-radius: 15px; color: white; }
.alias-destacado { font-size: 1.3em; font-weight: bold; color: #c9a03d; background: rgba(255,255,255,0.1); display: inline-block; padding: 6px 16px; border-radius: 30px; }
.orientacion-box { background: #fef3c7; border-left: 5px solid #c9a03d; padding: 15px; margin: 20px 0; border-radius: 12px; text-align: center; }

/* Botones */
.stButton button {
    background-color: #10b981 !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 5px !important;
    font-size: 15px !important;
    font-weight: bold !important;
    width: 100% !important;
    cursor: pointer !important;
}

.stButton button:hover {
    background-color: #059669 !important;
}

.stButton button:disabled {
    background-color: #f59e0b !important;
    cursor: not-allowed !important;
}

button[kind="secondary"][disabled] {
    background-color: #ef4444 !important;
}

@media (max-width: 768px) {
    .stButton button {
        padding: 10px 3px !important;
        font-size: 13px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ========== TÍTULO ==========
st.markdown('<div class="main-title">✂️ SUPER RIFA! ✂️</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">PARA EQUIPAR MI BARBERÍA</div>', unsafe_allow_html=True)

# ========== PREMIOS ==========
col1, col2, col3, col4, col5 = st.columns(5)
premios_texto = ["JARRA TÉRMICA<br>2 litros", "ROPA INTERIOR<br>Conjunto femenino", "TIENDA GABRIELA<br>Premio sorpresa", "BARBERÍA CANICHE<br>Corte de pelo", "PASTAFROLA<br>Una pastafrola"]
for i, col in enumerate([col1, col2, col3, col4, col5]):
    with col:
        st.markdown(f'<div class="premio-card"><div class="premio-numero">{i+1}°</div>{premios_texto[i]}</div>', unsafe_allow_html=True)

st.markdown('<div class="info-card"><h3>🎲 NÚMEROS DEL 00 AL 99</h3><div class="precio-destacado">$3.000 CADA NÚMERO</div></div>', unsafe_allow_html=True)
st.markdown('<div class="promo-oferta"><p>🎁 ¡PROMOCIÓN ESPECIAL! 🎁</p><span>2 NÚMEROS POR $5.000</span></div>', unsafe_allow_html=True)

# ========== MENSAJE DE ORIENTACIÓN ==========
st.markdown("""
<div class="orientacion-box">
    📱 <strong>¿Usás el celular?</strong><br>
    🔄 <strong>GIRÁ LA PANTALLA A HORIZONTAL (landscape)</strong> para ver los números en grilla
</div>
""", unsafe_allow_html=True)

# ========== CONEXIÓN GOOGLE SHEETS ==========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("Rifa").sheet1
except Exception as e:
    st.error(f"❌ Error de conexión: {str(e)}")
    st.stop()

# Leer datos
datos = sheet.get_all_values()
df = pd.DataFrame(datos[1:], columns=datos[0])

st.markdown("### 🎲 ¡ELEGÍ TUS NÚMEROS!")
st.markdown("🟢 **Verde = Disponible** | 🟠 **Reservado** | 🔴 **Vendido**")

# Inicializar número seleccionado
if 'numero_seleccionado' not in st.session_state:
    st.session_state.numero_seleccionado = None

# ========== BOTONES INTERACTIVOS (5 COLUMNAS x 20 FILAS) ==========
for fila in range(20):
    columnas = st.columns(5)
    for col_idx in range(5):
        numero_num = fila * 5 + col_idx
        if numero_num <= 99:
            numero = f"{numero_num:02d}"
            
            estado = "Disponible"
            for _, row in df.iterrows():
                if str(row['Número']).strip() == numero:
                    estado = row['Estado']
                    break
            
            with columnas[col_idx]:
                if estado == "Disponible":
                    if st.button(f"🟢 {numero}", key=f"btn_{numero}", use_container_width=True):
                        st.session_state.numero_seleccionado = numero
                        st.rerun()
                elif estado == "Reservado":
                    st.button(f"🟠 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)
                else:
                    st.button(f"🔴 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)

# ========== FORMULARIO DE RESERVA ==========
if st.session_state.numero_seleccionado:
    numero_sel = st.session_state.numero_seleccionado
    
    datos_actuales = sheet.get_all_values()
    estado_actual = "Disponible"
    fila_numero = None
    for idx, fila in enumerate(datos_actuales[1:], start=2):
        if fila[0] == numero_sel:
            estado_actual = fila[1]
            fila_numero = idx
            break
    
    if estado_actual != "Disponible":
        st.error(f"❌ El número {numero_sel} ya no está disponible.")
        st.session_state.numero_seleccionado = None
        st.rerun()
    else:
        with st.form("compra_form"):
            st.markdown(f"### ✨ Número seleccionado: **{numero_sel}**")
            nombre = st.text_input("📝 Nombre completo")
            dni = st.text_input("🆔 DNI")
            telefono = st.text_input("📱 Teléfono *")
            st.markdown('<div style="background:#f7f9fc;padding:15px;border-radius:15px;border-left:4px solid #c9a03d"><strong>💰 PAGO:</strong> Transferencia al alias <strong style="color:#c9a03d">Tomas.130611</strong></div>', unsafe_allow_html=True)
            
            if st.form_submit_button("✅ RESERVAR", use_container_width=True):
                if not telefono:
                    st.error("❌ El teléfono es obligatorio")
                else:
                    try:
                        sheet.update_cell(fila_numero, 2, "Reservado")
                        sheet.update_cell(fila_numero, 3, nombre or "")
                        sheet.update_cell(fila_numero, 4, dni or "")
                        sheet.update_cell(fila_numero, 5, telefono)
                        
                        st.success(f"✅ ¡Número {numero_sel} reservado con éxito!")
                        st.info(f"📌 Transferí a **Tomas.130611** para confirmar.")
                        st.balloons()
                        st.session_state.numero_seleccionado = None
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al reservar: {str(e)}")

# ========== FUNCIÓN PARA GENERAR IMAGEN ==========
@st.cache_data(ttl=600)
def generar_imagen_rifa():
    """Genera imagen PNG con los números actualizados"""
    try:
        # Leer datos actualizados
        datos = sheet.get_all_values()
        df_img = pd.DataFrame(datos[1:], columns=datos[0])
        
        estados = {}
        for _, row in df_img.iterrows():
            estados[str(row['Número']).strip()] = row['Estado']
        
        # Configuración de la imagen
        ancho_celda = 55
        alto_celda = 55
        columnas = 10
        filas = 10
        
        ancho_total = ancho_celda * columnas + 40
        alto_total = alto_celda * filas + 80
        
        img = Image.new('RGB', (ancho_total, alto_total), color='#f8f9fa')
        draw = ImageDraw.Draw(img)
        
        try:
            fuente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            fuente = ImageFont.load_default()
        
        # Título
        draw.text((ancho_total//2 - 70, 10), "SUPER RIFA", fill='#1e3a5f', font=fuente)
        
        # Cuadrícula
        for fila in range(filas):
            for col in range(columnas):
                numero = f"{fila * columnas + col:02d}"
                estado = estados.get(numero, "Disponible")
                
                x0 = 20 + col * ancho_celda
                y0 = 50 + fila * alto_celda
                x1 = x0 + ancho_celda - 1
                y1 = y0 + alto_celda - 1
                
                if estado == "Disponible":
                    color = '#10b981'
                elif estado == "Reservado":
                    color = '#f59e0b'
                else:
                    color = '#ef4444'
                
                draw.rectangle([x0, y0, x1, y1], fill=color, outline='white')
                draw.text((x0 + 18, y0 + 18), numero, fill='white', font=fuente)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    except Exception as e:
        return None

# ========== MOSTRAR IMAGEN ACTUALIZADA ==========
st.markdown("---")
st.markdown("### 📸 Vista previa de la rifa (actualizada cada 10 minutos)")

imagen = generar_imagen_rifa()
if imagen:
    st.image(imagen, use_container_width=True)
    st.caption(f"🕐 Última actualización: {time.strftime('%H:%M:%S')}")
    
    # Botón para descargar la imagen
    st.download_button(
        label="📥 Descargar imagen actualizada",
        data=imagen,
        file_name="rifa_actualizada.png",
        mime="image/png"
    )
else:
    st.error("Error al generar la imagen")

# ========== FOOTER ==========
st.markdown('<div class="sorteo-texto">🎲 SORTEO POR QUINIELA NACIONAL MATUTINA - AL VENDERSE TODOS LOS NÚMEROS 🎲</div>', unsafe_allow_html=True)
st.markdown('<div class="pago-texto">💰 PAGOS POR TRANSFERENCIA AL ALIAS:<br><div class="alias-destacado">Tomas.130611</div></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ✂️ SUPER RIFA ✂️")
    st.markdown("---")
    st.markdown("""
    **🎯 ¿CÓMO PARTICIPAR?**
    
    1️⃣ Elegí un número **VERDE**
    2️⃣ Completá tus datos
    3️⃣ Transferí al alias: **Tomas.130611**
    4️⃣ ¡Listo! Ya tenés tu número
    
    ---
    
    **🎨 ESTADOS**
    
    🟢 Verde = Disponible  
    🟠 Naranja = Reservado  
    🔴 Rojo = Vendido
    
    ---
    
    **📅 SORTEO**
    
    🎲 Quiniela Nacional Matutina  
    ⏰ Cuando se vendan todos los números
    
    ---
    
    **💎 PROMO ESPECIAL**
    
    ¡Llevá 2 números por **$5.000**!
    
    ---
    
    **📞 CONTACTO**
    
    WhatsApp: 3826448225
    """)
