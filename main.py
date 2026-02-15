import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

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
st.markdown('<div class="sub-header">Vibe coded by JhonatanChilet</div>', unsafe_allow_html=True)
st.markdown("---")

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

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
        self.set_font('Arial', 'B', 14)
        self.cell(80, 6, 'Rivulis Peru S.A.C.', 0, 2, 'L')
        
        self.set_font('Arial', '', 9)
        self.set_text_color(80, 80, 80)
        self.cell(80, 5, 'Av. Primavera Nro. 517 Int. 206', 0, 2, 'L')
        self.cell(80, 5, 'https://es.rivulis.com/', 0, 0, 'L')
        
        self.set_xy(120, y_inicial)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(0, 0, 0)
        self.cell(80, 6, f'COTIZACION: {st.session_state.get("num_cot", "001")}', 0, 1, 'R')
        self.ln(15) 

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, limpiar_texto(title), 1, 1, 'L', 1)

    def chapter_body(self, data):
        self.set_font('Arial', '', 8)
        self.set_fill_color(46, 125, 50)
        self.set_text_color(255, 255, 255)
        self.cell(10, 7, 'N°', 1, 0, 'C', 1) 
        self.cell(20, 7, 'Cod.', 1, 0, 'C', 1)
        self.cell(90, 7, 'Descripcion', 1, 0, 'C', 1)
        self.cell(15, 7, 'Cant.', 1, 0, 'C', 1)
        self.cell(25, 7, 'P.Unit ($)', 1, 0, 'C', 1)
        self.cell(30, 7, 'Total ($)', 1, 1, 'C', 1)

        self.set_text_color(0, 0, 0)
        total_capitulo = 0
        
        for index, row in data.iterrows():
            desc = (row['Descripcion'][:50] + '..') if len(str(row['Descripcion'])) > 50 else str(row['Descripcion'])
            
            self.cell(10, 6, str(int(row['Item'])), 1, 0, 'C')
            self.cell(20, 6, limpiar_texto(row['Codigo']), 1)
            self.cell(90, 6, limpiar_texto(desc), 1)
            self.cell(15, 6, f"{row['Cantidad']:,.2f}", 1, 0, 'R')
            self.cell(25, 6, f"{row['Precio']:,.2f}", 1, 0, 'R')
            
            total_item = row['Cantidad'] * row['Precio']
            self.cell(30, 6, f"{total_item:,.2f}", 1, 1, 'R')
            total_capitulo += total_item
            
        return total_capitulo

