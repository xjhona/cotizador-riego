import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
import tempfile
import os
import io
import json
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador AgroCost Pro", layout="wide", page_icon="🌱")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #2E7D32; font-weight: bold; margin-bottom: 0px;}
    .sub-header { font-size: 1rem; color: #666; margin-top: -10px; margin-bottom: 25px; font-style: italic;}
    .resumen-caja { background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌱 Cotizador de Proyectos de Riego</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Vibe coded by Jhonatan Chilet</div>', unsafe_allow_html=True)
st.markdown("---")

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

# --- CARPETA DE GUARDADO LOCAL ---
SAVE_DIR = "cotizaciones_guardadas"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- INICIALIZAR VARIABLES DE SESIÓN (Para que al cargar se actualicen los textos) ---
if 'cotizacion_num' not in st.session_state: st.session_state.cotizacion_num = "COT-2026-005"
if 'cliente_nombre' not in st.session_state: st.session_state.cliente_nombre = "AGROINDUSTRIAL DEL NORTE S.A.C."
if 'cliente_ruc' not in st.session_state: st.session_state.cliente_ruc = "20123456789"
if 'cliente_lugar' not in st.session_state: st.session_state.cliente_lugar = "Fundo El Porvenir, km 165"
if 'proyecto_nombre' not in st.session_state: st.session_state.proyecto_nombre = "PROYECTO DE RIEGO POR GOTEO PARA EL CULTIVO DE ARÁNDANO"
if 'area_ha' not in st.session_state: st.session_state.area_ha = 10.0

# --- CLASE PARA EL PDF ---
class PresupuestoPDF(FPDF):
    def header(self):
        y_inicial = 10
        margen_texto = 10
        
        logo_path = "logo.png" if os.path.exists("logo.png") else ("logo.jpg" if os.path.exists("logo.jpg") else "")
        if logo_path:
            self.image(logo_path, 10, y_inicial, 30) 
            margen_texto = 45 
            
        self.set_xy(margen_texto, y_inicial)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(46, 125, 50) 
        self.cell(80, 6, 'Rivulis Peru S.A.C.', 0, 2, 'L')
        
        self.set_font('Arial', '', 9)
        self.set_text_color(80, 80, 80)
        self.cell(80, 5, 'Av. Primavera Nro. 517 Int. 206', 0, 2, 'L')
        self.cell(80, 5, 'https://es.rivulis.com/', 0, 0, 'L')
        
        self.set_xy(140, y_inicial)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(150, 150, 150)
        self.cell(60, 5, 'DOCUMENTO N°', 0, 1, 'R')
        self.set_x(140)
        self.set_font('Arial', 'B', 13)
        self.set_text_color(0, 0, 0)
        self.cell(60, 6, st.session_state.cotizacion_num, 0, 1, 'R')
        self.ln(12) 

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y()) 
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.ln(4)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(46, 125, 50)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, f"  {limpiar_texto(title).upper()}", 0, 1, 'L', 1)
        self.ln(2)

    def chapter_body(self, data):
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(235, 235, 235)
        self.set_text_color(50, 50, 50)
        self.set_draw_color(255, 255, 255) 
        
        self.cell(10, 7, 'N°', 1, 0, 'C', 1) 
        self.cell(20, 7, 'Cod.', 1, 0, 'C', 1)
        self.cell(90, 7, 'Descripcion', 1, 0, 'L', 1) 
        self.cell(15, 7, 'Cant.', 1, 0, 'C', 1)
        self.cell(25, 7, 'P.Unit ($)', 1, 0, 'R', 1)
        self.cell(30, 7, 'Total ($)', 1, 1, 'R', 1)

        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        total_capitulo = 0
        fill = False 
        
        for index, row in data.iterrows():
            desc = (row['Descripcion'][:60] + '..') if len(str(row['Descripcion'])) > 60 else str(row['Descripcion'])
            if fill:
                self.set_fill_color(248, 250, 248)
            else:
                self.set_fill_color(255, 255, 255)
                
            self.cell(10, 6, str(int(row['Item'])), 0, 0, 'C', fill)
            self.cell(20, 6, limpiar_texto(row['Codigo']), 0, 0, 'C', fill)
            self.cell(90, 6, limpiar_texto(desc), 0, 0, 'L', fill)
            self.cell(15, 6, f"{row['Cantidad']:,.2f}", 0, 0, 'C', fill)
            self.cell(25, 6, f"{row['Precio']:,.2f}", 0, 0, 'R', fill)
            
            total_item = row['Cantidad'] * row['Precio']
            self.cell(30, 6, f"{total_item:,.2f}", 0, 1, 'R', fill)
            total_capitulo += total_item
            fill = not fill 
            
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        return total_capitulo

