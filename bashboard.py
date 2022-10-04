from multiprocessing import connection
from sqlalchemy import false
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import pathlib
import plotly.graph_objects as go
import matplotlib
import math
import altair as alt

millnames = ['',' K',' M',' mil M',' B']
def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def Productos(Fecha_inicial,Fecha_final):
    return pd.read_sql_query(f"SELECT NombreProducto as Producto, sum(Cantidad) as Ventas,sum(Cantidad*Precio) as Monto, strftime('%m',Factura.DtEmision)  as mes, strftime('%Y',Factura.DtEmision) as año FROM FacturaItem JOIN Factura on Factura.Id = FacturaItem.IdFactura WHERE Factura.DtEmision >= '{Fecha_inicial}' and Factura.DtEmision <='{Fecha_final}' GROUP by NombreProducto ORDER by Monto DESC",Conection_sql)


def gaugue_chart(Valor,rango_max,Titulo):
    return go.Figure(go.Indicator(mode="gauge+number",title={'text':Titulo},
                value=Valor, 
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {'axis': {'range': [None, rango_max]}},))
                


Folder_Path = r"c:\Users\horac\OneDrive\Documentos\GitHub\dashboard"
#Folder_Path= pathlib.Path().parent.absolute()
print(Folder_Path)
Conection_sql = sqlite3.Connection(Folder_Path+"\FacturaLight.db")

Ventas = pd.read_sql_query("Select Sum(Total) as Ventas,count(Total) as Clientes ,sum(Iva) as Impuestos, strftime('%m',DtEmision) as Mes, strftime('%Y',DtEmision) as Año From Factura Group By Mes,Año",Conection_sql)

Productos_total = pd.read_sql_query("Select Nombre as Producto, Sum(Cantidad) as Cantidad, PRODUCTO.Costo, PRODUCTO.LP1 AS Precio From FacturaItem JOIN Producto ON Producto.Id = FacturaItem.IdProducto group by Producto order by cantidad desc limit 10 offset 3",Conection_sql)

Ventas["Mes"]=pd.to_numeric(Ventas["Mes"])
Ventas["Año"]=pd.to_numeric(Ventas["Año"])


st.set_page_config(layout="wide")
####
#Sidebar
###
with st.sidebar:
    Lista_Meses=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    año_Selection = st.selectbox("Año:",sorted(Ventas["Año"].unique(), reverse=True))
    Ventas_Act=Ventas.query(f'Año=={año_Selection}')
    mes_Selection = st.selectbox("Mes:",Lista_Meses,index=Ventas_Act["Mes"].max()-1)
    mes_Selection_index =Lista_Meses.index(mes_Selection)
####
#Pagina Principal
###


st.title("Almacen de Picadas")


tab1,tab2,tab3,tab4,tab5 = st.tabs(["Anual","Mensual","12 meses","Productos","Variaciones"])

####
#Metricas Anuales
###

tab1.header(f"Metricas de Ventas Anuales: {año_Selection}")
col1,col2,col3,col4 = tab1.columns(4)

Ventas_Act=Ventas.query(f'Año=={año_Selection}')
ventas_ant=Ventas.query(f'Año=={año_Selection-1}')

Ventas_Anual=Ventas_Act["Ventas"].sum()
Crecimiento_Anual=((Ventas_Anual/ventas_ant["Ventas"].sum())-1)*100

col1.metric("Ventas",f"$ {millify(Ventas_Anual)}",f"{Crecimiento_Anual:.2f} %")

Dias_Ventas = pd.read_sql_query(f"Select count(distinct(strftime('%d-%m-%Y',DtEmision))) as Dias From Factura where Factura.DtEmision >= '{año_Selection}-01-01' and Factura.DtEmision <='{año_Selection}-12-31'",Conection_sql)

Estimacion = 365 *Ventas_Anual/ Dias_Ventas.iloc[0,0]
col2.metric("Estimacion Ventas",f"{millify(Estimacion)}")