# --- BARRA LATERAL ---
st.sidebar.header("📂 1. Cargar Datos")
db_file = st.sidebar.file_uploader("Base de Precios (Excel)", type=["xlsx"])
project_file = st.sidebar.file_uploader("Metrados (Excel)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("📄 2. Datos del Proyecto (Para PDF)")
cliente_nombre = st.sidebar.text_input("Cliente / Razón Social", "AGROINDUSTRIAL DEL NORTE S.A.C.")
cliente_ruc = st.sidebar.text_input("RUC", "20123456789")
cliente_lugar = st.sidebar.text_input("Lugar de Entrega", "Fundo El Porvenir, km 165")
cotizacion_num = st.sidebar.text_input("N° Cotización", "COT-2026-005")
proyecto_nombre = st.sidebar.text_input("Nombre del Proyecto", "PROYECTO DE RIEGO POR GOTEO PARA EL CULTIVO DE ARÁNDANO")
area_ha = st.sidebar.number_input("Área del Proyecto (Hectáreas)", min_value=0.1, value=10.0, step=0.5)

st.session_state['num_cot'] = cotizacion_num

def estandarizar_codigo(valor):
    valor_str = str(valor).strip().upper()
    if valor_str in ['S.C.', 'S.C', 'SC', '0', 'NAN', 'NONE', '', 'NAT']: return 'S.C'
    if valor_str.endswith('.0'): return valor_str[:-2]
    return valor_str

if project_file and db_file:
    try:
        # --- CARGA INICIAL ---
        if 'df_master' not in st.session_state:
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

        st.info("💡 **Para añadir:** Haz clic en 'Add row'. Puedes llenar todos los datos sin que el cursor salte. El Dashboard se actualizará en vivo.")
        
        df_view.insert(0, '❌ Eliminar', False)

        # --- TABLA EDITABLE ---
        edited_df = st.data_editor(
            df_view,
            column_config={
                "❌ Eliminar": st.column_config.CheckboxColumn("Borrar", default=False, width="small"),
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
            height=500
        )

        # --- LÓGICA DE ACTUALIZACIÓN (SIN PERDER EL FOCO) ---
        if not edited_df.equals(df_view):
            
            necesita_recargar = False
            if edited_df['❌ Eliminar'].any():
                necesita_recargar = True
            
            edited_df = edited_df[edited_df['❌ Eliminar'] == False]
            edited_df = edited_df.drop(columns=['❌ Eliminar']) 
            
            edited_df['Partida'] = edited_df['Partida'].apply(lambda x: "NUEVO SISTEMA" if pd.isna(x) or x is None else str(x))
            edited_df['Descripcion'] = edited_df['Descripcion'].apply(lambda x: "" if pd.isna(x) or x is None else str(x))
            edited_df['Codigo'] = edited_df['Codigo'].apply(lambda x: "S.C" if pd.isna(x) or x is None else str(x))
            edited_df['Unidades'] = edited_df['Unidades'].apply(lambda x: "Und." if pd.isna(x) or x is None else str(x))

            edited_df['Cantidad'] = pd.to_numeric(edited_df['Cantidad'], errors='coerce').fillna(0)
            edited_df['Precio'] = pd.to_numeric(edited_df['Precio'], errors='coerce').fillna(0)
            edited_df['Total'] = edited_df['Cantidad'] * edited_df['Precio']
            
            if 'Item' in edited_df.columns:
                edited_df['Item'] = pd.to_numeric(edited_df['Item'], errors='coerce')
                max_item = st.session_state.df_master['Item'].max()
                if pd.isna(max_item): max_item = 0
                
                mask_nan = edited_df['Item'].isna()
                if mask_nan.any():
                    n_missing = mask_nan.sum()
                    edited_df.loc[mask_nan, 'Item'] = range(int(max_item) + 1, int(max_item) + 1 + n_missing)

            st.session_state.df_master.update(edited_df)
            
            nuevas_filas = edited_df[~edited_df.index.isin(st.session_state.df_master.index)]
            if not nuevas_filas.empty:
                st.session_state.df_master = pd.concat([st.session_state.df_master, nuevas_filas])
                
            filas_borradas = df_view[~df_view.index.isin(edited_df.index)]
            if not filas_borradas.empty:
                st.session_state.df_master = st.session_state.df_master.drop(index=filas_borradas.index, errors='ignore')

            if necesita_recargar:
                st.session_state.df_master = st.session_state.df_master.sort_values(by='Item').reset_index(drop=True)
                st.rerun()

        # --- CÁLCULOS FINALES ---
        total_neto = st.session_state.df_master['Total'].sum()
        igv = total_neto * 0.18
        total_venta = total_neto + igv
        precio_ha = total_venta / area_ha if area_ha > 0 else 0

        st.markdown("---")
        st.subheader("📊 Resumen Ejecutivo y Exportación")

        c_izq, c_der = st.columns([1, 1.2])

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
            
            def generar_pdf_bytes():
                pdf = PresupuestoPDF()
                pdf.add_page()
                
                pdf.set_draw_color(46, 125, 50)
                pdf.set_line_width(0.6)
                
                y_rect = pdf.get_y()
                pdf.rect(10, y_rect, 105, 30) 
                
                pdf.set_xy(12, y_rect + 2)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(100, 5, limpiar_texto(f"CLIENTE: {cliente_nombre}"), 0, 1) 
                
                pdf.set_x(12)
                pdf.cell(100, 5, limpiar_texto(f"RUC: {cliente_ruc}"), 0, 1)
                
                pdf.set_x(12)
                pdf.set_font('Arial', '', 9)
                pdf.cell(100, 5, limpiar_texto(f"LUGAR: {cliente_lugar}"), 0, 1)
                
                pdf.set_x(12)
                pdf.cell(100, 5, limpiar_texto(f"ÁREA: {area_ha:,.2f} Hectáreas"), 0, 1)
                
                pdf.set_x(12)
                pdf.cell(100, 5, f"FECHA: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
                
                pdf.ln(8) 
                
                pdf.section_title(f"RESUMEN EJECUTIVO: {cliente_nombre} - {proyecto_nombre}")
                pdf.ln(2)
                
                resumen = st.session_state.df_master.groupby('Partida')[['Total']].sum().reset_index()
                resumen.insert(0, 'N°', range(1, len(resumen) + 1)) 
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(10, 7, 'N°', 1, 0, 'C')
                pdf.cell(130, 7, 'Sistema / Partida', 1)
                pdf.cell(50, 7, 'Monto ($)', 1, 1, 'C')
                
                pdf.set_font('Arial', '', 10)
                for i, row in resumen.iterrows():
                    pdf.cell(10, 6, str(row['N°']), 1, 0, 'C')
                    pdf.cell(130, 6, limpiar_texto(row['Partida']), 1)
                    pdf.cell(50, 6, f"$ {row['Total']:,.2f}", 1, 1, 'R')
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(140, 7, 'TOTAL NETO (SIN IGV):', 1, 0, 'R')
                pdf.cell(50, 7, f"$ {total_neto:,.2f}", 1, 1, 'R')
                pdf.cell(140, 7, 'IGV (18%):', 1, 0, 'R')
                pdf.cell(50, 7, f"$ {igv:,.2f}", 1, 1, 'R')
                
                pdf.set_fill_color(46, 125, 50)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(140, 8, 'VALOR VENTA TOTAL:', 1, 0, 'R', 1)
                pdf.cell(50, 8, f"$ {total_venta:,.2f}", 1, 1, 'R', 1)
                
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(211, 47, 47) 
                pdf.cell(140, 7, f'COSTO POR HECTAREA ({area_ha} Ha):', 1, 0, 'R', 1)
                pdf.cell(50, 7, f"$ {precio_ha:,.2f}", 1, 1, 'R', 1)
                
                pdf.ln(10)
                pdf.set_text_color(0, 0, 0)

                sistemas_unicos = st.session_state.df_master['Partida'].unique()
                for sist in sistemas_unicos:
                    df_sist = st.session_state.df_master[st.session_state.df_master['Partida'] == sist]
                    if not df_sist.empty:
                        pdf.section_title(f"DETALLE: {sist}")
                        total_sis = pdf.chapter_body(df_sist)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(160, 6, 'SUBTOTAL SISTEMA:', 1, 0, 'R')
                        pdf.cell(30, 6, f"{total_sis:,.2f}", 1, 1, 'R')
                        pdf.ln(5)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        return f.read()

            st.download_button(
                label="📄 Descargar Presupuesto (PDF)",
                data=generar_pdf_bytes(),
                file_name=f"Presupuesto_{cotizacion_num}.pdf",
                mime="application/pdf",
                type="primary"
            )

        with c_der:
            with st.container(border=True):
                resumen_grafico = st.session_state.df_master.groupby('Partida')[['Total']].sum().reset_index()
                fig = px.pie(
                    resumen_grafico, 
                    values='Total', 
                    names='Partida', 
                    hole=0.45, 
                    title="Distribución de Costos por Sistema"
                )
                
                fig.update_traces(
                    textposition='outside',
                    textinfo='percent+label',
                    textfont=dict(size=14, color='black') 
                )
                
                fig.update_layout(
                    legend=dict(
                        font=dict(size=16), 
                        orientation="h",
                        yanchor="bottom", y=-0.5 
                    ),
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        st.write("Presiona F5 para refrescar la página.")
else:
    st.info("👋 Sube tus archivos para comenzar.")