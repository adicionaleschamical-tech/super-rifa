import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="SUPER RIFA", page_icon="✂️", layout="wide")

# ========== INICIALIZAR SESSION STATE ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# ========== CONEXIÓN GOOGLE SHEETS ==========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def conectar_google_sheets():
    try:
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
        return None

client = conectar_google_sheets()

# ========== FUNCIÓN DE LOGIN (CONTRASEÑA EN TEXTO PLANO) ==========
def verificar_usuario(username, password):
    """Verificar usuario en Google Sheets (contraseña en texto plano)"""
    if not client:
        return False, None
    
    try:
        sheet = client.open("Rifa").worksheet("Usuarios")
        datos = sheet.get_all_values()
        
        for fila in datos[1:]:
            if len(fila) >= 4 and fila[0] == username and fila[3] == "SI":
                # Comparar contraseña en texto plano
                if password == fila[1]:
                    return True, fila[2]  # fila[2] es el rol
        return False, None
    except Exception as e:
        st.error(f"Error en login: {e}")
        return False, None

# ========== FUNCIONES PARA CARGAR DATOS ==========
def cargar_config():
    """Cargar configuración desde Google Sheets"""
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Config")
            datos = sheet.get_all_values()
            config = {}
            for fila in datos[1:]:
                if len(fila) >= 2:
                    config[fila[0]] = fila[1]
            return config
        except:
            return obtener_config_default()
    return obtener_config_default()

def obtener_config_default():
    return {
        "titulo": "SUPER RIFA",
        "subtitulo": "PARA EQUIPAR MI BARBERÍA",
        "color_principal": "#1e3a5f",
        "color_secundario": "#c9a03d",
        "precio_unidad": "3000",
        "precio_promo": "5000",
        "cantidad_promo": "2",
        "alias": "Tomas.130611",
        "telefono": "3826448225",
        "sorteo_texto": "Quiniela Nacional Matutina",
        "fecha_sorteo": "Pendiente",
        "footer_texto": "¡Gracias por participar!"
    }

def cargar_premios():
    """Cargar premios desde Google Sheets"""
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Premios")
            datos = sheet.get_all_values()
            premios = []
            for fila in datos[1:]:
                if len(fila) >= 4:
                    premios.append({
                        "icono": fila[0],
                        "titulo": fila[1],
                        "descripcion": fila[2],
                        "orden": int(fila[3]) if fila[3] and fila[3].isdigit() else 99
                    })
            return sorted(premios, key=lambda x: x['orden'])
        except:
            return obtener_premios_default()
    return obtener_premios_default()

def obtener_premios_default():
    return [
        {"icono": "🏆", "titulo": "Jarra térmica", "descripcion": "2 litros", "orden": 1},
        {"icono": "👙", "titulo": "Ropa interior", "descripcion": "Conjunto femenino", "orden": 2},
        {"icono": "🎁", "titulo": "Tienda Gabriela", "descripcion": "Premio sorpresa", "orden": 3},
        {"icono": "✂️", "titulo": "Barbería Caniche", "descripcion": "Corte de pelo", "orden": 4},
        {"icono": "🍰", "titulo": "Pastafrola", "descripcion": "Casera", "orden": 5}
    ]

def cargar_numeros():
    """Cargar números desde Google Sheets"""
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Numeros")
            datos = sheet.get_all_values()
            if len(datos) > 1:
                return pd.DataFrame(datos[1:], columns=datos[0])
        except:
            pass
    return pd.DataFrame(columns=["Número", "Estado", "Nombre", "DNI", "Teléfono"])

def actualizar_estado(numero, estado, nombre="", dni="", telefono=""):
    """Actualizar estado de un número"""
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Numeros")
            celda = sheet.find(numero)
            if celda:
                sheet.update_cell(celda.row, 2, estado)
                sheet.update_cell(celda.row, 3, nombre)
                sheet.update_cell(celda.row, 4, dni)
                sheet.update_cell(celda.row, 5, telefono)
                return True
        except:
            pass
    return False

