import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# CSS con Grid forzado para móvil
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
.stButton button { border-radius: 12px; background: white; border: 1px solid #e2e8f0; color: #1e3a5f; padding: 8px 4px; font-size: 12px; width: 100%; text-align: center; }
.stButton button:hover { background: #1e3a5f; color: white; }
.sorteo-texto { text-align: center; margin-top: 20px; padding: 12px; background: #1e3a5f; border-radius: 15px; color: white; font-size: 14px; }
.pago-texto { text-align: center; margin-top: 15px; padding: 15px; background: #1e3a5f; border-radius: 15px; color: white; }
.alias-destacado { font-size: 1.3em; font-weight: bold; color: #c9a03d; background: rgba(255,255,255,0.1); display: inline-block; padding: 6px 16px; border-radius: 30px; }

/* ESTILO PARA FORZAR 10 COLUMNAS EN MÓVIL */
@media (max-width: 768px) {
    .stButton button { 
        font-size: 10px; 
        padding: 6px 2px;
        min-width: 32px;
    }
    /* Forzar que los contenedores de columnas sean flexibles pero mantengan 10 por fila */
    .row-widget.stHorizontal {
        flex-wrap: wrap !important;
        display: flex !important;
        gap: 4px;
    }
    .row-widget.stHorizontal > div {
        flex: 0 0 calc(10% - 4px) !important;
        max-width: calc(10% - 4px) !important;
        min-width: calc(10% - 4px) !important;
        margin: 2px 0 !important;
    }
    .premio-card { padding: 8px 4px; font-size: 10px; }
    .premio-numero { width: 25px; height: 25px; font-size: 10px; }
    .main-title { font-size: 1.5em; }
    .info-card h3 { font-size: 1em; }
    .precio-destacado { font-size: 1.3em; }
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
    st.success("✅ Conectado a Google Sheets")
except Exception as e:
    st.error(f"❌ Error de conexión: {str(e)}")
    st.stop()

# Leer datos
datos = sheet.get_all_values()
df = pd.DataFrame(datos[1:], columns=datos[0])

st.markdown("### 🎲 ¡ELEGÍ TUS NÚMEROS!")
st.markdown("🟢 **Disponible** | 🟠 **Reservado** | 🔴 **Vendido**")

# ========== UNA SOLA CUADRÍCULA DE NÚMEROS ==========
# Usar st.columns con CSS que fuerza 10 columnas en móvil
for fila in range(10):
    cols = st.columns(10)
    for col_idx in range(10):
        numero_num = fila * 10 + col_idx
        numero = f"{numero_num:02d}"
        
        # Buscar estado del número
        estado = "Disponible"
        if len(df[df['Número'] == numero]) > 0:
            estado = df[df['Número'] == numero]['Estado'].values[0]
        
        with cols[col_idx]:
            if estado == "Disponible":
                if st.button(f"🟢 {numero}", key=f"num_{numero}", use_container_width=True):
                    st.session_state.numero_seleccionado = numero
                    st.rerun()
            elif estado == "Reservado":
                st.button(f"🟠 {numero}", key=f"num_{numero}", disabled=True, use_container_width=True)
            else:
                st.button(f"🔴 {numero}", key=f"num_{numero}", disabled=True, use_container_width=True)

# Formulario de reserva
if 'numero_seleccionado' in st.session_state and st.session_state.numero_seleccionado:
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
