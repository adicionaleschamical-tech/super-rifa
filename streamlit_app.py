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
if 'premios_temp' not in st.session_state:
    st.session_state.premios_temp = None

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

# ========== FUNCIÓN DE LOGIN ==========
def verificar_usuario(username, password):
    if not client:
        return False, None
    
    try:
        sheet = client.open("Rifa").worksheet("Usuarios")
        datos = sheet.get_all_values()
        
        for fila in datos[1:]:
            if len(fila) >= 4 and fila[0] == username and fila[3] == "SI":
                if password == fila[1]:
                    return True, fila[2]
        return False, None
    except Exception as e:
        return False, None

# ========== FUNCIONES PARA CARGAR DATOS ==========
def cargar_config():
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
        "footer_texto": "¡Gracias por participar!",
        "cantidad_numeros": "100",
        "inicio_numeracion": "0",
        "mostrar_imagen_rifa": "SI",
        "mostrar_orientacion": "SI"
    }

def limpiar_titulo_premio(titulo, posicion):
    """Limpia el título del premio removiendo palabras como 'Lugar' y 'Premio'"""
    if not titulo:
        return ""
    
    # Remover "Lugar" y "Premio" del título si están presentes
    titulo_limpio = titulo
    # Remover patrones como "1° Lugar", "2° Lugar", etc.
    import re
    titulo_limpio = re.sub(r'\d+°\s*Lugar\s*', '', titulo_limpio)
    titulo_limpio = re.sub(r'Premio\s+\d+°\s*', '', titulo_limpio)
    titulo_limpio = re.sub(r'Lugar\s*', '', titulo_limpio)
    titulo_limpio = titulo_limpio.strip()
    
    # Si después de limpiar queda vacío, usar un título por defecto
    if not titulo_limpio:
        return f"Premio {posicion}°"
    
    return titulo_limpio

def cargar_premios():
    """Cargar premios desde Google Sheets"""
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Premios")
            datos = sheet.get_all_values()
            premios = []
            
            # Saltar encabezado
            for idx, fila in enumerate(datos[1:], start=1):
                if len(fila) >= 3:
                    titulo_original = fila[1] if len(fila) > 1 else ""
                    # Limpiar el título automáticamente
                    titulo_limpio = limpiar_titulo_premio(titulo_original, idx)
                    
                    premio = {
                        "icono": fila[0] if len(fila) > 0 else "🎁",
                        "titulo": titulo_limpio,
                        "descripcion": fila[2] if len(fila) > 2 else "",
                        "orden": idx,
                        "premio_extra": fila[4] if len(fila) > 4 else ""
                    }
                    premios.append(premio)
            
            # Si no hay premios, crear los 20 por defecto
            if not premios:
                premios = obtener_premios_default()
                
            return sorted(premios, key=lambda x: x['orden'])
        except Exception as e:
            st.warning(f"Error al cargar premios: {e}. Usando premios por defecto.")
            return obtener_premios_default()
    return obtener_premios_default()

def obtener_premios_default():
    premios = []
    for i in range(1, 21):
        premios.append({
            "icono": "🏆" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else "🎁")),
            "titulo": f"Premio {i}°",
            "descripcion": f"Descripción del {i}° premio",
            "orden": i,
            "premio_extra": ""
        })
    return premios

def cargar_numeros(cantidad_numeros=100, inicio=0):
    if client:
        try:
            sheet = client.open("Rifa").worksheet("Numeros")
            datos = sheet.get_all_values()
            
            if len(datos) > 1:
                df = pd.DataFrame(datos[1:], columns=datos[0])
                numeros_esperados = [f"{i:02d}" for i in range(inicio, inicio + cantidad_numeros)]
                numeros_existentes = df['Número'].tolist()
                
                for num in numeros_esperados:
                    if num not in numeros_existentes:
                        sheet.append_row([num, "Disponible", "", "", ""])
                
                datos = sheet.get_all_values()
                df = pd.DataFrame(datos[1:], columns=datos[0])
                return df
            else:
                sheet.clear()
                sheet.append_row(["Número", "Estado", "Nombre", "DNI", "Teléfono"])
                for i in range(inicio, inicio + cantidad_numeros):
                    numero = f"{i:02d}"
                    sheet.append_row([numero, "Disponible", "", "", ""])
                return pd.DataFrame({
                    "Número": [f"{i:02d}" for i in range(inicio, inicio + cantidad_numeros)],
                    "Estado": ["Disponible"] * cantidad_numeros,
                    "Nombre": [""] * cantidad_numeros,
                    "DNI": [""] * cantidad_numeros,
                    "Teléfono": [""] * cantidad_numeros
                })
        except Exception as e:
            st.error(f"Error cargando números: {e}")
            return pd.DataFrame(columns=["Número", "Estado", "Nombre", "DNI", "Teléfono"])
    return pd.DataFrame(columns=["Número", "Estado", "Nombre", "DNI", "Teléfono"])

