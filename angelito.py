import streamlit as st
import random
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="🌸 Angelito Secreto", layout="centered")

# Paleta de colores aesthetic
COLORES = ["#FEC8D8", "#FCD5CE", "#D8E2DC", "#A9DEF9", "#E4C1F9", "#CDEAC0"]

# Google Sheets setup
@st.cache_resource
def conectar_google_sheets():
    creds_json = st.secrets["google"]["credentials"]
    sheet_id = st.secrets["google"]["sheet_id"]
    credentials_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(credentials_dict)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

sheet = conectar_google_sheets()

# Funciones
@st.cache_data(ttl=60)
def obtener_historial():
    return sheet.get_all_records()

def guardar_asignacion(usuario, asignado):
    sheet.append_row([usuario, asignado])

def obtener_asignacion(usuario):
    historial = obtener_historial()
    for entrada in historial:
        if entrada['usuario'] == usuario:
            return entrada['asignado']
    return None

def participantes_disponibles(usuario):
    historial = obtener_historial()
    ya_asignados = [h['asignado'] for h in historial]
    ya_jugaron = [h['usuario'] for h in historial]
    restantes = [n for n in nombres if n != usuario and n not in ya_asignados and n not in ya_jugaron]
    if not restantes:
        restantes = [n for n in nombres if n != usuario and n not in ya_asignados]
    return restantes

# Lista de participantes (podés mantenerla también en Sheets si querés)
nombres = ["Caro", "Luli", "Meli", "Sofi", "Flor", "Vicky", "Gime"]

# UI
st.markdown("""
    <h1 style='text-align: center; color: #D88C9A;'>🌸 Angelito Secreto 🌸</h1>
    <p style='text-align: center;'>Elegí tu nombre, ingresá tu contraseña secreta y descubrí tu persona asignada.</p>
""", unsafe_allow_html=True)

usuario = st.selectbox("¿Quién sos?", nombres)
clave = st.text_input("Contraseña secreta", type="password")
boton = st.button("Girar la ruleta 🎡")

if usuario and clave:
    asignado_previo = obtener_asignacion(usuario)
    if asignado_previo:
        st.success(f"Ya te tocó: **{asignado_previo}** ✨\n\n¡Prepará tus sorpresas angelicales!")
    elif boton:
        posibles = participantes_disponibles(usuario)
        if not posibles:
            st.warning("Ya no quedan personas disponibles. ¡Todas fueron asignadas!")
        else:
            asignado = random.choice(posibles)
            guardar_asignacion(usuario, asignado)
            st.balloons()
            st.success(f"Te tocó: **{asignado}** 🎁\n\n¡Guardá bien el secreto y sé un angelito atento! 💖")
else:
    st.info("Ingresá tu nombre y contraseña para comenzar.")
