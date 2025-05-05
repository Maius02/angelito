import streamlit as st
import json
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
from datetime import datetime

# --- CONFIGURACIÓN ---

# Cargar configuración local
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

participantes = list(config["participantes"].keys())
claves = config["participantes"]
admin_password = config["admin_password"]
ronda_habilitada = config["ronda_habilitada"]

# --- CONEXIÓN GOOGLE SHEETS ---

@st.cache_resource
def conectar_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    cliente = gspread.authorize(creds)
    hoja = cliente.open_by_key(st.secrets["sheet"]["id"]).sheet1
    return hoja

sheet = conectar_sheets()

# --- FUNCIONES AUXILIARES ---

# Función para obtener el historial de un usuario desde Google Sheets
def obtener_historial(usuario):
    historial = sheet.get_all_records()
    historial_usuario = [entry for entry in historial if entry["Usuario"] == usuario]
    return historial_usuario

# Función para bloquear la elección de un usuario
def bloquear_usuario(usuario):
    # Esto marca al usuario como bloqueado en la hoja de Google Sheets
    hoja = sheet
    usuario_actual = hoja.find(usuario)
    if usuario_actual:
        hoja.update_cell(usuario_actual.row, 2, "Bloqueado")  # Marcar como bloqueado

# --- UI ---

st.image("santuario.jpg", use_column_width=True)
st.title("🎁 Ruleta del Angelito")

clave = st.text_input("🔑 Ingresá tu clave secreta", type="password")

if clave not in claves.values():
    st.error("❌ Clave incorrecta.")
else:
    nombre = [k for k, v in claves.items() if v == clave][0]
    historial_usuario = obtener_historial(nombre)

    # Verificar si el usuario ya ha elegido
    if not historial_usuario:
        st.warning(f"⚠️ {nombre}, aún no has girado la ruleta.")
    elif ronda_habilitada and not any(entry['Elegido'] == '' for entry in historial_usuario):
        st.success(f"🎉 {nombre}, ya has girado la ruleta y te ha tocado: {historial_usuario[-1]['Elegido']}")
    else:
        if st.button("🎡 Girar la ruleta"):
            posibles = [p for p in participantes if p != nombre and p not in [entry['Elegido'] for entry in historial_usuario]]
            
            if len(posibles) == 0:
                st.warning("⚠️ Ya te tocó a todos los demás.")
            else:
                elegido = random.choice(posibles)
                with st.spinner("Girando la ruleta..."):
                    time.sleep(2)

                st.success(f"🎉 {nombre}, tu angelito es: **{elegido}**")
                # Guardar en Google Sheets el nombre elegido
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hoja.append_row([timestamp, nombre, elegido])
                bloquear_usuario(nombre)

# --- ADMIN ---

with st.expander("🔐 Panel de administración"):
    admin = st.text_input("Contraseña admin", type="password")
    if admin == admin_password:
        st.markdown("## Panel de control")
        if st.button("✅ Habilitar ronda"):
            config["ronda_habilitada"] = True
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.success("Ronda habilitada")
        if st.button("🛑 Deshabilitar ronda"):
            config["ronda_habilitada"] = False
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.warning("Ronda deshabilitada")