Ventas_Anual=Ventas_Act["Clientes"].sum()
Crecimiento_Anual=((Ventas_Anual/ventas_ant["Clientes"].sum())-1)*100

col3.metric("Clientes",f"{Ventas_Anual:,}",f"{Crecimiento_Anual:.2f} %")

Fact_Prom=(Ventas_Act["Ventas"].sum()/Ventas_Act["Clientes"].sum())
Fact_Prom_ant=(ventas_ant["Ventas"].sum()/ventas_ant["Clientes"].sum())

col4.metric("Factura Promedio",f"$ {Fact_Prom:.2f}",f"{((Fact_Prom/Fact_Prom_ant)-1)*100:.2f} %")

col1,col2 = tab1.columns(2)

fig = gaugue_chart(Ventas_Act["Ventas"].sum(),ventas_ant["Ventas"].sum(),"Ventas Totales")
col1.plotly_chart(fig,height=300,width=300)

fig = gaugue_chart(Ventas_Act["Clientes"].sum(),ventas_ant["Clientes"].sum(),"Clientes Totales")

col2.plotly_chart(fig,height=300,width=300)


####
#Metricas Mensuales
###

tab2.header(f"Ventas {mes_Selection} vs {Lista_Meses[mes_Selection_index-1]}")
col1,col2,col3 = tab2.columns(3)

Ventas_Act=Ventas.query(f'Mes == {mes_Selection_index+1} & Año=={año_Selection}')

if mes_Selection_index>0:
    ventas_ant=Ventas.query(f'Mes == {mes_Selection_index} & Año=={año_Selection}')
else:
    ventas_ant=Ventas.query(f'Mes == 12 & Año=={año_Selection-1}')

col1.metric("Ventas",f"$ {millify(Ventas_Act.iloc[0,0])}",f"{((Ventas_Act.iloc[0,0]/ventas_ant.iloc[0,0])-1)*100:.2f} %")

col2.metric("Clientes",f"{Ventas_Act.iloc[0,1]}",f"{((Ventas_Act.iloc[0,1]/ventas_ant.iloc[0,1])-1)*100:.2f} %")

Fact_Prom=(Ventas_Act.iloc[0,0]/Ventas_Act.iloc[0,1])
Fact_Prom_ant=(ventas_ant.iloc[0,0]/ventas_ant.iloc[0,1])

col3.metric("Factura Promedio",f"$ {Fact_Prom:.2f}",f"{((Fact_Prom/Fact_Prom_ant)-1)*100:.2f} %")

col1,col2 = tab2.columns(2)

fig = gaugue_chart(Ventas_Act.iloc[0,0],ventas_ant.iloc[0,0],"Ventas Totales")
col1.plotly_chart(fig,height=300,width=300)

fig = gaugue_chart(Ventas_Act.iloc[0,1],ventas_ant.iloc[0,1],"Clientes Totales")
col2.plotly_chart(fig,height=300,width=300)

###
#Metricas 12 meses
###

tab3.header(f"Ventas {mes_Selection} / {año_Selection} vs {mes_Selection} / {año_Selection-1}")
col1,col2,col3 = tab3.columns(3)

Ventas_Act=Ventas.query(f'Mes == {mes_Selection_index+1} & Año=={año_Selection}')
ventas_ant=Ventas.query(f'Mes == {mes_Selection_index+1} & Año=={año_Selection-1}')

col1.metric("Ventas",f"$ {millify(Ventas_Act.iloc[0,0])}",f"{((Ventas_Act.iloc[0,0]/ventas_ant.iloc[0,0])-1)*100:.2f} %")
col2.metric("Clientes",f"{Ventas_Act.iloc[0,1]}",f"{((Ventas_Act.iloc[0,1]/ventas_ant.iloc[0,1])-1)*100:.2f} %")
Fact_Prom=(Ventas_Act.iloc[0,0]/Ventas_Act.iloc[0,1])
Fact_Prom_ant=(ventas_ant.iloc[0,0]/ventas_ant.iloc[0,1])

