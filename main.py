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
st.markdown('<div class="sub-header">Vibe coded by Jhonatan Chilet</div>', unsafe_allow_html=True)
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
        self.cell(60, 6, f'{st.session_state.get("num_cot", "001")}', 0, 1, 'R')
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
            
            self.set_fill_color(248, 250, 248) if fill else self.set_fill_color(255, 255, 255)
                
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
st.sidebar.header("📂 1. Cargar Datos")
db_file = st.sidebar.file_uploader("Base de Precios (Excel)", type=["xlsx"])
project_file = st.sidebar.file_uploader("Metrados (Excel)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("📄 2. Datos del Cliente")
cliente_nombre = st.sidebar.text_input("Cliente / Razón Social", "AGROINDUSTRIAL DEL NORTE S.A.C.")
cliente_ruc = st.sidebar.text_input("RUC", "20123456789")
cliente_lugar = st.sidebar.text_input("Lugar de Entrega", "Fundo El Porvenir, km 165")
proyecto_nombre = st.sidebar.text_input("Nombre del Proyecto", "PROYECTO DE RIEGO POR GOTEO PARA EL CULTIVO DE ARÁNDANO")
area_ha = st.sidebar.number_input("Área del Proyecto (Hectáreas)", min_value=0.1, value=10.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.header("👤 3. Datos del Vendedor")
cotizacion_num = st.sidebar.text_input("N° Cotización", "COT-2026-005")
vendedor_nombre = st.sidebar.text_input("Ejecutivo Comercial", "Ing. Jhonatan Chilet")
vendedor_celular = st.sidebar.text_input("Número Celular", "+51 987 654 321")
vendedor_correo = st.sidebar.text_input("Correo Electrónico", "jchilet@rivulis.com")

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

        st.info("💡 **Cómo usar:** Haz clic en 'Add row' para agregar. Llena los datos **tranquilamente celda por celda**. Al terminar, haz clic en el botón verde de abajo para actualizar los cálculos.")

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

        # --- LÓGICA DE GUARDADO EN SEGUNDO PLANO ---
        if not edited_df.equals(df_view):
            
            edited_df['Partida'] = edited_df['Partida'].fillna("NUEVO SISTEMA")
            edited_df['Descripcion'] = edited_df['Descripcion'].fillna("")
            edited_df['Codigo'] = edited_df['Codigo'].fillna("S.C")
            edited_df['Unidades'] = edited_df['Unidades'].fillna("Und.")

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

            existing_indices = edited_df.index.intersection(st.session_state.df_master.index)
            st.session_state.df_master.loc[existing_indices] = edited_df.loc[existing_indices]
            
            new_indices = edited_df.index.difference(st.session_state.df_master.index)
            if not new_indices.empty:
                st.session_state.df_master = pd.concat([st.session_state.df_master, edited_df.loc[new_indices]])
                
            deleted_indices = df_view.index.difference(edited_df.index)
            if not deleted_indices.empty:
                st.session_state.df_master.drop(index=deleted_indices, inplace=True, errors='ignore')

        # --- BOTÓN DE RECALCULAR Y ACTUALIZAR ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_espacio, col_boton, col_espacio2 = st.columns([1, 2, 1])
        with col_boton:
            if st.button("🔄 Recalcular y Actualizar Dashboard", type="primary", use_container_width=True):
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
        precio_ha = total_venta / area_ha if area_ha > 0 else 0

        st.markdown("---")
        st.subheader("📊 Resumen Ejecutivo y Exportación")

        c_izq, c_der = st.columns([1, 1.2])

        # Creamos la figura Donut primero para usarla tanto en Dashboard como en PDF
        resumen_grafico = st.session_state.df_master.groupby('Partida')[['Total']].sum().reset_index()
        fig_donut = None
        if resumen_grafico['Total'].sum() > 0:
            fig_donut = px.pie(
                resumen_grafico, values='Total', names='Partida', hole=0.45, title="Distribución de Costos por Sistema"
            )
            fig_donut.update_traces(textposition='outside', textinfo='percent+label', textfont=dict(size=14, color='black'))
            fig_donut.update_layout(legend=dict(font=dict(size=16), orientation="h", yanchor="bottom", y=-0.5), margin=dict(t=40, b=40, l=40, r=40))

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
                
                # --- NUEVA TARJETA DE ENCABEZADO (CLIENTE + VENDEDOR) ---
                y_rect = pdf.get_y()
                pdf.set_fill_color(245, 248, 245) 
                pdf.rect(10, y_rect, 190, 26, 'F')
                pdf.set_fill_color(46, 125, 50) 
                pdf.rect(10, y_rect, 2, 26, 'F')
                
                # Columna Izquierda: CLIENTE
                pdf.set_xy(15, y_rect + 4)
                pdf.set_font('Arial', 'B', 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(90, 4, "DATOS DEL CLIENTE", 0, 0)
                
                # Columna Derecha: VENDEDOR
                pdf.set_xy(110, y_rect + 4)
                pdf.cell(90, 4, "ATENDIDO POR", 0, 1)
                
                pdf.set_text_color(0, 0, 0)
                
                # Fila 1
                pdf.set_x(15)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(95, 5, limpiar_texto(cliente_nombre), 0, 0) 
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(vendedor_nombre), 0, 1)
                
                # Fila 2
                pdf.set_x(15)
                pdf.set_font('Arial', '', 9)
                pdf.cell(95, 5, limpiar_texto(f"RUC: {cliente_ruc}"), 0, 0)
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(f"Celular: {vendedor_celular}"), 0, 1)
                
                # Fila 3
                pdf.set_x(15)
                pdf.cell(95, 5, limpiar_texto(f"Lugar: {cliente_lugar}"), 0, 0)
                pdf.set_x(110)
                pdf.cell(90, 5, limpiar_texto(f"Correo: {vendedor_correo}"), 0, 1)
                
                pdf.ln(6) 
                
                # --- RESUMEN EJECUTIVO (INICIO) ---
                pdf.section_title(f"Resumen: {proyecto_nombre}")
                
                # ¡AQUÍ ESTÁ LA CORRECCIÓN CLAVE! 
                resumen = st.session_state.df_master.groupby('Partida')[['Total']].sum().reset_index()
                resumen.insert(0, 'N°', range(1, len(resumen) + 1)) 
                
                # Cabecera Resumen
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(235, 235, 235)
                pdf.set_text_color(50, 50, 50)
                pdf.set_draw_color(255, 255, 255)
                
                pdf.cell(10, 7, 'N°', 1, 0, 'C', 1)
                pdf.cell(130, 7, 'Sistema / Partida', 1, 0, 'L', 1)
                pdf.cell(50, 7, 'Monto ($)', 1, 1, 'R', 1)
                
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(0, 0, 0)
                fill_resumen = False
                for i, row in resumen.iterrows():
                    pdf.set_fill_color(248, 250, 248) if fill_resumen else pdf.set_fill_color(255, 255, 255)
                    pdf.cell(10, 6, str(row['N°']), 0, 0, 'C', fill_resumen)
                    pdf.cell(130, 6, limpiar_texto(row['Partida']), 0, 0, 'L', fill_resumen)
                    pdf.cell(50, 6, f"$ {row['Total']:,.2f}", 0, 1, 'R', fill_resumen)
                    fill_resumen = not fill_resumen
                
                pdf.ln(5)

                # --- DETALLES DE CADA SISTEMA (ORDENADOS POR PRECIO) ---
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

                # --- SECCIÓN FINAL: REPETIR RESUMEN FINANCIERO Y MOSTRAR DONUT ---
                pdf.add_page() 
                
                pdf.section_title("Resumen Financiero y Distribucion")
                
                # Bloque Financiero Final
                pdf.set_font('Arial', '', 11)
                pdf.cell(140, 7, 'TOTAL NETO (SIN IGV):', 0, 0, 'R')
                pdf.cell(50, 7, f"$ {total_neto:,.2f}", 0, 1, 'R')
                
                pdf.cell(140, 7, 'IGV (18%):', 0, 0, 'R')
                pdf.cell(50, 7, f"$ {igv:,.2f}", 0, 1, 'R')
                
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(46, 125, 50) 
                pdf.cell(140, 10, 'VALOR VENTA TOTAL:', 0, 0, 'R')
                pdf.cell(50, 10, f"$ {total_venta:,.2f}", 0, 1, 'R')
                
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(211, 47, 47) 
                pdf.cell(140, 7, f'COSTO POR HECTAREA ({area_ha} Ha):', 0, 0, 'R')
                pdf.cell(50, 7, f"$ {precio_ha:,.2f}", 0, 1, 'R')
                
                pdf.set_text_color(0, 0, 0)
                pdf.ln(10)
                
                # Insertar Gráfico Donut
                if fig_donut:
                    try:
                        fig_pdf = px.pie(resumen_grafico, values='Total', names='Partida', hole=0.45)
                        fig_pdf.update_traces(textposition='outside', textinfo='percent+label', textfont=dict(size=18, color='black'))
                        fig_pdf.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                            fig_pdf.write_image(tmp_img.name, width=800, height=500)
                        
                        pdf.image(tmp_img.name, x=25, y=pdf.get_y(), w=160)
                        os.unlink(tmp_img.name)
                    except Exception as e:
                        pdf.set_font('Arial', 'I', 9)
                        pdf.cell(0, 10, "* Nota: Para visualizar el grafico aqui, instala la libreria 'kaleido' en tu entorno/servidor.", 0, 1, 'C')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_final:
                    pdf.output(tmp_final.name)
                    with open(tmp_final.name, "rb") as f:
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
                if fig_donut:
                    st.plotly_chart(fig_donut, use_container_width=True)
                else:
                    st.info("Aún no hay costos asignados para generar el gráfico.")

    except Exception as e:
        st.error(f"⚠️ Error de datos: Revisa que los archivos sean correctos. Detalle: {e}")
        st.write("Presiona F5 para limpiar la memoria si persiste el error.")
else:
    st.info("👋 Sube tus archivos Excel en el panel lateral para comenzar.")