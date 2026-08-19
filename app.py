import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="OFD Control Tower",
    page_icon="📦",
    layout="wide"
)

st.title("📦 OFD Control Tower")
st.caption("Dashboard Ejecutivo Logístico")

archivo = st.file_uploader(
    "Carga archivo OFD",
    type=["xls", "xlsx"]
)

if archivo is not None:

    df = pd.read_excel(archivo)

    df["LM Receive Date"] = pd.to_datetime(
        df["LM Receive Date"],
        errors="coerce"
    )

    df["Aging"] = (
        pd.Timestamp.today() - df["LM Receive Date"]
    ).dt.days

    st.sidebar.header("Filtros")

    if "DA" in df.columns:

        drivers = st.sidebar.multiselect(
            "Driver",
            sorted(df["DA"].dropna().unique())
        )

        if drivers:
            df = df[df["DA"].isin(drivers)]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📦 Inventario", len(df))

    c2.metric(
        "🔴 +5 Días",
        len(df[df["Aging"] >= 5])
    )

    c3.metric(
        "⚠ Problemas",
        df["Problem Type"].notna().sum()
        if "Problem Type" in df.columns else 0
    )

    c4.metric(
        "📅 Aging Promedio",
        round(df["Aging"].mean(), 1)
    )

    col1, col2 = st.columns(2)

    with col1:

        if "Problem Type" in df.columns:

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
                color="Total",
                title="Problemas por Tipo"
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

    with col2:

        if "DA" in df.columns:

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
                color="Total",
                title="Ranking Driver"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

    st.subheader("🚨 Top 5 Guías con Mayor Aging")

    top5 = (
        df[df["Aging"] >= 5]
        .sort_values(
            "Aging",
            ascending=False
        )
        .head(5)
    )

    columnas_top5 = [
        "Waybill Number",
        "Aging",
        "DA",
        "Consignee Address",
        "Problem Type"
    ]

    columnas_top5 = [
        c for c in columnas_top5
        if c in df.columns
    ]

    st.dataframe(
        top5[columnas_top5],
        use_container_width=True
    )

    st.subheader("🚨 Guías con 5 Días o Más en Estación")

    guias5 = (
        df[df["Aging"] >= 5]
        .sort_values(
            "Aging",
            ascending=False
        )
    )

    st.metric(
        "Total Guías +5 Días",
        len(guias5)
    )

    st.dataframe(
        guias5[columnas_top5],
        use_container_width=True
    )

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
        c for c in columnas_inventario
        if c in df.columns
    ]

    inventario = (
        df[columnas_inventario]
        .sort_values(
            "Aging",
            ascending=False
        )
    )

    st.dataframe(
        inventario,
        use_container_width=True
    )
