import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# CSS con ancho optimizado para 5 columnas
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

/* BOTONES CON ANCHO OPTIMIZADO PARA 5 COLUMNAS */
.stButton button {
    background-color: #10b981 !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 5px !important;
    font-size: 14px !important;
    font-weight: bold !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
    width: 100% !important;
}

.stButton button:hover {
    background-color: #059669 !important;
    transform: translateY(-2px);
}

.stButton button:disabled {
    background-color: #f59e0b !important;
    color: white !important;
    cursor: not-allowed !important;
    transform: none !important;
}

button[kind="secondary"][disabled] {
    background-color: #ef4444 !important;
}

/* FORZAR QUE LAS COLUMNAS TENGAN EL MISMO ANCHO */
[data-testid="column"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
}

/* FORZAR QUE LAS FILAS NO APILEN Y PERMITAN SCROLL */
.row-widget.stHorizontal {
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    gap: 8px !important;
    padding-bottom: 10px !important;
    margin-bottom: 10px !important;
}

/* EN MÓVIL, AJUSTAR GAP Y TAMAÑO DE FUENTE */
@media (max-width: 768px) {
    .row-widget.stHorizontal {
        gap: 5px !important;
    }
    .stButton button {
        padding: 8px 2px !important;
        font-size: 12px !important;
    }
    .premio-card { padding: 8px 4px; font-size: 10px; }
    .premio-numero { width: 28px; height: 28px; font-size: 11px; }
}

@media (max-width: 480px) {
    .row-widget.stHorizontal {
        gap: 3px !important;
    }
    .stButton button {
        padding: 6px 1px !important;
        font-size: 10px !important;
    }
}

/* Ocultar scrollbar en móvil (opcional, se ve mejor) */
@media (max-width: 768px) {
    .row-widget.stHorizontal::-webkit-scrollbar {
        height: 3px;
    }
    .row-widget.stHorizontal::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    .row-widget.stHorizontal::-webkit-scrollbar-thumb {
        background: #c9a03d;
        border-radius: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✂️ SUPER RIFA! ✂️</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">PARA EQUIPAR MI BARBERÍA</div>', unsafe_allow_html=True)

# Premios
col1, col2, col3, col4, col5 = st.columns(5)
premios_texto = ["JARRA TÉRMICA<br>2 litros", "ROPA INTERIOR<br>Conjunto femenino", "TIENDA GABRIELA<br>Premio sorpresa", "BARBERÍA CANICHE<br>Corte de pelo", "PASTAFROLA<br>Una pastafrola"]
for i, col in enumerate([col1, col2, col3, col4, col5]):
    with col:
        st.markdown(f'<div class="premio-card"><div class="premio-numero">{i+1}°</div>{premios_texto[i]}</div>', unsafe_allow_html=True)

st.markdown('<div class="info-card"><h3>🎲 NÚMEROS DEL 00 AL 99</h3><div class="precio-destacado">$3.000 CADA NÚMERO</div></div>', unsafe_allow_html=True)
st.markdown('<div class="promo-oferta"><p>🎁 ¡PROMOCIÓN ESPECIAL! 🎁</p><span>2 NÚMEROS POR $5.000</span></div>', unsafe_allow_html=True)

# Conectar con Google Sheets
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

# ========== 5 COLUMNAS x 20 FILAS ==========
# 5 columnas es el número perfecto para móvil vertical
for fila in range(20):  # 20 filas
    columnas = st.columns(5)  # 5 columnas por fila
    for col_idx in range(5):
        numero_num = fila * 5 + col_idx
        if numero_num <= 99:
            numero = f"{numero_num:02d}"
            
            # Buscar estado
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
    
    # Verificar que siga disponible
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

# Footer
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
