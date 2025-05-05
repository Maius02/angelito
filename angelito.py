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
    hoja = cliente.open_by_key(st.secrets["sheet_id"]).sheet1
    return hoja

sheet = conectar_sheets()

# --- UI ---

st.image("santuario.jpg", use_column_width=True)
st.title("🎁 Ruleta del Angelito")

clave = st.text_input("🔑 Ingresá tu clave secreta", type="password")

if st.button("🎡 Girar"):
    nombre = None
    for participante, c in claves.items():
        if clave == c:
            nombre = participante
            break

    if not nombre:
        st.error("❌ Clave incorrecta.")
    elif not ronda_habilitada:
        st.warning("⚠️ La ronda todavía no está habilitada.")
    else:
        posibles = [p for p in participantes if p != nombre]
        elegido = random.choice(posibles)

        with st.spinner("Girando la ruleta..."):
            time.sleep(2)

        st.success(f"🎉 {nombre}, tu angelito es: **{elegido}**")

        # Guardar en Google Sheets
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, nombre, elegido])

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