def actualizar_estado(numero, estado, nombre="", dni="", telefono=""):
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
    if not client:
        return False
    
    try:
        sheet = client.open("Rifa").worksheet("Config")
        
        todas_filas = sheet.get_all_values()
        if len(todas_filas) == 0:
            sheet.append_row(["Campo", "Valor"])
        
        for clave, valor in config.items():
            try:
                celda = sheet.find(clave)
                if celda:
                    sheet.update_cell(celda.row, 2, str(valor))
                else:
                    sheet.append_row([clave, str(valor)])
            except:
                pass
        return True
    except:
        return False

def guardar_premios(premios):
    """Guardar premios con mejor manejo de errores"""
    if not client:
        st.error("No hay conexión con Google Sheets")
        return False
    
    try:
        sheet = client.open("Rifa").worksheet("Premios")
        
        # Limpiar la hoja completamente
        sheet.clear()
        
        # Agregar encabezados
        sheet.append_row(["Icono", "Título", "Descripción", "Orden", "Premio Extra"])
        
        # Agregar cada premio
        for premio in premios:
            sheet.append_row([
                premio.get('icono', '🎁'),
                premio.get('titulo', ''),
                premio.get('descripcion', ''),
                str(premio.get('orden', 99)),
                premio.get('premio_extra', '')
            ])
        
        return True
    except Exception as e:
        st.error(f"Error al guardar premios: {str(e)}")
        return False

def regenerar_numeros(cantidad, inicio):
    if not client:
        return False
    try:
        sheet = client.open("Rifa").worksheet("Numeros")
        sheet.clear()
        sheet.append_row(["Número", "Estado", "Nombre", "DNI", "Teléfono"])
        
        for i in range(inicio, inicio + cantidad):
            numero = f"{i:02d}"
            sheet.append_row([numero, "Disponible", "", "", ""])
        return True
    except:
        return False