col3.metric("Factura Promedio",f"$ {Fact_Prom:.2f}",f"{((Fact_Prom/Fact_Prom_ant)-1)*100:.2f} %")

col1,col2 = tab3.columns(2)

fig = gaugue_chart(Ventas_Act.iloc[0,0],ventas_ant.iloc[0,0],"Ventas Totales")
col1.plotly_chart(fig,height=300,width=300)

fig = gaugue_chart(Ventas_Act.iloc[0,1],ventas_ant.iloc[0,1],"Clientes Totales")
col2.plotly_chart(fig,height=300,width=300)


####
#Metricas Productos
###

Productos_mes=Productos(f"{año_Selection}-{mes_Selection_index+1:02d}-1",f"{año_Selection}-{mes_Selection_index+1:02d}-31")

tab4.header(f"Metricas de Productos {mes_Selection} / {año_Selection} ")

col1,col2 = tab4.columns(2)
col1.subheader("Top 20 Productos mes")
col1.write(Productos_mes)

col1.write(alt.Chart(Productos_mes[["Producto","Monto"]][0:20]).mark_bar().encode(
    x=alt.X('Producto', sort=None),
    y='Monto',
).properties(height=500))

Productos_Anual=Productos(f"{año_Selection}-01-1",f"{año_Selection}-12-31")
col2.subheader("Top 20 Productos Anual")
col2.write(Productos_Anual)

col2.write(alt.Chart(Productos_Anual[["Producto","Monto"]][0:20]).mark_bar().encode(
    x=alt.X('Producto', sort=None),
    y='Monto',
).properties(height=500))


###
#Productos aumentos y bajas
###

Productos_mes=Productos(f"{año_Selection}-{mes_Selection_index+1:02d}-1",f"{año_Selection}-{mes_Selection_index+1:02d}-31")

tab5.header(f"Variacion de Productos {mes_Selection} / {año_Selection}")

if mes_Selection_index==1:
    mes_Selection_index=11

Productos_mes_2=Productos(f"{año_Selection}-{mes_Selection_index:02d}-1",f"{año_Selection}-{mes_Selection_index:02d}-31")
Producto_comparacion=  pd.merge(Productos_mes,Productos_mes_2,on="Producto")
Producto_comparacion.loc[:,"Variacion"]= (Producto_comparacion["Ventas_x"]/Producto_comparacion["Ventas_y"] -1)*100


col1,col2=tab5.columns(2)
col1.subheader("Variacion en de ventas en %")
col1.write(Producto_comparacion.loc[:,["Producto","Variacion"]].sort_values(by="Variacion",ascending=False))

col2.subheader("Top Productos")

Prodcto_top=Producto_comparacion.sort_values(by="Variacion").iloc[-1,0]
delta_top=Producto_comparacion.sort_values(by="Variacion").iloc[-1,-1]

col2.metric("Mayor aumento de ventas",value=Prodcto_top,delta=f"{delta_top:.2f} %")

Prodcto_top=Producto_comparacion.sort_values(by="Variacion").iloc[-2,0]
delta_top=Producto_comparacion.sort_values(by="Variacion").iloc[-2,-1]
col2.metric("Mayor aumento de ventas",value=Prodcto_top,delta=f"{delta_top:.2f} %")

Prodcto_top=Producto_comparacion.sort_values(by="Variacion").iloc[0,0]
delta_top=Producto_comparacion.sort_values(by="Variacion").iloc[0,-1]
col2.metric("Mayor descenso de ventas",value=Prodcto_top,delta=f"{delta_top:.2f} %")

Prodcto_top=Producto_comparacion.sort_values(by="Variacion").iloc[1,0]
delta_top=Producto_comparacion.sort_values(by="Variacion").iloc[1,-1]
col2.metric("Mayor descenso de ventas",value=Prodcto_top,delta=f"{delta_top:.2f} %")
