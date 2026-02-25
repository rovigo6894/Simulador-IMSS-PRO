import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="IMSS Ley 73 - PRO", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ocultar menús de Streamlit
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Título
st.title("💰 SIMULADOR DE PENSIÓN IMSS")
st.markdown("**LEY 73 - Art. 167**")
st.caption("Modelo basado en cálculo oficial con Modalidad 40")
st.divider()

# ============================================
# FUNCIONES DE CÁLCULO
# ============================================

def calcular_pension(semanas, salario, edad_actual, edad_retiro, esposa=True):
    FACTOR_POR_EDAD = {60:0.75, 61:0.80, 62:0.85, 63:0.90, 64:0.95, 65:1.00}
    FACTOR_EDAD = FACTOR_POR_EDAD.get(edad_retiro, 0.75)
    
    PCT_CUANTIA = 0.13
    PCT_INCREMENTO = 0.0245
    PCT_ESPOSA = 0.15 if esposa else 0
    DECRETO_FOX = 0.11
    
    años_para_retiro = max(0, edad_retiro - edad_actual)
    semanas_60 = semanas + (52 * años_para_retiro)
    
    cuantia_basica_diaria = salario * PCT_CUANTIA
    cuantia_basica_anual = cuantia_basica_diaria * 365
    
    incremento_diario = salario * PCT_INCREMENTO
    años_despues_500 = max(0, (semanas_60 - 500) / 52)
    incrementos_anuales = incremento_diario * 365 * años_despues_500
    
    cuantia_total_anual = cuantia_basica_anual + incrementos_anuales
    asignacion_anual = cuantia_total_anual * PCT_ESPOSA
    total_con_asignacion = cuantia_total_anual + asignacion_anual
    decreto_fox = total_con_asignacion * DECRETO_FOX
    cuantia_base_total = total_con_asignacion + decreto_fox
    
    pension_anual = cuantia_base_total * FACTOR_EDAD
    pension_mensual = pension_anual / 12
    
    return {
        'mensual': round(pension_mensual, 2),
        'anual': round(pension_anual, 2),
        'semanas_60': round(semanas_60, 0),
        'factor_edad': FACTOR_EDAD
    }

def calcular_mod40(semanas, salario, edad_actual, edad_retiro, salario_m40, meses_m40, esposa=True):
    años_para_retiro = max(0, edad_retiro - edad_actual)
    
    factores = {1: 0.13347, 2: 0.14438, 3: 0.15529, 4: 0.1662}
    
    meses_por_año = 30.4
    inversion = 0
    meses_restantes = meses_m40
    
    for año in range(1, 5):
        if meses_restantes <= 0:
            break
        meses_en_año = min(12, meses_restantes)
        inversion += salario_m40 * meses_en_año * meses_por_año * factores.get(año, 0.13347)
        meses_restantes -= meses_en_año
    
    semanas_m40 = (meses_m40 / 12) * 52
    semanas_totales = semanas + (52 * años_para_retiro) + semanas_m40
    
    if meses_m40 >= 6:
        semanas_ponderadas = min(semanas_m40, 250)
        semanas_previas = 250 - semanas_ponderadas
        nuevo_promedio = ((salario * semanas_previas) + (salario_m40 * semanas_ponderadas)) / 250 if semanas_previas > 0 else salario_m40
    else:
        nuevo_promedio = salario
    
    FACTOR_POR_EDAD = {60:0.75, 61:0.80, 62:0.85, 63:0.90, 64:0.95, 65:1.00}
    FACTOR_EDAD = FACTOR_POR_EDAD.get(edad_retiro, 0.75)
    
    PCT_CUANTIA = 0.13
    PCT_INCREMENTO = 0.0245
    PCT_ESPOSA = 0.15 if esposa else 0
    DECRETO_FOX = 0.11
    AJUSTE_FINAL = 1.2166
    
    años_despues_500 = max(0, (semanas_totales - 500) / 52)
    
    pension_anual = (
        ((nuevo_promedio * PCT_CUANTIA * 365) +
         (nuevo_promedio * PCT_INCREMENTO * 365 * años_despues_500)) *
        (1 + PCT_ESPOSA) * (1 + DECRETO_FOX) * FACTOR_EDAD * AJUSTE_FINAL
    )
    
    pension_mensual = pension_anual / 12
    base = calcular_pension(semanas, salario, edad_actual, edad_retiro, esposa)
    incremento = pension_mensual - base['mensual']
    
    return {
        'base': base['mensual'],
        'con_m40': round(pension_mensual, 2),
        'incremento': round(incremento, 2),
        'inversion': round(inversion, 2),
        'recuperacion_meses': round(inversion / max(1, incremento), 1),
        'utilidad_20': round((incremento * 12 * 20) - inversion, 2),
        'roi': round(((incremento * 12 * 20) / inversion) * 100, 0) if inversion > 0 else 0,
        'nuevo_promedio': round(nuevo_promedio, 2)
    }