def limpiar_todos_los_premios():
    """Función para limpiar todos los títulos de premios existentes"""
    if not client:
        return False
    
    try:
        premios_actuales = cargar_premios()
        
        # Limpiar todos los títulos
        for i, premio in enumerate(premios_actuales, start=1):
            premio['titulo'] = limpiar_titulo_premio(premio['titulo'], i)
            premio['orden'] = i
        
        # Guardar los premios limpios
        return guardar_premios(premios_actuales)
    except Exception as e:
        st.error(f"Error al limpiar premios: {e}")
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
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🚪 Cerrar sesión"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()
    
    st.markdown("---")
    
    # Botón para limpiar todos los premios (solo admin)
    if st.session_state.user_role == "admin":
        with st.expander("🧹 Herramientas de Limpieza", expanded=False):
            st.warning("⚠️ Esta herramienta eliminará la palabra 'Lugar' de todos los títulos de premios.")
            if st.button("🗑️ LIMPIAR TÍTULOS DE PREMIOS", use_container_width=True, type="secondary"):
                if limpiar_todos_los_premios():
                    st.success("✅ ¡Todos los títulos de premios han sido limpiados!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al limpiar los premios")
    
    # ========== CONFIGURACIÓN GENERAL ==========
    with st.expander("⚙️ Configuración General", expanded=True):
        with st.form("config_form"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_titulo = st.text_input("Título", value=config.get("titulo", "SUPER RIFA"))
                nuevo_subtitulo = st.text_input("Subtítulo", value=config.get("subtitulo", "PARA EQUIPAR MI BARBERÍA"))
                nuevo_color_principal = st.color_picker("Color principal", value=config.get("color_principal", "#1e3a5f"))
                nuevo_color_secundario = st.color_picker("Color secundario", value=config.get("color_secundario", "#c9a03d"))
                
            with col2:
                nuevo_precio = st.number_input("Precio por número ($)", value=int(config.get("precio_unidad", 3000)))
                nuevo_precio_promo = st.number_input("Precio promoción 2x ($)", value=int(config.get("precio_promo", 5000)))
                nuevo_alias = st.text_input("Alias de transferencia", value=config.get("alias", "Tomas.130611"))
                nuevo_telefono = st.text_input("WhatsApp", value=config.get("telefono", "3826448225"))
            
            nuevo_sorteo = st.text_input("Texto del sorteo", value=config.get("sorteo_texto", "Quiniela Nacional Matutina"))
            nueva_fecha = st.text_input("📅 Fecha del sorteo", value=config.get("fecha_sorteo", "Pendiente"))
            
            st.markdown("---")
            st.markdown("### 🔢 Personalización Avanzada")
            
            col3, col4 = st.columns(2)
            with col3:
                mostrar_imagen = st.selectbox("Mostrar imagen de la rifa", 
                                             options=["SI", "NO"],
                                             index=0 if config.get("mostrar_imagen_rifa", "SI") == "SI" else 1)
                mostrar_orientacion = st.selectbox("Mostrar orientación horizontal", 
                                                  options=["SI", "NO"],
                                                  index=0 if config.get("mostrar_orientacion", "SI") == "SI" else 1)
            
            with col4:
                nuevo_footer = st.text_input("Texto de pie de página", value=config.get("footer_texto", "¡Gracias por participar!"))
            
            if st.form_submit_button("💾 Guardar Configuración", use_container_width=True):
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
                    "footer_texto": nuevo_footer,
                    "mostrar_imagen_rifa": mostrar_imagen,
                    "mostrar_orientacion": mostrar_orientacion,
                    "cantidad_numeros": config.get("cantidad_numeros", "100"),
                    "inicio_numeracion": config.get("inicio_numeracion", "0")
                }
                if guardar_config(nueva_config):
                    st.success("✅ Configuración guardada")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar")
    
    # ========== CONFIGURACIÓN DE NÚMEROS ==========
    with st.expander("🔢 Configuración de Números", expanded=False):
        st.warning("⚠️ **ATENCIÓN:** Cambiar la cantidad de números reiniciará completamente la rifa. Todos los números volverán a estar disponibles.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cantidad_numeros = st.number_input("Cantidad de números", 
                                               min_value=10, 
                                               max_value=500, 
                                               value=int(config.get("cantidad_numeros", 100)),
                                               step=10)
        with col2:
            inicio_numeracion = st.number_input("Inicio de numeración", 
                                                min_value=0, 
                                                max_value=999, 
                                                value=int(config.get("inicio_numeracion", 0)),
                                                step=1)
        with col3:
            st.markdown("### ")
            if st.button("🔄 REGENERAR NÚMEROS", use_container_width=True, type="primary"):
                if regenerar_numeros(cantidad_numeros, inicio_numeracion):
                    config_actualizada = config.copy()
                    config_actualizada["cantidad_numeros"] = str(cantidad_numeros)
                    config_actualizada["inicio_numeracion"] = str(inicio_numeracion)
                    guardar_config(config_actualizada)
                    st.success(f"✅ {cantidad_numeros} números generados desde {inicio_numeracion:02d}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al regenerar números")
    
    # ========== PREMIOS (Hasta 20°) ==========
    with st.expander("🎁 Editar Premios (1° al 20° Lugar)", expanded=True):
        st.info("Configurá los premios para cada posición. Los primeros lugares se destacan visualmente.")
        
        # Usar session state para mantener los premios temporalmente
        if st.session_state.premios_temp is None:
            st.session_state.premios_temp = premios.copy()
        
        premios_actuales = st.session_state.premios_temp
        
        # Mostrar premios existentes
        for idx in range(len(premios_actuales)):
            p = premios_actuales[idx]
            with st.container():
                # Mostrar el número del lugar de forma clara
                st.markdown(f"**🎖️ {idx+1}° LUGAR**")
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
                with col1:
                    nuevo_icono = st.text_input("Icono", value=p['icono'], key=f"icono_{idx}", help="Ej: 🏆, 🎁, ✂️, etc.")
                with col2:
                    # Mostrar el título actual ya limpio
                    valor_titulo = p['titulo']
                    nuevo_titulo = st.text_input("Nombre del Premio", value=valor_titulo, key=f"titulo_{idx}", 
                                                placeholder="Ej: Jarra térmica, Corte de pelo, etc.")
                with col3:
                    nueva_desc = st.text_input("Descripción", value=p['descripcion'], key=f"desc_{idx}", 
                                              placeholder="Ej: 2 litros, Incluye bebida, etc.")
                with col4:
                    nuevo_extra = st.text_input("Premio Extra", value=p.get('premio_extra', ''), key=f"extra_{idx}", 
                                               placeholder="Ej: + $5000 adicional")
                with col5:
                    if idx >= 5:  # Permitir eliminar solo premios después del 5°
                        if st.button("🗑️ Eliminar", key=f"del_{idx}"):
                            st.session_state.premios_temp.pop(idx)
                            st.rerun()
                
                premios_actuales[idx] = {
                    "icono": nuevo_icono,
                    "titulo": nuevo_titulo,
                    "descripcion": nueva_desc,
                    "orden": idx + 1,
                    "premio_extra": nuevo_extra
                }
                st.markdown("---")
        
        # Botón para agregar nuevo premio
        if len(premios_actuales) < 20:
            col_add1, col_add2, col_add3 = st.columns([1, 2, 1])
            with col_add2:
                if st.button("➕ Agregar nuevo premio", use_container_width=True):
                    st.session_state.premios_temp.append({
                        "icono": "🎁",
                        "titulo": "",
                        "descripcion": "",
                        "orden": len(premios_actuales) + 1,
                        "premio_extra": ""
                    })
                    st.rerun()
        
        # Botón para guardar todos los premios
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            if st.button("💾 GUARDAR TODOS LOS PREMIOS", use_container_width=True, type="primary"):
                if guardar_premios(st.session_state.premios_temp):
                    st.success("✅ ¡Premios guardados exitosamente!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar los premios. Verifica la conexión con Google Sheets.")
    
    # ========== USUARIOS (SOLO ADMIN) ==========
    if st.session_state.user_role == "admin":
        with st.expander("👥 Gestión de Usuarios", expanded=False):
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