def guardar_config(config):
    """Guardar configuración con diagnóstico"""
    if not client or st.session_state.user_role != "admin":
        st.error("❌ No tienes permisos o no hay conexión")
        return False
    
    try:
        sheet = client.open("Rifa").worksheet("Config")
        
        # Obtener todas las filas actuales
        todas_filas = sheet.get_all_values()
        
        # Si no hay datos, crear encabezados
        if len(todas_filas) == 0:
            sheet.append_row(["Campo", "Valor"])
        
        # Actualizar cada campo
        for clave, valor in config.items():
            try:
                # Buscar si la clave ya existe
                celda = sheet.find(clave)
                if celda:
                    # Actualizar valor existente
                    sheet.update_cell(celda.row, 2, str(valor))
                else:
                    # Agregar nueva fila
                    sheet.append_row([clave, str(valor)])
            except Exception as e:
                st.warning(f"Error con {clave}: {e}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al guardar: {str(e)}")
        return False

def guardar_premios(premios):
    """Guardar premios (solo admin)"""
    if not client or st.session_state.user_role != "admin":
        return False
    try:
        sheet = client.open("Rifa").worksheet("Premios")
        todas_filas = sheet.get_all_values()
        if len(todas_filas) > 1:
            for i in range(len(todas_filas), 1, -1):
                sheet.delete_rows(i)
        
        for i, p in enumerate(premios, start=2):
            sheet.update_cell(i, 1, p['icono'])
            sheet.update_cell(i, 2, p['titulo'])
            sheet.update_cell(i, 3, p['descripcion'])
            sheet.update_cell(i, 4, p['orden'])
        return True
    except Exception as e:
        st.error(f"Error al guardar premios: {e}")
        return False

