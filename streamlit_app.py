import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# CSS para grid de números
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

/* GRID DE NÚMEROS */
.numeros-container {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;
    margin: 20px 0;
}

.numero-boton {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 5px;
    font-size: 14px;
    font-weight: bold;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
    font-family: monospace;
}

.numero-boton:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.numero-boton.disponible {
    background: #10b981;
    color: white;
    border-color: #10b981;
}

.numero-boton.reservado {
    background: #f59e0b;
    color: white;
    border-color: #f59e0b;
    cursor: not-allowed;
    opacity: 0.8;
}

.numero-boton.vendido {
    background: #ef4444;
    color: white;
    border-color: #ef4444;
    cursor: not-allowed;
    opacity: 0.8;
}

@media (max-width: 768px) {
    .numeros-container {
        gap: 4px;
    }
    .numero-boton {
        padding: 8px 2px;
        font-size: 11px;
    }
    .premio-card { padding: 8px 4px; font-size: 10px; }
    .premio-numero { width: 28px; height: 28px; font-size: 11px; }
}

@media (max-width: 480px) {
    .numero-boton {
        padding: 6px 1px;
        font-size: 9px;
    }
    .numeros-container {
        gap: 3px;
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
st.markdown("🟢 **Disponible** | 🟠 **Reservado** | 🔴 **Vendido**")

# ========== GENERAR GRID CON BOTONES FUNCIONALES ==========
# Crear un diccionario de estados
estados = {}
for _, row in df.iterrows():
    estados[str(row['Número']).strip()] = row['Estado']

# Inicializar número seleccionado
if 'numero_seleccionado' not in st.session_state:
    st.session_state.numero_seleccionado = None

# Usar st.markdown con HTML y botones que usan JavaScript para comunicarse
import streamlit.components.v1 as components

# Generar HTML con botones interactivos
html_botones = """
<script>
function seleccionarNumero(numero) {
    // Crear un evento personalizado para Streamlit
    const input = document.createElement('input');
    input.type = 'text';
    input.value = numero;
    input.id = 'selected_number';
    input.style.display = 'none';
    document.body.appendChild(input);
    
    // Disparar evento de cambio
    input.dispatchEvent(new Event('input', { bubbles: true }));
    
    // También intentar con el método de Streamlit
    if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: numero
        }, '*');
    }
}
</script>
<div class="numeros-container">
"""

for i in range(100):
    numero = f"{i:02d}"
    estado = estados.get(numero, "Disponible")
    
    if estado == "Disponible":
        clase = "disponible"
        emoji = "🟢"
        onclick = f"onclick=\"seleccionarNumero('{numero}')\""
    elif estado == "Reservado":
        clase = "reservado"
        emoji = "🟠"
        onclick = "disabled"
    else:
        clase = "vendido"
        emoji = "🔴"
        onclick = "disabled"
    
    if onclick != "disabled":
        html_botones += f'<button class="numero-boton {clase}" {onclick}>{emoji} {numero}</button>'
    else:
        html_botones += f'<button class="numero-boton {clase}" disabled>{emoji} {numero}</button>'

html_botones += '</div>'

# Agregar input oculto para capturar la selección
html_botones += """
<input type="text" id="numero_seleccionado" style="display:none">
<script>
// Escuchar cambios en el input oculto
const hiddenInput = document.getElementById('numero_seleccionado');
if (hiddenInput) {
    hiddenInput.addEventListener('input', function(e) {
        // Enviar a Streamlit
        const streamlitInput = document.createElement('input');
        streamlitInput.type = 'text';
        streamlitInput.value = e.target.value;
        streamlitInput.style.display = 'none';
        document.body.appendChild(streamlitInput);
        streamlitInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
}
</script>
"""

# Mostrar el grid
components.html(html_botones, height=650, scrolling=False)

# Input oculto para recibir el número desde JavaScript
numero_desde_js = st.text_input("", key="numero_js", label_visibility="collapsed", placeholder="")

if numero_desde_js:
    st.session_state.numero_seleccionado = numero_desde_js
    st.rerun()

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
