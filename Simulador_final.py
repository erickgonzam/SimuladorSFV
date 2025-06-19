import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# Configuración inicial del dashboard
st.set_page_config(page_title="🔋 Simulador SFV Aislado", layout="wide")
st.title("🔋 Simulador Avanzado de Sistema Fotovoltaico Aislado")

# --- Estilos personalizados ---
st.markdown("""
    <style>
        .main {background-color: #111827; color: #F3F4F6;}
        h1, h2, h3 {color: #38BDF8;}
        .stTable tbody tr td {background-color: #1F2937 !important; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- Cuadro de Cargas ---
st.header("1. Cuadro de Cargas")
data = {
    "Aparato": ["Refrigerador", "Foco LED", "Televisor"],
    "Voltaje (V)": [120, 120, 120],
    "Corriente (A)": [1.25, 0.08, 0.83],
    "Potencia (W)": [None, None, None],
    "Horas uso (h/día)": [24, 5, 4]
}
df = pd.DataFrame(data)

# Editor interactivo
df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# Cálculo inteligente de potencia

def calcular_potencia(row):
    if pd.notna(row["Potencia (W)"]):
        return row["Potencia (W)"]
    elif pd.notna(row["Voltaje (V)"]) and pd.notna(row["Corriente (A)"]):
        return row["Voltaje (V)"] * row["Corriente (A)"]
    else:
        return None

df_editado["Potencia (W)"] = df_editado.apply(calcular_potencia, axis=1)
df_editado["Energía diaria (Wh)"] = pd.to_numeric(df_editado["Potencia (W)"], errors="coerce") * pd.to_numeric(df_editado["Horas uso (h/día)"], errors="coerce")
energia_total = df_editado["Energía diaria (Wh)"].sum()
st.success(f"Demanda energética total: {energia_total:.2f} Wh/día")

# --- Parámetros del sistema ---
st.header("2. Parámetros del Sistema")
col1, col2 = st.columns(2)
with col1:
    hsp = st.number_input("Horas Sol Pico (HSP)", 1.0, 8.0, 5.0, 0.1)
    perdidas = st.slider("Pérdidas del sistema (%)", 0, 30, 15)
    dias_autonomia = st.slider("Días de autonomía", 1, 7, 2)
with col2:
    voltaje_sistema = st.selectbox("Voltaje del sistema (V)", [12, 24, 48])
    profundidad_descarga = st.slider("Profundidad de descarga de batería (%)", 10, 100, 50)

energia_ajustada = energia_total / (1 - perdidas / 100)
potencia_fv = energia_ajustada / hsp

# --- Paneles Solares ---
st.header("3. Selección de Paneles Solares")
paneles = {
    "JA Solar JAM60S21 390W": 390,
    "Canadian Solar CS3L-375MS": 375,
    "Trina Solar TSM-370DE08M.08(II)": 370,
    "LONGi LR4-60HPH-365M": 365
}
modelo_panel = st.selectbox("Modelo de panel solar", list(paneles.keys()))
potencia_panel = paneles[modelo_panel]
num_paneles = math.ceil(potencia_fv / potencia_panel)

# --- Baterías ---
st.header("4. Selección de Baterías")
baterias = {
    "Trojan T-105 (6V, 225Ah)": (6, 225),
    "Rolls S6 L16-HC (6V, 445Ah)": (6, 445),
    "Victron AGM 12V/220Ah": (12, 220),
    "Discover 12V/100Ah": (12, 100)
}
modelo_bateria = st.selectbox("Modelo de batería", list(baterias.keys()))
voltaje_bateria, capacidad_ah_bateria = baterias[modelo_bateria]
energia_por_bateria = voltaje_bateria * capacidad_ah_bateria

capacidad_total_wh = energia_total * dias_autonomia / (profundidad_descarga / 100)
num_baterias = math.ceil(capacidad_total_wh / energia_por_bateria)
baterias_serie = math.ceil(voltaje_sistema / voltaje_bateria)

if voltaje_sistema % voltaje_bateria != 0:
    st.error("⚠️ El voltaje del sistema no es múltiplo del voltaje de la batería seleccionada.")
    baterias_totales = "Error"
else:
    baterias_totales = baterias_serie * math.ceil(num_baterias / baterias_serie)

# --- Controlador ---
st.header("5. Controlador de Carga")
corriente_panel = potencia_panel / voltaje_sistema
corriente_total = corriente_panel * num_paneles
corriente_controlador = math.ceil(corriente_total * 1.25)
st.info(f"🔌 Controlador sugerido: {corriente_controlador} A mínimo, tipo MPPT de {voltaje_sistema} V")

# --- Inversor ---
st.header("6. Inversor Recomendado")
potencia_pico = df_editado["Potencia (W)"].max() * 1.2
st.info(f"🔄 Inversor sugerido: mínimo {math.ceil(potencia_fv)} W continuo, con picos de {math.ceil(potencia_pico)} W")

# --- Resultados ---
st.header("7. Resultados Generales")
resultados = {
    "Demanda Total (Wh/día)": f"{energia_total:.2f}",
    "Energía Ajustada (Wh/día)": f"{energia_ajustada:.2f}",
    "Potencia SFV Requerida (W)": f"{potencia_fv:.2f}",
    "Modelo de Panel": modelo_panel,
    "Núm. de Paneles": num_paneles,
    "Modelo de Batería": modelo_bateria,
    "Total Baterías (solo en serie)": baterias_totales,
    "Controlador de Carga (A)": corriente_controlador,
    "Inversor (W)": f"{math.ceil(potencia_fv)} W / Pico {math.ceil(potencia_pico)} W"
}
st.table(pd.DataFrame(resultados.items(), columns=["Elemento", "Valor"]))

# --- Visualizaciones ---
st.header("8. Visualizaciones")
if "Energía diaria (Wh)" in df_editado.columns:
    fig1, ax1 = plt.subplots()
    ax1.pie(df_editado["Energía diaria (Wh)"], labels=df_editado["Aparato"], autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.subheader("🔌 Distribución de Energía por Aparato")
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    ax2.bar(["Demanda Original", "Energía Ajustada"], [energia_total, energia_ajustada], color=["#60A5FA", "#FCD34D"])
    ax2.set_ylabel("Energía (Wh/día)")
    ax2.set_title("Comparativa: Real vs Ajustada")
    st.pyplot(fig2)
else:
    st.warning("⚠️ No hay datos de energía para mostrar gráficas.")