# ========== GENERAR CSS PERSONALIZADO ==========
def generar_css(config):
    color_principal = config.get("color_principal", "#1e3a5f")
    color_secundario = config.get("color_secundario", "#c9a03d")
    
    return f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%); }}
    .main-title {{ text-align: center; font-size: 2.2em; font-weight: 800; background: linear-gradient(135deg, {color_principal}, {color_principal}dd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-title {{ text-align: center; font-size: 1.2em; color: #4a5568; margin-top: -10px; }}
    .premio-card {{ background: white; border-radius: 20px; padding: 15px 10px; text-align: center; box-shadow: 0 5px 20px rgba(0,0,0,0.08); margin: 5px; transition: transform 0.2s; }}
    .premio-card:hover {{ transform: translateY(-5px); }}
    .premio-numero {{ background: {color_principal}; color: white; width: 35px; height: 35px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 10px; font-size: 14px; }}
    .premio-extra {{ background: {color_secundario}20; border-radius: 10px; padding: 3px 8px; font-size: 10px; margin-top: 5px; display: inline-block; }}
    .info-card {{ background: {color_principal}; border-radius: 20px; padding: 20px; color: white; text-align: center; margin: 15px 0; }}
    .precio-destacado {{ font-size: 1.8em; font-weight: bold; color: {color_secundario}; }}
    .promo-oferta {{ background: {color_secundario}; border-radius: 20px; padding: 15px; text-align: center; margin: 15px 0; animation: pulse 1.5s infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.02); }} 100% {{ transform: scale(1); }} }}
    .stButton button {{ background-color: #10b981 !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 12px 5px !important; font-size: 15px !important; font-weight: bold !important; width: 100% !important; cursor: pointer !important; }}
    .stButton button:hover {{ background-color: #059669 !important; }}
    .stButton button:disabled {{ background-color: #f59e0b !important; cursor: not-allowed !important; }}
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
def generar_imagen_rifa(cantidad_numeros=100, inicio=0):
    try:
        sheet = client.open("Rifa").worksheet("Numeros")
        datos = sheet.get_all_values()
        df_img = pd.DataFrame(datos[1:], columns=datos[0])
        
        estados = {}
        for _, row in df_img.iterrows():
            estados[str(row['Número']).strip()] = row['Estado']
        
        columnas = 10
        filas = (cantidad_numeros + columnas - 1) // columnas
        
        ancho_celda = 55
        alto_celda = 55
        
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
                numero_idx = fila * columnas + col
                if numero_idx < cantidad_numeros:
                    numero = f"{inicio + numero_idx:02d}"
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
    st.markdown(generar_css(config), unsafe_allow_html=True)
    
    st.markdown(f'<div class="main-title">✂️ {config.get("titulo", "SUPER RIFA")} ✂️</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{config.get("subtitulo", "PARA EQUIPAR MI BARBERÍA")}</div>', unsafe_allow_html=True)
    
    # Mostrar premios destacados (primeros 5)
    if premios:
        st.markdown("### 🏆 PREMIOS DESTACADOS")
        cols = st.columns(min(len(premios), 5))
        for i in range(min(5, len(premios))):
            premio = premios[i]
            with cols[i]:
                # Mostrar solo el título del premio, ya está limpio
                titulo_mostrar = premio["titulo"] if premio["titulo"] else f"Premio {i+1}°"
                premio_extra_html = f'<div class="premio-extra">{premio.get("premio_extra", "")}</div>' if premio.get("premio_extra") else ""
                st.markdown(f'<div class="premio-card"><div class="premio-numero">{i+1}°</div><b>{titulo_mostrar}</b><br><small>{premio["descripcion"]}</small>{premio_extra_html}</div>', unsafe_allow_html=True)
        
        # Mostrar premios adicionales en expander
        if len(premios) > 5:
            with st.expander("🎁 Ver todos los premios (1° al 20°)"):
                for i in range(5, len(premios)):
                    premio = premios[i]
                    titulo_mostrar = premio["titulo"] if premio["titulo"] else f"Premio {i+1}°"
                    premio_extra_html = f' <span class="premio-extra">{premio.get("premio_extra", "")}</span>' if premio.get("premio_extra") else ""
                    st.markdown(f"**{i+1}° Lugar:** {premio['icono']} **{titulo_mostrar}** - {premio['descripcion']}{premio_extra_html}")
    
    # Configuración de números
    cantidad_numeros = int(config.get("cantidad_numeros", 100))
    inicio_numeracion = int(config.get("inicio_numeracion", 0))
    fin_numeracion = inicio_numeracion + cantidad_numeros - 1
    
    precio_unidad = int(config.get("precio_unidad", 3000))
    precio_promo = int(config.get("precio_promo", 5000))
    cantidad_promo = int(config.get("cantidad_promo", 2))
    
    st.markdown(f'<div class="info-card"><h3>🎲 NÚMEROS DEL {inicio_numeracion:02d} AL {fin_numeracion:02d}</h3><div class="precio-destacado">${precio_unidad:,} CADA NÚMERO</div><div>Total de números: {cantidad_numeros}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="promo-oferta"><p>🎁 ¡PROMOCIÓN ESPECIAL! 🎁</p><span>{cantidad_promo} NÚMEROS POR ${precio_promo:,}</span></div>', unsafe_allow_html=True)
    
    fecha_sorteo = config.get("fecha_sorteo", "Pendiente")
    if fecha_sorteo and fecha_sorteo != "Pendiente":
        st.markdown(f'<div class="fecha-box"><strong>📅 Fecha del sorteo:</strong> {fecha_sorteo}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fecha-box"><strong>📅 Sorteo:</strong> Se realizará cuando se completen todos los números</div>', unsafe_allow_html=True)
    
    if config.get("mostrar_orientacion", "SI") == "SI":
        st.markdown("""
        <div class="orientacion-box">
            📱 <strong>¿Usás el celular?</strong><br>
            🔄 <strong>GIRÁ LA PANTALLA A HORIZONTAL (landscape)</strong> para ver los números en grilla
        </div>
        """, unsafe_allow_html=True)
    
    df = cargar_numeros(cantidad_numeros, inicio_numeracion)
    
    st.markdown("### 🎲 ¡ELEGÍ TUS NÚMEROS!")
    st.markdown("🟢 **Verde = Disponible** | 🟠 **Reservado** | 🔴 **Vendido**")
    
    if not df.empty:
        estados = {}
        for _, row in df.iterrows():
            estados[str(row['Número']).strip()] = row['Estado']
        
        columnas_grilla = 10
        filas_grilla = (cantidad_numeros + columnas_grilla - 1) // columnas_grilla
        
        for fila in range(filas_grilla):
            cols = st.columns(columnas_grilla)
            for col in range(columnas_grilla):
                numero_idx = fila * columnas_grilla + col
                if numero_idx < cantidad_numeros:
                    numero = f"{inicio_numeracion + numero_idx:02d}"
                    estado = estados.get(numero, "Disponible")
                    
                    with cols[col]:
                        if estado == "Disponible":
                            if st.button(f"🟢 {numero}", key=f"btn_{numero}", use_container_width=True):
                                st.session_state.numero_seleccionado = numero
                                st.rerun()
                        elif estado == "Reservado":
                            st.button(f"🟠 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)
                        else:
                            st.button(f"🔴 {numero}", key=f"btn_{numero}", disabled=True, use_container_width=True)
    
    if 'numero_seleccionado' in st.session_state and st.session_state.numero_seleccionado:
        numero_sel = st.session_state.numero_seleccionado
        
        df_actual = cargar_numeros(cantidad_numeros, inicio_numeracion)
        estado_actual = "Disponible"
        for idx, row in df_actual.iterrows():
            if str(row['Número']).strip() == numero_sel:
                estado_actual = row['Estado']
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
    
    fecha_sorteo = config.get("fecha_sorteo", "Pendiente")
    if fecha_sorteo and fecha_sorteo != "Pendiente":
        st.markdown(f'<div class="sorteo-texto">🎲 SORTEO POR {config.get("sorteo_texto", "QUINIELA NACIONAL MATUTINA")} - {fecha_sorteo} 🎲</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sorteo-texto">🎲 SORTEO POR {config.get("sorteo_texto", "QUINIELA NACIONAL MATUTINA")} - AL VENDERSE TODOS LOS NÚMEROS 🎲</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="pago-texto">💰 PAGOS POR TRANSFERENCIA AL ALIAS:<br><div class="alias-destacado">{config.get("alias", "Tomas.130611")}</div></div>', unsafe_allow_html=True)
    
    if config.get("mostrar_imagen_rifa", "SI") == "SI":
        st.markdown("---")
        st.markdown("### 📸 Vista previa de la rifa")
        imagen = generar_imagen_rifa(cantidad_numeros, inicio_numeracion)
        if imagen:
            st.image(imagen, use_container_width=True)
            st.caption("🕐 Imagen actualizada cada 10 minutos")
            st.download_button(
                label="📥 Descargar imagen",
                data=imagen,
                file_name="rifa_actualizada.png",
                mime="image/png"
            )
    
    st.markdown(f'<div style="text-align:center; color:#666; margin-top:30px;">{config.get("footer_texto", "¡Gracias por participar!")}</div>', unsafe_allow_html=True)

# ========== SIDEBAR ==========
def mostrar_sidebar(config):
    precio_unidad = int(config.get("precio_unidad", 3000))
    precio_promo = int(config.get("precio_promo", 5000))
    cantidad_numeros = int(config.get("cantidad_numeros", 100))
    
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
        
        **📊 ESTADÍSTICAS**
        
        • Total números: {cantidad_numeros}
        
        ---
        
        **📅 SORTEO**
        
        🎲 {config.get('sorteo_texto', 'Quiniela Nacional Matutina')}
        
        ---
        
        **📞 CONTACTO**
        
        WhatsApp: {config.get('telefono', '3826448225')}
        """)

# ========== MAIN ==========
def main():
    config = cargar_config()
    mostrar_sidebar(config)
    
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