# ============================================
# PESTAÑAS
# ============================================

tab1, tab2, tab3 = st.tabs(["📋 Calculadora Base", "📈 Modalidad 40", "📊 Comparativa"])

# ========== PESTAÑA 1: CALCULADORA BASE ==========
with tab1:
    st.subheader("Datos personales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        edad_actual = st.number_input("Edad actual", min_value=40, max_value=65, value=55, step=1, key="edad1")
        semanas_hoy = st.number_input("Semanas cotizadas a la fecha", min_value=0, max_value=3000, value=1315, step=1, key="sem1")
        salario_promedio = st.number_input("Salario promedio últimos 5 años ($)", min_value=0.0, max_value=10000.0, value=965.25, step=10.0, key="sal1")
    
    with col2:
        edad_retiro = st.selectbox("Edad de retiro", [60, 61, 62, 63, 64, 65], index=0, key="retiro1")
        asignacion_esposa = st.checkbox("¿Con asignación por esposa?", value=True, key="esposa1")
        inflacion = st.slider("Inflación estimada anual (%)", 0.0, 10.0, 4.0, key="inf1") / 100
    
    if st.button("Calcular pensión base", type="primary", use_container_width=True, key="btn1"):
        with st.spinner("Calculando..."):
            base = calcular_pension(semanas_hoy, salario_promedio, edad_actual, edad_retiro, asignacion_esposa)
            
            st.divider()
            col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
            with col_r2:
                st.markdown(f"""
                <div style='background-color: #0066b3; padding: 20px; border-radius: 10px; text-align: center; color: white'>
                    <h2 style='color: white; margin:0'>PENSIÓN MENSUAL</h2>
                    <h1 style='color: white; font-size: 48px; margin:10px'>${base['mensual']:,.2f}</h1>
                    <p style='color: #e0e0e0; margin:0'>Ley 73 - Retiro a los {edad_retiro} años</p>
                    <p style='color: #e0e0e0; margin:0; font-size: 12px;'>Semanas totales: {base['semanas_60']:.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("🔍 Ver desglose del cálculo"):
                st.write(f"**Factor por edad:** {base['factor_edad']*100:.0f}%")
                st.write(f"**Semanas a los {edad_retiro} años:** {base['semanas_60']:.0f}")
            
            años_para_retiro = max(0, edad_retiro - edad_actual)
            if años_para_retiro > 0 and inflacion > 0:
                factor_inflacion = (1 + inflacion) ** años_para_retiro
                pension_inflacion = base['mensual'] * factor_inflacion
                st.info(f"📈 Con inflación del {inflacion*100:.1f}% anual: ${pension_inflacion:,.2f} mensuales (pesos de hoy)")

# ========== PESTAÑA 2: MODALIDAD 40 ==========
with tab2:
    st.subheader("Análisis de Modalidad 40")
    
    col1, col2 = st.columns(2)
    
    with col1:
        edad_m40 = st.number_input("Edad actual", min_value=40, max_value=65, value=55, step=1, key="edad2")
        semanas_m40 = st.number_input("Semanas cotizadas", min_value=0, max_value=3000, value=1315, step=1, key="sem2")
        salario_actual = st.number_input("Salario promedio ($)", min_value=0.0, max_value=10000.0, value=965.25, step=10.0, key="sal2")
    
    with col2:
        edad_retiro2 = st.selectbox("Edad de retiro", [60,61,62,63,64,65], index=0, key="retiro2")
        esposa2 = st.checkbox("¿Con asignación por esposa?", value=True, key="esposa2")
        salario_m40 = st.number_input("Salario a cotizar en M40 ($)", min_value=0.0, max_value=20000.0, value=2932.0, step=100.0, key="sal_m40")
        meses_m40 = st.selectbox("Meses en M40", [6,12,18,24,30,36,42,48], index=3, key="meses")
    
    if st.button("Calcular Modalidad 40", type="primary", use_container_width=True, key="btn2"):
        with st.spinner("Analizando..."):
            res = calcular_mod40(semanas_m40, salario_actual, edad_m40, edad_retiro2, salario_m40, meses_m40, esposa2)
            
            st.divider()
            
            st.markdown(f"""
            <div style='background-color: #00a86b; padding: 15px; border-radius: 10px; text-align: center; color: white; margin: 15px 0;'>
                <h2 style='color: white; margin:0'>💰 INCREMENTO MENSUAL: ${res['incremento']:,.2f}</h2>
                <p style='color: #e0e0e0;'>Tu pensión aumentaría con Modalidad 40</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown(f"""
                <div style='background-color: white; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #0066b3;'>
                    <h3 style='color: #0066b3; margin:0'>PENSIÓN BASE</h3>
                    <h2 style='color: #0066b3; margin:10px'>${res['base']:,.2f}</h2>
                    <p style='color: #666; margin:0'>Sin Modalidad 40</p>
                </div>
                """, unsafe_allow_html=True)
            with col_c2:
                st.markdown(f"""
                <div style='background-color: #0066b3; padding: 15px; border-radius: 10px; text-align: center; color: white'>
                    <h3 style='color: white; margin:0'>CON MOD. 40</h3>
                    <h2 style='color: white; margin:10px'>${res['con_m40']:,.2f}</h2>
                    <p style='color: #e0e0e0; margin:0'>{meses_m40} meses</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Inversión total", f"${res['inversion']:,.0f}")
            with col_m2:
                st.metric("Recuperación", f"{res['recuperacion_meses']:.0f} meses")
            with col_m3:
                st.metric("Utilidad 20 años", f"${res['utilidad_20']:,.0f}")
            
            st.caption(f"ROI: {res['roi']}% | Nuevo salario promedio: ${res['nuevo_promedio']:,.2f}")

# ========== PESTAÑA 3: COMPARATIVA CORREGIDA ==========
with tab3:
    st.subheader("Comparativa de escenarios Modalidad 40")
    
    col1, col2 = st.columns(2)
    
    with col1:
        edad_comp = st.number_input("Edad actual", min_value=40, max_value=65, value=55, step=1, key="edad3")
        semanas_comp = st.number_input("Semanas cotizadas", min_value=0, max_value=3000, value=1315, step=1, key="sem3")
        salario_comp = st.number_input("Salario promedio ($)", min_value=0.0, max_value=10000.0, value=965.25, step=10.0, key="sal3")
    
    with col2:
        edad_retiro3 = st.selectbox("Edad de retiro", [60,61,62,63,64,65], index=0, key="retiro3")
        esposa3 = st.checkbox("¿Con asignación por esposa?", value=True, key="esposa3")
        salario_tope = st.number_input("Salario M40 ($)", min_value=0.0, max_value=20000.0, value=2932.0, step=100.0, key="tope3")
    
    if st.button("Comparar todos los escenarios", type="primary", use_container_width=True, key="btn3"):
        with st.spinner("Generando comparativa..."):
            
            base = calcular_pension(semanas_comp, salario_comp, edad_comp, edad_retiro3, esposa3)
            pension_base = base['mensual']
            
            meses_lista = [6,12,18,24,30,36,42,48]
            resultados = []
            pensiones_con_m40 = []
            incrementos = []
            inversiones = []
            
            for meses in meses_lista:
                r = calcular_mod40(semanas_comp, salario_comp, edad_comp, edad_retiro3, salario_tope, meses, esposa3)
                pensiones_con_m40.append(r['con_m40'])
                incrementos.append(r['incremento'])
                inversiones.append(r['inversion'])
                resultados.append({
                    "Meses": f"{meses}",
                    "Pensión Base": f"${pension_base:,.0f}",
                    "Pensión con M40": f"${r['con_m40']:,.0f}",
                    "Incremento": f"${r['incremento']:,.0f}",
                    "Inversión": f"${r['inversion']:,.0f}",
                    "Recuperación": f"{r['recuperacion_meses']:.0f} meses",
                    "Utilidad 20a": f"${r['utilidad_20']:,.0f}",
                    "ROI": f"{r['roi']}%"
                })
            
            st.divider()
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # GRÁFICA SIMPLE CON VALORES REALES
            st.subheader("📊 Pensión mensual por escenario")
            
            # Mostrar los valores para debug (opcional, puede borrarlo después)
            with st.expander("📊 Ver valores de la gráfica"):
                for i, m in enumerate(meses_lista):
                    st.write(f"{m} meses: Base=${pension_base:,.0f}, Con M40=${pensiones_con_m40[i]:,.0f}")
            
            # Crear DataFrame para la gráfica
            chart_df = pd.DataFrame({
                "Meses": [str(m) for m in meses_lista],
                "Sin M40": [pension_base] * len(meses_lista),
                "Con M40": pensiones_con_m40
            })
            
            # Gráfica de barras
            st.bar_chart(chart_df.set_index("Meses"))
            
            st.info(f"💡 **Pensión base sin M40:** ${pension_base:,.0f} mensuales")

# ========== PIE ==========
st.divider()
st.caption("© Ing. Roberto Villarreal - Versión Profesional con análisis completo")