# --- BARRA LATERAL ---
st.sidebar.header("📂 1. Cargar Datos Iniciales")
db_file = st.sidebar.file_uploader("Base de Precios (Excel)", type=["xlsx"])
project_file = st.sidebar.file_uploader("Metrados (Excel)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("📄 2. Datos del Cliente")
st.sidebar.text_input("Cliente / Razón Social", key="cliente_nombre")
st.sidebar.text_input("RUC", key="cliente_ruc")
st.sidebar.text_input("Lugar de Entrega", key="cliente_lugar")
st.sidebar.text_input("Nombre del Proyecto", key="proyecto_nombre")
st.sidebar.number_input("Área del Proyecto (Hectáreas)", min_value=0.1, step=0.5, key="area_ha")

st.sidebar.markdown("---")
st.sidebar.header("👤 3. Datos del Vendedor")
st.sidebar.text_input("N° Cotización", key="cotizacion_num")
vendedor_nombre = st.sidebar.text_input("Ejecutivo Comercial", "Ing. Jhonatan Chilet")
vendedor_celular = st.sidebar.text_input("Número Celular", "+51 987 654 321")
vendedor_correo = st.sidebar.text_input("Correo Electrónico", "jchilet@rivulis.com")

st.sidebar.markdown("---")
st.sidebar.header("💾 4. Historial (Sistema de Guardado)")
c_save, c_load = st.sidebar.columns(2)
with c_save:
    if st.button("💾 Guardar Cotización"):
        if 'df_master' in st.session_state:
            datos_guardar = {
                "meta": {
                    "cliente_nombre": st.session_state.cliente_nombre,
                    "cliente_ruc": st.session_state.cliente_ruc,
                    "cliente_lugar": st.session_state.cliente_lugar,
                    "proyecto_nombre": st.session_state.proyecto_nombre,
                    "area_ha": st.session_state.area_ha,
                    "cotizacion_num": st.session_state.cotizacion_num
                },
                "data": st.session_state.df_master.to_dict('records')
            }
            nombre_archivo = f"{SAVE_DIR}/{st.session_state.cotizacion_num}.json"
            with open(nombre_archivo, "w") as f:
                json.dump(datos_guardar, f)
            st.success(f"¡{st.session_state.cotizacion_num} guardada con éxito!")
        else:
            st.error("Sube los archivos Excel primero.")

archivos_guardados = [f for f in os.listdir(SAVE_DIR) if f.endswith('.json')]
if archivos_guardados:
    seleccion_archivo = st.sidebar.selectbox("📂 Cargar anterior:", ["-- Seleccionar --"] + archivos_guardados)
    if seleccion_archivo != "-- Seleccionar --":
        if st.sidebar.button("📥 Cargar a la tabla"):
            with open(f"{SAVE_DIR}/{seleccion_archivo}", "r") as f:
                datos_cargados = json.load(f)
                
                # Restaurar Metadata
                st.session_state.cliente_nombre = datos_cargados["meta"]["cliente_nombre"]
                st.session_state.cliente_ruc = datos_cargados["meta"]["cliente_ruc"]
                st.session_state.cliente_lugar = datos_cargados["meta"]["cliente_lugar"]
                st.session_state.proyecto_nombre = datos_cargados["meta"]["proyecto_nombre"]
                st.session_state.area_ha = datos_cargados["meta"]["area_ha"]
                st.session_state.cotizacion_num = datos_cargados["meta"]["cotizacion_num"]
                
                # Restaurar Tabla
                st.session_state.df_master = pd.DataFrame(datos_cargados["data"])
                st.rerun()

def estandarizar_codigo(valor):
    valor_str = str(valor).strip().upper()
    if valor_str in ['S.C.', 'S.C', 'SC', '0', 'NAN', 'NONE', '', 'NAT']: return 'S.C'
    if valor_str.endswith('.0'): return valor_str[:-2]
    return valor_str

if project_file and db_file or 'df_master' in st.session_state:
    try:
        # --- CARGA INICIAL (Solo si no hay datos guardados/cargados en memoria) ---
        if 'df_master' not in st.session_state and project_file and db_file:
            df_precios = pd.read_excel(db_file)
            df_proyecto = pd.read_excel(project_file)
            
            df_precios.columns = df_precios.columns.str.strip()
            df_proyecto.columns = df_proyecto.columns.str.strip()
            if 'Código' in df_proyecto.columns: df_proyecto.rename(columns={'Código': 'Codigo'}, inplace=True)
            if 'Código' in df_precios.columns: df_precios.rename(columns={'Código': 'Codigo'}, inplace=True)
            
            df_proyecto['Codigo'] = df_proyecto['Codigo'].apply(estandarizar_codigo)
            df_precios['Codigo'] = df_precios['Codigo'].apply(estandarizar_codigo)

            df_agrupado = df_proyecto.groupby(['Partida', 'Codigo', 'Descripcion', 'Unidades'], as_index=False)['Cantidad'].sum()
            df_final = pd.merge(df_agrupado, df_precios[['Codigo', 'Precio']], on='Codigo', how='left')
            df_final['Precio'] = df_final['Precio'].fillna(0.0)
            df_final['Total'] = df_final['Cantidad'] * df_final['Precio']
            
            df_final = df_final.sort_values(by=['Partida', 'Descripcion']).reset_index(drop=True)
            df_final.insert(0, 'Item', range(1, len(df_final) + 1))
            st.session_state.df_master = df_final

        # --- FILTROS ---
        st.header("📝 Editor de Cotización")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: busqueda = st.text_input("🔍 Buscar material:")
        with col2: 
            lista_sistemas = [str(s) for s in st.session_state.df_master['Partida'].unique() if pd.notna(s)]
            sistemas = st.multiselect("Filtro Sistema", sorted(lista_sistemas), default=[])
        with col3:
            orden = st.selectbox("🔃 Ordenar por:", ["N° de Fila (Item)", "Partida (Agrupado)", "Precio TOTAL (Mayor a Menor)", "Cantidad (Mayor a Menor)"])

        df_view = st.session_state.df_master.copy()
        
        if busqueda:
            mask = df_view['Descripcion'].astype(str).str.contains(busqueda, case=False, na=False) | \
                   df_view['Codigo'].astype(str).str.contains(busqueda, case=False, na=False)
            df_view = df_view[mask]
        if sistemas: df_view = df_view[df_view['Partida'].isin(sistemas)]
            
        if orden == "Precio TOTAL (Mayor a Menor)": df_view = df_view.sort_values(by='Total', ascending=False)
        elif orden == "Cantidad (Mayor a Menor)": df_view = df_view.sort_values(by='Cantidad', ascending=False)
        elif orden == "Partida (Agrupado)": df_view = df_view.sort_values(by=['Partida', 'Descripcion'])
        else: df_view = df_view.sort_values(by='Item', ascending=True)

        st.info("💡 **Fluidez total:** Modifica todo lo que quieras. Al terminar, presiona el botón verde.")

        # --- TABLA EDITABLE ---
        edited_df = st.data_editor(
            df_view,
            column_config={
                "Item": st.column_config.NumberColumn("N°", format="%d", disabled=False),
                "Total": st.column_config.NumberColumn("Total ($)", format="%.2f", disabled=True),
                "Precio": st.column_config.NumberColumn("P. Unitario ($)", format="%.2f", min_value=0.0),
                "Cantidad": st.column_config.NumberColumn("Cantidad", format="%.2f"),
                "Partida": st.column_config.TextColumn("Sistema"),
                "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
                "Unidades": st.column_config.TextColumn("Und."),
                "Codigo": st.column_config.TextColumn("Cód.", disabled=False),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_principal",
            num_rows="dynamic",
            height=450
        )

        # --- BOTÓN DE RECALCULAR ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_espacio, col_boton, col_espacio2 = st.columns([1, 2, 1])
        with col_boton:
            if st.button("🔄 Recalcular y Actualizar Dashboard", type="primary", use_container_width=True):
                
                deleted_indices = df_view.index.difference(edited_df.index)
                if not deleted_indices.empty:
                    st.session_state.df_master.drop(index=deleted_indices, inplace=True, errors='ignore')

                existing_indices = edited_df.index.intersection(st.session_state.df_master.index)
                st.session_state.df_master.loc[existing_indices] = edited_df.loc[existing_indices]
                
                new_indices = edited_df.index.difference(st.session_state.df_master.index)
                if not new_indices.empty:
                    st.session_state.df_master = pd.concat([st.session_state.df_master, edited_df.loc[new_indices]])
                
                st.session_state.df_master['Partida'] = st.session_state.df_master['Partida'].fillna("NUEVO SISTEMA")
                st.session_state.df_master['Descripcion'] = st.session_state.df_master['Descripcion'].fillna("")
                st.session_state.df_master['Codigo'] = st.session_state.df_master['Codigo'].fillna("S.C")
                st.session_state.df_master['Unidades'] = st.session_state.df_master['Unidades'].fillna("Und.")
                
                st.session_state.df_master['Cantidad'] = pd.to_numeric(st.session_state.df_master['Cantidad'], errors='coerce').fillna(0)
                st.session_state.df_master['Precio'] = pd.to_numeric(st.session_state.df_master['Precio'], errors='coerce').fillna(0)
                st.session_state.df_master['Total'] = st.session_state.df_master['Cantidad'] * st.session_state.df_master['Precio']
                
                st.session_state.df_master = st.session_state.df_master.sort_values(by='Item', na_position='last').reset_index(drop=True)
                st.session_state.df_master['Item'] = range(1, len(st.session_state.df_master) + 1)
                
                st.rerun() 

        # --- CÁLCULOS FINALES ---
        total_neto = st.session_state.df_master['Total'].sum()
        igv = total_neto * 0.18
        total_venta = total_neto + igv
        precio_ha = total_venta / st.session_state.area_ha if st.session_state.area_ha > 0 else 0

        st.markdown("---")
        st.subheader("📊 Resumen Ejecutivo y Exportación")

        c_izq, c_der = st.columns([1, 1.2])

        resumen_grafico = st.session_state.df_master.groupby('Partida')[['Total']].sum().reset_index()
        fig_donut_web = None
        if resumen_grafico['Total'].sum() > 0:
            fig_donut_web = px.pie(
                resumen_grafico, values='Total', names='Partida', hole=0.45, title="Distribución de Costos por Sistema"
            )
            fig_donut_web.update_traces(textposition='outside', textinfo='percent+label', textfont=dict(size=14, color='black'))
            fig_donut_web.update_layout(legend=dict(font=dict(size=16), orientation="h", yanchor="bottom", y=-0.5), margin=dict(t=40, b=40, l=40, r=40))

        with c_izq:
            st.markdown(f"""
            <div class="resumen-caja">
                <h3 style="color: #2e7d32; margin:0;">TOTAL NETO (SIN IGV): $ {total_neto:,.2f}</h3>
                <h3 style="color: #555; margin:0; margin-top:5px;">IGV (18%): $ {igv:,.2f}</h3>
                <hr style="margin: 15px 0;">
                <h2 style="color: #1b5e20; margin:0;">VALOR VENTA TOTAL: $ {total_venta:,.2f}</h2>
                <h3 style="color: #d32f2f; margin-top:10px;">Costo por Hectárea: $ {precio_ha:,.2f} / Ha</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(" ")
            
            # --- FUNCIONES DE EXPORTACIÓN ---
            def generar_excel():
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Exportamos la data maestra y la del resumen
                    st.session_state.df_master.to_excel(writer, index=False, sheet_name='Detalle Cotización')
                    resumen.to_excel(writer, index=False, sheet_name='Resumen Sistemas')
                return output.getvalue()

            def generar_pdf_bytes():
                pdf = PresupuestoPDF()
                pdf.add_page()
                
                y_rect = pdf.get_y()
                pdf.set_fill_color(245, 248, 245) 
                pdf.rect(10, y_rect, 190, 26, 'F')
                pdf.set_fill_color(46, 125, 50) 
                pdf.rect(10, y_rect, 2, 26, 'F')
                
                pdf.set_xy(15, y_rect + 4)
                pdf.set_font('Arial', 'B', 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(90, 4, "DATOS DEL CLIENTE", 0, 0)
                
                pdf.set_xy(110, y_rect + 4)
                pdf.cell(90, 4, "ATENDIDO POR", 0, 1)
                
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_x(15)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(95, 5, limpiar_texto(st.session_state.cliente_nombre), 0, 0) 
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(vendedor_nombre), 0, 1)
                
                pdf.set_x(15)
                pdf.set_font('Arial', '', 9)
                pdf.cell(95, 5, limpiar_texto(f"RUC: {st.session_state.cliente_ruc}"), 0, 0)
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(f"Celular: {vendedor_celular}"), 0, 1)
                
                pdf.set_x(15)
                pdf.cell(95, 5, limpiar_texto(f"Lugar: {st.session_state.cliente_lugar}"), 0, 0)
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(f"Correo: {vendedor_correo}"), 0, 1)
                
                pdf.ln(6) 
                
                def dibujar_resumen_y_totales(pdf_obj):
                    pdf_obj.set_font('Arial', 'B', 9)
                    pdf_obj.set_fill_color(235, 235, 235)
                    pdf_obj.set_text_color(50, 50, 50)
                    pdf_obj.set_draw_color(255, 255, 255)
                    
                    pdf_obj.cell(10, 7, 'N°', 1, 0, 'C', 1)
                    pdf_obj.cell(130, 7, 'Sistema / Partida', 1, 0, 'L', 1)
                    pdf_obj.cell(50, 7, 'Monto ($)', 1, 1, 'R', 1)
                    
                    pdf_obj.set_font('Arial', '', 9)
                    pdf_obj.set_text_color(0, 0, 0)
                    fill_resumen = False
                    for i, row in resumen.iterrows():
                        if fill_resumen:
                            pdf_obj.set_fill_color(248, 250, 248)
                        else:
                            pdf_obj.set_fill_color(255, 255, 255)
                            
                        pdf_obj.cell(10, 6, str(row['N°']), 0, 0, 'C', fill_resumen)
                        pdf_obj.cell(130, 6, limpiar_texto(row['Partida']), 0, 0, 'L', fill_resumen)
                        pdf_obj.cell(50, 6, f"$ {row['Total']:,.2f}", 0, 1, 'R', fill_resumen)
                        fill_resumen = not fill_resumen
                    
                    pdf_obj.ln(5)
                    pdf_obj.set_font('Arial', '', 11)
                    pdf_obj.cell(140, 7, 'TOTAL NETO (SIN IGV):', 0, 0, 'R')
                    pdf_obj.cell(50, 7, f"$ {total_neto:,.2f}", 0, 1, 'R')
                    
                    pdf_obj.cell(140, 7, 'IGV (18%):', 0, 0, 'R')
                    pdf_obj.cell(50, 7, f"$ {igv:,.2f}", 0, 1, 'R')
                    
                    pdf_obj.set_font('Arial', 'B', 14)
                    pdf_obj.set_text_color(46, 125, 50) 
                    pdf_obj.cell(140, 10, 'VALOR VENTA TOTAL:', 0, 0, 'R')
                    pdf_obj.cell(50, 10, f"$ {total_venta:,.2f}", 0, 1, 'R')
                    
                    pdf_obj.set_font('Arial', 'B', 11)
                    pdf_obj.set_text_color(211, 47, 47) 
                    pdf_obj.cell(140, 7, f'COSTO POR HECTAREA ({st.session_state.area_ha} Ha):', 0, 0, 'R')
                    pdf_obj.cell(50, 7, f"$ {precio_ha:,.2f}", 0, 1, 'R')
                    
                    pdf_obj.set_text_color(0, 0, 0)
                    pdf_obj.ln(8)

                # --- HOJA 1 ---
                pdf.section_title(f"Resumen: {st.session_state.proyecto_nombre}")
                dibujar_resumen_y_totales(pdf)

                # --- HOJAS DE DETALLES ---
                sistemas_unicos = st.session_state.df_master['Partida'].unique()
                for sist in sistemas_unicos:
                    df_sist = st.session_state.df_master[st.session_state.df_master['Partida'] == sist].copy()
                    if not df_sist.empty:
                        df_sist = df_sist.sort_values(by='Total', ascending=False)
                        
                        pdf.section_title(sist)
                        total_sis = pdf.chapter_body(df_sist)
                        
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_text_color(46, 125, 50)
                        pdf.cell(160, 6, 'SUBTOTAL SISTEMA:', 0, 0, 'R')
                        pdf.cell(30, 6, f"$ {total_sis:,.2f}", 0, 1, 'R')
                        pdf.set_text_color(0, 0, 0)
                        pdf.ln(3)

                # --- ÚLTIMA HOJA CON GRÁFICO ---
                pdf.add_page() 
                pdf.section_title("Resumen Financiero y Distribucion")
                dibujar_resumen_y_totales(pdf)
                
                # --- MATPLOTLIB (CORRECCIÓN DE ETIQUETAS CENTRADAS) ---
                if not resumen_grafico.empty and resumen_grafico['Total'].sum() > 0:
                    try:
                        fig_mat, ax = plt.subplots(figsize=(10, 5))
                        colores = plt.cm.Set2.colors
                        
                        wedges, texts, autotexts = ax.pie(
                            resumen_grafico['Total'], 
                            labels=[limpiar_texto(x) for x in resumen_grafico['Partida']],
                            autopct='%1.1f%%', 
                            pctdistance=0.75, # <--- ESTO CENTRA LOS PORCENTAJES EN EL ANILLO
                            startangle=140,
                            colors=colores,
                            wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
                            textprops=dict(color="black", fontsize=10, weight="bold")
                        )
                        
                        # Garantizamos el centrado absoluto de cada etiqueta de porcentaje
                        for autotext in autotexts:
                            autotext.set_horizontalalignment('center')
                            autotext.set_verticalalignment('center')
                            
                        ax.set_title("Distribucion de Costos por Sistema", fontsize=14, weight='bold')
                        fig_mat.patch.set_facecolor('white')
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_jpg:
                            plt.savefig(tmp_jpg.name, format='jpg', bbox_inches='tight', facecolor='white', dpi=300)
                            plt.close(fig_mat) 
                            
                        pdf.image(tmp_jpg.name, x=15, y=pdf.get_y(), w=180)
                        os.unlink(tmp_jpg.name)
                        
                    except Exception as e:
                        pdf.set_font('Arial', 'I', 9)
                        pdf.cell(0, 10, f"* Nota: No se pudo generar el grafico ({e}).", 0, 1, 'C')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_final:
                    pdf.output(tmp_final.name)
                    with open(tmp_final.name, "rb") as f:
                        return f.read()

            # --- BOTONES LADO A LADO ---
            col_descargar_pdf, col_descargar_excel = st.columns(2)
            
            with col_descargar_pdf:
                st.download_button(
                    label="📄 Descargar Presupuesto (PDF)",
                    data=generar_pdf_bytes(),
                    file_name=f"Presupuesto_{st.session_state.cotizacion_num}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            
            with col_descargar_excel:
                st.download_button(
                    label="📊 Descargar en Excel",
                    data=generar_excel(),
                    file_name=f"Presupuesto_{st.session_state.cotizacion_num}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with c_der:
            with st.container(border=True):
                if fig_donut_web:
                    st.plotly_chart(fig_donut_web, use_container_width=True)
                else:
                    st.info("Aún no hay costos asignados para generar el gráfico.")

    except Exception as e:
        st.error(f"⚠️ Error de datos: Revisa que los archivos sean correctos. Detalle: {e}")
        st.write("Presiona F5 para limpiar la memoria si persiste el error.")
else:
    st.info("👋 Sube tus archivos Excel en el panel lateral o carga una cotización guardada.")