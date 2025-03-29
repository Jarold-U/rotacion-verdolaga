
import streamlit as st
import pandas as pd
import io
import random

# Seguridad básica
PASSWORD = "Verd0laga2025!"

st.set_page_config(page_title="Sistema de Rotación Verdolaga", layout="centered")
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://atlnacional.com.co/wp-content/uploads/2021/05/Solo-escudo.png' width='150'>
        <h1 style='color:#008D52;'>Sistema de Rotación Verdolaga</h1>
    </div>
""", unsafe_allow_html=True)

# Autenticación
password = st.text_input("Ingresa la contraseña para continuar", type="password")
if password != PASSWORD:
    st.warning("Acceso restringido. Ingresa la clave correcta.")
    st.stop()

st.success("Acceso concedido. Bienvenido al sistema verdolaga 💚")

# Carga de archivos
st.header("1. Carga los archivos de los partidos")
archivo_actual = st.file_uploader("📥 Archivo del partido actual", type=["csv", "xlsx"], key="actual")
archivo_anterior = st.file_uploader("📥 Archivo del partido anterior", type=["csv", "xlsx"], key="anterior")

if archivo_actual and archivo_anterior:
    def cargar_archivo(f):
        if f.name.endswith(".csv"):
            return pd.read_csv(f, delimiter=';', encoding='utf-8')
        else:
            return pd.read_excel(f)

    df_actual = cargar_archivo(archivo_actual)
    df_anterior = cargar_archivo(archivo_anterior)

    st.subheader("2. Selecciona cuántas personas quieres por tribuna")
    tribunas = df_actual['TRIBUNA'].dropna().unique()
    tribuna_config = {}

    for tribuna in tribunas:
        cantidad = st.number_input(f"Cantidad para tribuna {tribuna}", min_value=0, step=1)
        tribuna_config[tribuna] = cantidad

    if st.button("🎲 Generar Rotación"):
        df_actual['CLASIFICACION'] = 'ROTAR'
        df_actual.loc[df_actual['ACOMODACION'].str.upper().str.contains('COORDINADOR', na=False), 'CLASIFICACION'] = 'FIJO'
        df_actual.loc[df_actual['UBICACIÓN'].str.upper().str.contains('PALCO', na=False), 'CLASIFICACION'] = 'FIJO'
        df_actual.loc[df_actual['ACOMODACION'].str.upper().str.contains('PUERTA', na=False), 'CLASIFICACION'] = 'PUERTA'

        personas_previas = df_anterior[['DOCUMENTO', 'TRIBUNA']].rename(columns={'TRIBUNA': 'TRIBUNA_ANTERIOR'})
        df_merge = df_actual.merge(personas_previas, on='DOCUMENTO', how='left')

        df_resultado = df_merge.copy()
        disponibles = df_resultado[df_resultado['CLASIFICACION'] == 'ROTAR'].copy()
        asignaciones = []

        for tribuna, cantidad in tribuna_config.items():
            candidatos = disponibles[disponibles['TRIBUNA_ANTERIOR'] != tribuna]
            seleccionados = candidatos.sample(n=min(cantidad, len(candidatos)), replace=False)
            disponibles = disponibles.drop(seleccionados.index)
            seleccionados['TRIBUNA'] = tribuna
            asignaciones.append(seleccionados)

        df_final = pd.concat([
            df_resultado[df_resultado['CLASIFICACION'] == 'FIJO'],
            df_resultado[df_resultado['CLASIFICACION'] == 'PUERTA'],
            *asignaciones
        ])

        df_final = df_final.drop(columns=['TRIBUNA_ANTERIOR', 'CLASIFICACION'])
        st.success("✅ Rotación generada con éxito")
        st.dataframe(df_final)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Rotacion')
        st.download_button("📥 Descargar archivo rotado", data=output.getvalue(), file_name="rotacion_verdolaga.xlsx")
