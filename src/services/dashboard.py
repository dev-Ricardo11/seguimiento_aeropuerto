import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import time

st.set_page_config(
    page_title="Gestión Aeropuerto",
    layout="wide",
    page_icon="✈️",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stDecoration"] {visibility: hidden;}

    /* Marca de agua RESTRINGIDO */
    .main::before {
        content: "RESTRINGIDO";
        position: fixed;
        top: 10px;
        right: 20px;
        font-size: 16px;
        color: #ff4444;
        font-weight: bold;
        z-index: 9999;
    }

    /* Estilos del título */
    .titulo-principal {
        background: linear-gradient(90deg, #20B2AA 0%, #3CB371 100%);
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: left;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* Estilos de tabla personalizada */
    .tabla-resumen {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }

    .tabla-resumen table {
        width: 100%;
        border-collapse: collapse;
    }

    .tabla-resumen th {
        background: #1a5f7a;
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #ddd;
    }

    .tabla-resumen td {
        padding: 12px;
        text-align: center;
        border: 1px solid #ddd;
        font-size: 18px;
    }

    /* Ajustes de gráficos */
    .stPlotlyChart {
        background: white;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

API_URL = "http://localhost:8000/ReservasGDS"

st.markdown('<div class="titulo-principal">Gestión Aeropuerto</div>', unsafe_allow_html=True)

modo_consulta = st.radio(
    "Modo de consulta:",
    ["Con rango de fechas", "Todas las reservas"],
    horizontal=True
)

if modo_consulta == "Con rango de fechas":
    col1, col2 = st.columns(2)
    fecha_inicio = col1.date_input("Desde", date(2025, 1, 1))
    fecha_fin = col2.date_input("Hasta", date.today())

    dias_diferencia = (fecha_fin - fecha_inicio).days
    if dias_diferencia > 365:
        st.warning("⚠️ El rango de fechas es muy amplio. Se recomienda consultar máximo 1 año.")
    elif dias_diferencia < 0:
        st.error("❌ La fecha de inicio debe ser menor a la fecha fin.")
        st.stop()

if st.button("🔍 Consultar datos"):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🔄 Conectando con la API...")
        progress_bar.progress(25)

        if modo_consulta == "Con rango de fechas":
            payload = {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            }
        else:
            payload = {}

        response = requests.post(API_URL, json=payload if payload else None, timeout=120)
        progress_bar.progress(50)
        status_text.text("📊 Procesando datos...")

        if response.status_code == 200:
            result = response.json()
            progress_bar.progress(75)

            if "data" in result:
                df = pd.DataFrame(result["data"])
            else:
                df = pd.DataFrame(result)

            progress_bar.progress(100)
            status_text.text("✅ Datos cargados correctamente")
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

            if df.empty:
                st.warning("⚠️ No hay registros procesados disponibles.")
            else:
                total_procesados = len(df)

                if modo_consulta == "Con rango de fechas":
                    dias = (fecha_fin - fecha_inicio).days + 1
                    promedio = round(total_procesados / dias, 2) if dias > 0 else 0
                    rango_fechas = f"{fecha_inicio.strftime('%d')} al {fecha_fin.strftime('%d %B')}"
                else:
                    df['id_hora'] = pd.to_datetime(df['id_hora'], errors='coerce')
                    df_con_fecha = df.dropna(subset=['id_hora'])

                    if not df_con_fecha.empty:
                        fecha_min = df_con_fecha['id_hora'].min()
                        fecha_max = df_con_fecha['id_hora'].max()
                        dias = (fecha_max - fecha_min).days + 1
                        promedio = round(total_procesados / dias, 2) if dias > 0 else 0
                        rango_fechas = f"{fecha_min.strftime('%d')} al {fecha_max.strftime('%d %B')}"
                    else:
                        promedio = 0
                        rango_fechas = "Rango completo"

                st.markdown(f"""
                <div class="tabla-resumen">
                    <table>
                        <thead>
                            <tr>
                                <th>CORTE</th>
                                <th>N. ASISTENCIAS</th>
                                <th>ASISTENCIAS PROMEDIO</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{rango_fechas}</td>
                                <td><strong>{total_procesados}</strong></td>
                                <td><strong>{promedio}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    if "Sucursal" in df.columns:
                        sucursal_count = df[df["Sucursal"] != "SIN SUCURSAL"]["Sucursal"].value_counts().reset_index()
                        sucursal_count.columns = ["Sucursal", "Total"]

                        fig_sucursal = go.Figure(data=[
                            go.Bar(
                                x=sucursal_count["Sucursal"],
                                y=sucursal_count["Total"],
                                text=sucursal_count["Total"],
                                textposition='outside',
                                marker=dict(
                                    color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd', '#8c564b']
                                ),
                                hovertemplate='<b>%{x}</b><br>Total: %{y}<extra></extra>'
                            )
                        ])

                        fig_sucursal.update_layout(
                            title={
                                'text': "SOLICITUDES POR ÁREA",
                                'x': 0.5,
                                'xanchor': 'center',
                                'font': {'size': 12, 'color': '#333', 'family': 'Arial, sans-serif'}
                            },
                            xaxis_title="",
                            yaxis_title="Cantidad de Reservas",
                            height=600,
                            showlegend=False,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=True, gridcolor='#e0e0e0')
                        )

                        st.plotly_chart(fig_sucursal, use_container_width=True)

                with col2:
                    if "id_cuenta_str" in df.columns:
                        top_cuentas = df[df["id_cuenta_str"] != "SIN CUENTA"]["id_cuenta_str"].value_counts().nlargest(5).reset_index()
                        top_cuentas.columns = ["Cuenta", "Total"]

                        fig_cuentas = go.Figure(data=[
                            go.Bar(
                                x=top_cuentas["Cuenta"],
                                y=top_cuentas["Total"],
                                text=top_cuentas["Total"],
                                textposition='outside',
                                marker=dict(color='#20B2AA'),
                                hovertemplate='<b>%{x}</b><br>Total: %{y}<extra></extra>'
                            )
                        ])

                        fig_cuentas.update_layout(
                            title={
                                'text': "TOP 5 CLIENTES",
                                'x': 0.5,
                                'xanchor': 'center',
                                'font': {'size': 16, 'color': '#333', 'family': 'Arial, sans-serif'}
                            },
                            xaxis_title="",
                            yaxis_title="Cantidad",
                            height=400,
                            showlegend=False,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=True, gridcolor='#e0e0e0')
                        )

                        st.plotly_chart(fig_cuentas, use_container_width=True)

                st.markdown("---")

                if "Sucursal" in df.columns:
                    sucursal_distrib = df[df["Sucursal"] != "SIN SUCURSAL"]["Sucursal"].value_counts().reset_index()
                    sucursal_distrib.columns = ["Categoría", "Total"]

                    fig_tipo = px.pie(
                        sucursal_distrib,
                        values="Total",
                        names="Categoría",
                        title="SOLICITUDES POR TIPO DE SERVICIO",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4
                    )

                    fig_tipo.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Total: %{value}<br>Porcentaje: %{percent}<extra></extra>'
                    )

                    fig_tipo.update_layout(
                        title={
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 16, 'color': '#333', 'family': 'Arial, sans-serif'}
                        },
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.05
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )

                    st.plotly_chart(fig_tipo, use_container_width=True)

                with st.expander("📋 Ver datos completos"):
                    st.dataframe(df, use_container_width=True)

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar datos en CSV",
                    data=csv,
                    file_name=f"dashboard_stats_{date.today().isoformat()}.csv",
                    mime="text/csv"
                )

        elif response.status_code == 500:
            progress_bar.empty()
            status_text.empty()
            error_detail = response.json().get('detail', 'Error desconocido')
            st.error(f"❌ Error en el servidor: {error_detail}")
        else:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error al conectar con la API. Código: {response.status_code}")

    except requests.exceptions.Timeout:
        progress_bar.empty()
        status_text.empty()
        st.error("⏱️ La solicitud tardó demasiado (>120s). Intenta con un rango de fechas más corto.")
    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        status_text.empty()
        st.error("❌ No se pudo conectar con la API. Verifica que esté corriendo en http://localhost:8000")
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Error inesperado: {str(e)}")
        with st.expander("🔍 Ver detalles del error"):
            st.code(str(e))
