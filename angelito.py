import streamlit as st
import json
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- CONFIGURACION ---

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

participantes = list(config["participantes"].keys())
claves = config["participantes"]
admin_password = config["admin_password"]
ronda_habilitada = config["ronda_habilitada"]

# --- CONEXION GOOGLE SHEETS ---
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

# --- UTILIDADES ---
def obtener_datos():
    valores = sheet.get_all_values()
    df = pd.DataFrame(valores[1:], columns=valores[0])
    return df

def guardar_asignacion(usuario, elegido, ronda):
    df = obtener_datos()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Revisar si el usuario ya tiene una fila
    if usuario in df['Usuario'].values:
        fila_idx = df[df['Usuario'] == usuario].index[0] + 2  # +2 por encabezado + base 1
        sheet.update_cell(fila_idx, 1, timestamp)
        sheet.update_cell(fila_idx, ronda + 2, elegido)  # Timestamp y Usuario ocupan las 2 primeras
    else:
        nueva_fila = [timestamp, usuario] + [""] * (ronda - 1) + [elegido]
        sheet.append_row(nueva_fila)

# --- DETERMINAR RONDA ACTUAL ---
valores = sheet.get_all_values()
columnas = valores[0] if valores else []
ronda_actual = sum([1 for c in columnas if c.startswith("Ronda")])
if ronda_habilitada:
    ronda_actual += 1

# --- UI ---
st.title("🎁 Ruleta del Angelito")

clave = st.text_input("🔑 Ingresá tu clave secreta", type="password")

if clave:
    nombre = next((n for n, c in claves.items() if c == clave), None)
    if not nombre:
        st.error("❌ Clave incorrecta.")
    else:
        df = obtener_datos()
        jugo_en_ronda = False
        if ronda_actual > 0:
            col_ronda = f"Ronda {ronda_actual}"
            if col_ronda in df.columns:
                jugo_en_ronda = nombre in df[df[col_ronda] != ""]["Usuario"].values

        if jugo_en_ronda:
            ultimo = df.loc[df["Usuario"] == nombre, col_ronda].values[0]
            st.info(f"👼 Ya giraste esta ronda. Tu angelito es: **{ultimo}**")
        elif not ronda_habilitada:
            st.warning("⚠️ La ronda todavía no está habilitada.")
        else:
            # Obtener historial del usuario
            historial = df[df['Usuario'] == nombre].filter(like='Ronda').values.tolist()
            ya_tocados = [e for sublist in historial for e in sublist if e and e != nombre]
            posibles = [p for p in participantes if p != nombre and p not in ya_tocados]

            if not posibles:
                st.success("🎉 ¡Ya fuiste angelito de todas!")
            else:
                if st.button("🎡 Girar ruleta"):
                    elegido = random.choice(posibles)
                    with st.spinner("Girando la ruleta..."):
                        time.sleep(2)
                    st.success(f"🎉 {nombre}, tu angelito es: **{elegido}**")
                    guardar_asignacion(nombre, elegido, ronda_actual)

# --- PANEL ADMIN ---
with st.expander("🔐 Panel de administración"):
    admin = st.text_input("Contraseña admin", type="password")
    if admin == admin_password:
        st.markdown("## Panel de control")
        if st.button("✅ Habilitar nueva ronda"):
            config["ronda_habilitada"] = True
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            nueva_columna = f"Ronda {ronda_actual + 1}"
            sheet.add_cols(1)
            sheet.update_cell(1, ronda_actual + 3, nueva_columna)
            st.success(f"Ronda {ronda_actual + 1} habilitada")

        if st.button("🛑 Deshabilitar ronda"):
            config["ronda_habilitada"] = False
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.warning("Ronda deshabilitada")
