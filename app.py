import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title='OFD Control Tower',page_icon='📦',layout='wide')

st.markdown("""
<style>
.stApp {background-color:#0e1117;color:white;}
</style>
""", unsafe_allow_html=True)

st.title('📦 OFD Control Tower')
st.caption('Dashboard ejecutivo logístico')

f=st.file_uploader('Carga archivo OFD',type=['xls','xlsx'])
if f:
    df=pd.read_excel(f)
    df['LM Receive Date']=pd.to_datetime(df.get('LM Receive Date'),errors='coerce')
    df['Aging']=(pd.Timestamp.today()-df['LM Receive Date']).dt.days

    def score(r):
        s=0
        if pd.notna(r['Aging']) and r['Aging']>=5:s+=50
        if pd.notna(r.get('OFD Attempts')) and r.get('OFD Attempts',0)>=2:s+=20
        if pd.notna(r.get('Problem Type')):s+=20
        if str(r.get('Main Stage'))=='Report Suspected Loss':s+=100
        return s

    df['Priority Score']=df.apply(score,axis=1)
    df['Priority']=df['Priority Score'].apply(lambda x:'Crítico' if x>=100 else 'Alto' if x>=60 else 'Medio' if x>=30 else 'Normal')

    da=st.sidebar.multiselect('Driver',sorted(df['DA'].dropna().unique()))
    if da: df=df[df['DA'].isin(da)]

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('Inventario',len(df))
    c2.metric('Críticos',len(df[df.Priority=='Crítico']))
    c3.metric('Problemas',df['Problem Type'].notna().sum())
    c4.metric('Aging',round(df['Aging'].mean(),1))
    c5.metric('Drivers',df['DA'].nunique())

    a,b=st.columns(2)
    with a:
        p=df['Problem Type'].fillna('Sin problema').value_counts().reset_index()
        p.columns=['Problema','Total']
        st.plotly_chart(px.bar(p,x='Problema',y='Total',title='Problemas por Tipo'),use_container_width=True)
    with b:
        d=df.groupby('DA').size().reset_index(name='Total').sort_values('Total',ascending=False)
        st.plotly_chart(px.bar(d,x='DA',y='Total',title='Ranking DA'),use_container_width=True)

    a,b=st.columns(2)
    with a:
        st.plotly_chart(px.pie(df,names='Priority',title='Prioridades'),use_container_width=True)
    with b:
        ag=df.groupby(pd.cut(df['Aging'],[-1,2,4,7,999])).size().reset_index(name='Total')
        st.plotly_chart(px.bar(ag,x='Aging',y='Total',title='Aging'),use_container_width=True)

    st.subheader('🚨 Top 10 Casos')
    top=df.sort_values('Priority Score',ascending=False).head(10)
    st.dataframe(top,use_container_width=True)

    output=BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as writer:
        df.to_excel(writer,index=False)

    st.download_button('⬇ Exportar Excel Filtrado',output.getvalue(),'OFD_filtrado.xlsx')

    st.dataframe(df,use_container_width=True)
