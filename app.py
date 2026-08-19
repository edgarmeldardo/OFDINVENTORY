import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# -----------------------------
#-----------
st.set_page_config(
    page_title="OFD Control Tower",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 OFD Control Tower")
st.caption("Dashboard Ejecutivo Logístico")

# -----------------------------
# CARGA DE ARCHIVO
# -----------------------------
archivo = st.file_uploader(
    "Carga archivo OFD",
    type=["xls", "xlsx"]
)

if archivo:

    df = pd.read_excel(archivo)

    # -----------------------------
    # FECHAS
    # -----------------------------
    df["LM Receive Date"] = pd.to_datetime(
        df["LM Receive Date"],
        errors="coerce"
    )

    hoy = pd.Timestamp.today()

    df["Aging"] = (
        hoy - df["LM Receive Date"]
    ).dt.days

    # -----------------------------
    # PRIORIDAD
    # -----------------------------
    def calcular_score(row):

        score = 0

        if pd.notna(row["Aging"]) and row["Aging"] >= 5:
            score += 50

        if pd.notna(row.get("OFD Attempts")) and row["OFD Attempts"] >= 2:
            score += 20

        if pd.notna(row.get("Problem Type")):
            score += 20

        if str(row.get("Main Stage")) == "Report Suspected Loss":
            score += 100

        return score

    df["Priority Score"] = df.apply(
        calcular_score,
        axis=1
    )

    def prioridad(score):

        if score >= 100:
            return "Crítico"

        elif score >= 60:
            return "Alto"

        elif score >= 30:
            return "Medio"

        return "Normal"

    df["Priority"] = df["Priority Score"].apply(
        prioridad
    )

    # -----------------------------
    # FILTROS
    # -----------------------------
    st.sidebar.header("Filtros")

    drivers = st.sidebar.multiselect(
        "Driver",
        sorted(df["DA"].dropna().unique())
    )

    if drivers:
        df = df[df["DA"].isin(drivers)]

    # -----------------------------
    # KPIs
    # -----------------------------
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "📦 Inventario",
        len(df)
    )

    c2.metric(
        "🔴 Críticos",
        len(df[df["Priority"] == "Crítico"])
    )

    c3.metric(
        "⚠ Problemas",
        df["Problem Type"].notna().sum()
    )

    c4.metric(
        "📅 Aging",
        round(df["Aging"].mean(), 1)
    )

    c5.metric(
        "👤 Drivers",
        df["DA"].nunique()
    )

    # -----------------------------
    # GRÁFICOS SUPERIORES
    # -----------------------------
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Problemas por Tipo")

        problemas = (
            df["Problem Type"]
            .fillna("Sin problema")
            .value_counts()
            .reset_index()
        )

        problemas.columns = [
            "Problema",
            "Total"
        ]

        fig1 = px.bar(
            problemas,
            x="Problema",
            y="Total",
            color="Total"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with col2:

        st.subheader("Ranking Driver")

        ranking = (
            df.groupby("DA")
            .size()
            .reset_index(name="Total")
            .sort_values(
                "Total",
                ascending=False
            )
        )

        fig2 = px.bar(
            ranking,
            x="DA",
            y="Total",
            color="Total"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # -----------------------------
    # GRÁFICOS INFERIORES
    # -----------------------------
    col3, col4 = st.columns(2)

    with col3:

        st.subheader("Distribución de Prioridad")

        prioridad_df = (
            df["Priority"]
            .value_counts()
            .reset_index()
        )

        prioridad_df.columns = [
            "Prioridad",
            "Total"
        ]

        fig3 = px.pie(
            prioridad_df,
            names="Prioridad",
            values="Total"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    with col4:

        st.subheader("Distribución Aging")

        df["Rango Aging"] = pd.cut(
            df["Aging"],
            bins=[-1, 2, 4, 7, 999],
            labels=[
                "0-2 días",
                "3-4 días",
                "5-7 días",
                "8+ días"
            ]
        )

        aging_df = (
            df["Rango Aging"]
            .value_counts()
            .sort_index()
            .reset_index()
        )

        aging_df.columns = [
            "Rango",
            "Total"
        ]

        fig4 = px.bar(
            aging_df,
            x="Rango",
            y="Total",
            color="Total"
        )

        st.plotly_chart(
            fig4,
            use_container_width=True
        )

        # -----------------------------
    # GUIAS CON 5 DIAS O MAS
    # -----------------------------
    st.subheader("🚨 Guías con 5 días o más en estación")

    guias_criticas = (
        df[df["Aging"] >= 5]
        .sort_values(
            by="Aging",
            ascending=False
        )
    )

    columnas_guias = [
        "Waybill Number",
        "DA",
        "Aging",
        "OFD Attempts",
        "Consignee Address",
        "Problem Type"
    ]

    columnas_guias = [
        columna
        for columna in columnas_guias
        if columna in df.columns
    ]

    st.metric(
        "🔴 Total Guías +5 Días",
        len(guias_criticas)
    )

    st.dataframe(
        guias_criticas[columnas_guias],
        use_container_width=True
    )

    # -----------------------------
    # EXPORTAR
    # -----------------------------
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False
        )

    st.download_button(
        "⬇ Exportar Excel Filtrado",
        data=output.getvalue(),
        file_name="OFD_Filtrado.xlsx"
    )

    # -----------------------------
    # INVENTARIO COMPLETO
    # -----------------------------
    st.subheader("Inventario Completo")

    columnas_inventario = [
        "Aging",
        "OFD Time",
        "Waybill Number",
        "DA",
        "Consignee Address",
        "Problem Type"
    ]

    columnas_inventario = [
        columna
        for columna in columnas_inventario
        if columna in df.columns
    ]

    inventario_view = (
        df[columnas_inventario]
        .sort_values(
            by="Aging",
            ascending=False
        )
    )

    st.dataframe(
        inventario_view,
        use_container_width=True
    )