# ========== MOSTRAR LOGIN ==========
def mostrar_login():
    st.markdown("### 🔐 Acceso al Panel de Administración")
    st.markdown("Ingresá tus credenciales para personalizar la rifa")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)
        
        if submitted:
            if username and password:
                valido, rol = verificar_usuario(username, password)
                if valido:
                    st.session_state.logged_in = True
                    st.session_state.user_role = rol
                    st.session_state.username = username
                    st.success(f"✅ Bienvenido {username}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.error("❌ Complete todos los campos")

# ========== PANEL DE ADMINISTRACIÓN ==========
def mostrar_admin_panel(config, premios):
    st.markdown(f"### 🔧 Panel de Administración")
    st.markdown(f"👤 **Usuario:** {st.session_state.username} | **Rol:** {st.session_state.user_role}")
    
    if st.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.user_role == "admin":
        tab1, tab2, tab3 = st.tabs(["⚙️ Configuración", "🎁 Premios", "👥 Usuarios"])
        
        with tab1:
            st.markdown("### Configuración General")
            with st.form("config_form"):
                nuevo_titulo = st.text_input("Título", value=config.get("titulo", "SUPER RIFA"))
                nuevo_subtitulo = st.text_input("Subtítulo", value=config.get("subtitulo", "PARA EQUIPAR MI BARBERÍA"))
                nuevo_color_principal = st.color_picker("Color principal", value=config.get("color_principal", "#1e3a5f"))
                nuevo_color_secundario = st.color_picker("Color secundario", value=config.get("color_secundario", "#c9a03d"))
                nuevo_precio = st.number_input("Precio por número ($)", value=int(config.get("precio_unidad", 3000)))
                nuevo_precio_promo = st.number_input("Precio promoción 2x ($)", value=int(config.get("precio_promo", 5000)))
                nuevo_alias = st.text_input("Alias de transferencia", value=config.get("alias", "Tomas.130611"))
                nuevo_telefono = st.text_input("WhatsApp", value=config.get("telefono", "3826448225"))
                nuevo_sorteo = st.text_input("Texto del sorteo", value=config.get("sorteo_texto", "Quiniela Nacional Matutina"))
                nueva_fecha = st.text_input("📅 Fecha del sorteo", value=config.get("fecha_sorteo", "Pendiente"))
                
                if st.form_submit_button("💾 Guardar Configuración"):
                    nueva_config = {
                        "titulo": nuevo_titulo,
                        "subtitulo": nuevo_subtitulo,
                        "color_principal": nuevo_color_principal,
                        "color_secundario": nuevo_color_secundario,
                        "precio_unidad": str(nuevo_precio),
                        "precio_promo": str(nuevo_precio_promo),
                        "cantidad_promo": "2",
                        "alias": nuevo_alias,
                        "telefono": nuevo_telefono,
                        "sorteo_texto": nuevo_sorteo,
                        "fecha_sorteo": nueva_fecha,
                        "footer_texto": config.get("footer_texto", "¡Gracias por participar!")
                    }
                    if guardar_config(nueva_config):
                        st.success("✅ Configuración guardada")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar")
        
        with tab2:
            st.markdown("### Editar Premios")
            premios_editables = []
            for i, p in enumerate(premios):
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
                    with col1:
                        icono = st.text_input(f"Icono {i+1}", value=p['icono'], key=f"icono_{i}")
                    with col2:
                        titulo = st.text_input(f"Título {i+1}", value=p['titulo'], key=f"titulo_{i}")
                    with col3:
                        desc = st.text_input(f"Descripción {i+1}", value=p['descripcion'], key=f"desc_{i}")
                    with col4:
                        orden = st.number_input(f"Orden {i+1}", value=p['orden'], key=f"orden_{i}", min_value=1, max_value=10)
                    premios_editables.append({"icono": icono, "titulo": titulo, "descripcion": desc, "orden": orden})
            
            if st.button("💾 Guardar Premios"):
                if guardar_premios(premios_editables):
                    st.success("✅ Premios guardados")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar")
        
        with tab3:
            st.markdown("### Gestión de Usuarios")
            st.info("📌 Para agregar o modificar usuarios, editá directamente el Google Sheet en la pestaña 'Usuarios'")
            st.markdown("""
            **Estructura de la pestaña Usuarios:**
            - Columna A: Usuario
            - Columna B: Contraseña (texto plano)
            - Columna C: Rol (admin / editor)
            - Columna D: Activo (SI / NO)
            
            **Ejemplo:**
            | administrador | 124578 | admin | SI |
            | editor | 123456 | editor | SI |
            """)
    
    else:
        # Editor: solo puede personalizar visual
        st.markdown("### 🎨 Personalización Visual")
        st.info("Como Editor, podés modificar colores, textos, precios y fecha del sorteo")
        
        with st.form("editor_form"):
            nuevo_titulo = st.text_input("Título", value=config.get("titulo", "SUPER RIFA"))
            nuevo_subtitulo = st.text_input("Subtítulo", value=config.get("subtitulo", "PARA EQUIPAR MI BARBERÍA"))
            nuevo_color_principal = st.color_picker("Color principal", value=config.get("color_principal", "#1e3a5f"))
            nuevo_color_secundario = st.color_picker("Color secundario", value=config.get("color_secundario", "#c9a03d"))
            nuevo_precio = st.number_input("Precio por número ($)", value=int(config.get("precio_unidad", 3000)))
            nuevo_precio_promo = st.number_input("Precio promoción 2x ($)", value=int(config.get("precio_promo", 5000)))
            nuevo_alias = st.text_input("Alias de transferencia", value=config.get("alias", "Tomas.130611"))
            nuevo_telefono = st.text_input("WhatsApp", value=config.get("telefono", "3826448225"))
            nuevo_sorteo = st.text_input("Texto del sorteo", value=config.get("sorteo_texto", "Quiniela Nacional Matutina"))
            nueva_fecha = st.text_input("📅 Fecha del sorteo", value=config.get("fecha_sorteo", "Pendiente"))
            
            if st.form_submit_button("💾 Guardar Cambios"):
                nueva_config = {
                    "titulo": nuevo_titulo,
                    "subtitulo": nuevo_subtitulo,
                    "color_principal": nuevo_color_principal,
                    "color_secundario": nuevo_color_secundario,
                    "precio_unidad": str(nuevo_precio),
                    "precio_promo": str(nuevo_precio_promo),
                    "cantidad_promo": "2",
                    "alias": nuevo_alias,
                    "telefono": nuevo_telefono,
                    "sorteo_texto": nuevo_sorteo,
                    "fecha_sorteo": nueva_fecha,
                    "footer_texto": config.get("footer_texto", "¡Gracias por participar!")
                }
                if guardar_config(nueva_config):
                    st.success("✅ Cambios guardados")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar")

# ========== GENERAR CSS PERSONALIZADO ==========
def generar_css(config):
    color_principal = config.get("color_principal", "#1e3a5f")
    color_secundario = config.get("color_secundario", "#c9a03d")
    
    return f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%); }}
    .main-title {{ text-align: center; font-size: 2.2em; font-weight: 800; background: linear-gradient(135deg, {color_principal}, {color_principal}dd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-title {{ text-align: center; font-size: 1.2em; color: #4a5568; margin-top: -10px; }}
    .premio-card {{ background: white; border-radius: 20px; padding: 15px 10px; text-align: center; box-shadow: 0 5px 20px rgba(0,0,0,0.08); margin: 5px; }}
    .premio-numero {{ background: {color_principal}; color: white; width: 35px; height: 35px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 10px; font-size: 14px; }}
    .info-card {{ background: {color_principal}; border-radius: 20px; padding: 20px; color: white; text-align: center; margin: 15px 0; }}
    .precio-destacado {{ font-size: 1.8em; font-weight: bold; color: {color_secundario}; }}
    .promo-oferta {{ background: {color_secundario}; border-radius: 20px; padding: 15px; text-align: center; margin: 15px 0; animation: pulse 1.5s infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} 100% {{ transform: scale(1); }} }}
    .stButton button {{ background-color: #10b981 !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 12px 5px !important; font-size: 15px !important; font-weight: bold !important; width: 100% !important; cursor: pointer !important; }}
    .stButton button:hover {{ background-color: #059669 !important; }}
    .stButton button:disabled {{ background-color: #f59e0b !important; cursor: not-allowed !important; }}
    button[kind="secondary"][disabled] {{ background-color: #ef4444 !important; }}
    .sorteo-texto {{ text-align: center; margin-top: 20px; padding: 12px; background: {color_principal}; border-radius: 15px; color: white; font-size: 14px; }}
    .pago-texto {{ text-align: center; margin-top: 15px; padding: 15px; background: {color_principal}; border-radius: 15px; color: white; }}
    .alias-destacado {{ font-size: 1.3em; font-weight: bold; color: {color_secundario}; background: rgba(255,255,255,0.1); display: inline-block; padding: 6px 16px; border-radius: 30px; }}
    .orientacion-box {{ background: #fef3c7; border-left: 5px solid {color_secundario}; padding: 15px; margin: 20px 0; border-radius: 12px; text-align: center; }}
    .fecha-box {{ background: #f0f2f5; border-radius: 15px; padding: 12px; text-align: center; margin: 15px 0; }}
    @media (max-width: 768px) {{ .stButton button {{ padding: 10px 3px !important; font-size: 13px !important; }} .premio-card {{ padding: 10px 4px; font-size: 11px; }} .premio-numero {{ width: 30px; height: 30px; font-size: 12px; }} }}
    </style>
    """

# ========== FUNCIÓN PARA GENERAR IMAGEN ==========
@st.cache_data(ttl=600)
def generar_imagen_rifa():
    try:
        sheet = client.open("Rifa").worksheet("Numeros")
        datos = sheet.get_all_values()
        df_img = pd.DataFrame(datos[1:], columns=datos[0])
        
        estados = {}
        for _, row in df_img.iterrows():
            estados[str(row['Número']).strip()] = row['Estado']
        
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
        
        draw.text((ancho_total//2 - 70, 10), "SUPER RIFA", fill='#1e3a5f', font=fuente)
        
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
    except:
        return None

# ========== VISTA PÚBLICA DE LA RIFA ==========
def mostrar_rifa_publica(config, premios):
    # CSS personalizado
    st.markdown(generar_css(config), unsafe_allow_html=True)
    
    # Título
    st.markdown(f'<div class="main-title">✂️ {config.get("titulo", "SUPER RIFA")} ✂️</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{config.get("subtitulo", "PARA EQUIPAR MI BARBERÍA")}</div>', unsafe_allow_html=True)
    
    # Premios
    if premios:
        cols = st.columns(min(len(premios), 5))
        for i, premio in enumerate(premios[:5]):
            with cols[i % 5]:
                st.markdown(f'<div class="premio-card"><div class="premio-numero">{i+1}°</div><b>{premio["titulo"]}</b><br><small>{premio["descripcion"]}</small></div>', unsafe_allow_html=True)
    
    # Precios
    precio_unidad = int(config.get("precio_unidad", 3000))
    precio_promo = int(config.get("precio_promo", 5000))
    cantidad_promo = int(config.get("cantidad_promo", 2))
    
    st.markdown(f'<div class="info-card"><h3>🎲 NÚMEROS DEL 00 AL 99</h3><div class="precio-destacado">${precio_unidad:,} CADA NÚMERO</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="promo-oferta"><p>🎁 ¡PROMOCIÓN ESPECIAL! 🎁</p><span>{cantidad_promo} NÚMEROS POR ${precio_promo:,}</span></div>', unsafe_allow_html=True)
    
    # Fecha del sorteo
    fecha_sorteo = config.get("fecha_sorteo", "Pendiente")
    if fecha_sorteo and fecha_sorteo != "Pendiente":
        st.markdown(f'<div class="fecha-box"><strong>📅 Fecha del sorteo:</strong> {fecha_sorteo}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fecha-box"><strong>📅 Sorteo:</strong> Se realizará cuando se completen todos los números</div>', unsafe_allow_html=True)
    
    # Mensaje orientación
    st.markdown("""
    <div class="orientacion-box">
        📱 <strong>¿Usás el celular?</strong><br>
        🔄 <strong>GIRÁ LA PANTALLA A HORIZONTAL (landscape)</strong> para ver los números en grilla
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar números
    df = cargar_numeros()
    
    st.markdown("### 🎲 ¡ELEGÍ TUS NÚMEROS!")
    st.markdown("🟢 **Verde = Disponible** | 🟠 **Reservado** | 🔴 **Vendido**")
    
    # Botones de números
    if not df.empty:
        estados = {}
        for _, row in df.iterrows():
            estados[str(row['Número']).strip()] = row['Estado']
        
        for fila in range(20):
            columnas = st.columns(5)
            for col_idx in range(5):
                numero_num = fila * 5 + col_idx
                if numero_num <= 99:
                    numero = f"{numero_num:02d}"
                    estado = estados.get(numero, "Disponible")
                    
                    with columnas[col_idx]:
                        if estado == "Disponible":
                            if st.button(f"🟢 {numero}", key=f"btn_{numero}", use_container_width=True):
                                st.session_state.numero_seleccionado = numero
                                st.rerun()
                        elif estado == "Reservado":
                            st.button(f"🟠 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)
                        else:
                            st.button(f"🔴 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)
    
    # Formulario de reserva
    if 'numero_seleccionado' in st.session_state and st.session_state.numero_seleccionado:
        numero_sel = st.session_state.numero_seleccionado
        
        # Verificar disponibilidad
        df_actual = cargar_numeros()
        estado_actual = "Disponible"
        fila_numero = None
        for idx, row in df_actual.iterrows():
            if str(row['Número']).strip() == numero_sel:
                estado_actual = row['Estado']
                fila_numero = idx + 2
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
                st.markdown(f'<div style="background:#f7f9fc;padding:15px;border-radius:15px;border-left:4px solid {config.get("color_secundario", "#c9a03d")}"><strong>💰 PAGO:</strong> Transferencia al alias <strong style="color:{config.get("color_secundario", "#c9a03d")}">{config.get("alias", "Tomas.130611")}</strong></div>', unsafe_allow_html=True)
                
                if st.form_submit_button("✅ RESERVAR", use_container_width=True):
                    if not telefono:
                        st.error("❌ El teléfono es obligatorio")
                    else:
                        if actualizar_estado(numero_sel, "Reservado", nombre, dni, telefono):
                            st.success(f"✅ ¡Número {numero_sel} reservado con éxito!")
                            st.info(f"📌 Transferí a **{config.get('alias', 'Tomas.130611')}** para confirmar.")
                            st.balloons()
                            st.session_state.numero_seleccionado = None
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Error al reservar")
    
    # Footer con fecha condicional
    fecha_sorteo = config.get("fecha_sorteo", "Pendiente")
    if fecha_sorteo and fecha_sorteo != "Pendiente":
        st.markdown(f'<div class="sorteo-texto">🎲 SORTEO POR {config.get("sorteo_texto", "QUINIELA NACIONAL MATUTINA")} - {fecha_sorteo} 🎲</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sorteo-texto">🎲 SORTEO POR {config.get("sorteo_texto", "QUINIELA NACIONAL MATUTINA")} - AL VENDERSE TODOS LOS NÚMEROS 🎲</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="pago-texto">💰 PAGOS POR TRANSFERENCIA AL ALIAS:<br><div class="alias-destacado">{config.get("alias", "Tomas.130611")}</div></div>', unsafe_allow_html=True)
    
    # Imagen actualizada
    st.markdown("---")
    st.markdown("### 📸 Vista previa de la rifa")
    imagen = generar_imagen_rifa()
    if imagen:
        st.image(imagen, use_container_width=True)
        st.caption("🕐 Imagen actualizada cada 10 minutos")
        st.download_button(
            label="📥 Descargar imagen",
            data=imagen,
            file_name="rifa_actualizada.png",
            mime="image/png"
        )

# ========== SIDEBAR ==========
def mostrar_sidebar(config):
    precio_unidad = int(config.get("precio_unidad", 3000))
    precio_promo = int(config.get("precio_promo", 5000))
    
    with st.sidebar:
        st.markdown(f"### ✂️ {config.get('titulo', 'SUPER RIFA')}")
        st.markdown("---")
        st.markdown(f"""
        **🎯 ¿CÓMO PARTICIPAR?**
        
        1️⃣ Elegí un número **VERDE**
        2️⃣ Completá tus datos
        3️⃣ Transferí a: **{config.get('alias', 'Tomas.130611')}**
        4️⃣ ¡Listo! Ya tenés tu número
        
        ---
        
        **🎨 ESTADOS**
        
        🟢 Verde = Disponible  
        🟠 Naranja = Reservado  
        🔴 Rojo = Vendido
        
        ---
        
        **💰 PRECIOS**
        
        • 1 número: ${precio_unidad:,}
        • 2 números: ${precio_promo:,}
        
        ---
        
        **📅 SORTEO**
        
        🎲 {config.get('sorteo_texto', 'Quiniela Nacional Matutina')}
        
        ---
        
        **📞 CONTACTO**
        
        WhatsApp: {config.get('telefono', '3826448225')}
        """)

# ========== MAIN ==========
def main():
    # Cargar configuración
    config = cargar_config()
    
    # Mostrar sidebar siempre
    mostrar_sidebar(config)
    
    # Verificar si está logueado
    if st.session_state.logged_in:
        premios = cargar_premios()
        mostrar_admin_panel(config, premios)
    else:
        premios = cargar_premios()
        mostrar_rifa_publica(config, premios)
        
        with st.expander("🔐 Acceso Administrativo"):
            mostrar_login()

if __name__ == "__main__":
    main()
