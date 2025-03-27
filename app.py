import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# ==============================
# CONFIGURAÇÕES INICIAIS E CSS
# ==============================
st.set_page_config(
    page_title="Northwind Traders | Dashboard Moderno",
    layout="wide"
)

# CSS customizado para um layout moderno e para os cards de KPI
st.markdown(
    """
    <style>
    /* Estilo Global */
    body, .stApp {
        background-color: #F7F9F9;
        color: #2C3E50;
        font-family: "Segoe UI", sans-serif;
    }
    /* Títulos */
    h1, h2, h3, h4, h5, h6, .css-10trblm {
        color: #2C3E50 !important;
        font-weight: 700;
    }
    /* Cards de KPI customizados */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        padding: 10px;
        border-radius: 8px;
        margin: 5px;
    }
    /* Botões */
    .stButton>button {
        background: linear-gradient(45deg, #2C3E50, #4CA1AF);
        color: #FFFFFF;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Northwind Traders | Dashboard Moderno")

# ==============================
# UPLOAD & FILTROS GLOBAIS (na home page)
# ==============================
with st.container():
    st.markdown("## Upload & Filtros Globais")
    uploaded_file = st.file_uploader("Carregue seu arquivo .xlsx", type=["xlsx"])
    
# Função para carregar e processar os dados
@st.cache_data(show_spinner=False)
def load_and_process_data(uploaded_file):
    df_raw = pd.read_excel(uploaded_file)
    # Remover colunas redundantes (com "-2" no nome)
    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('-2')]
    
    # Converter colunas de data (se existirem)
    for col in ["order_date", "required_date", "shipped_date"]:
        if col in df_raw.columns:
            df_raw[col] = pd.to_datetime(df_raw[col], errors="coerce")
    
    # Calcular receita: unit_price * quantity * (1 - discount)
    if all(col in df_raw.columns for col in ["unit_price", "quantity", "discount"]):
        df_raw["revenue"] = df_raw["unit_price"] * df_raw["quantity"] * (1 - df_raw["discount"])
    else:
        df_raw["revenue"] = 0
    
    # Selecionar as colunas essenciais (incluindo "revenue")
    cols_essenciais = [
        "order_id", "customer_id", "order_date", "required_date", "shipped_date",
        "freight", "ship_country", "product_id", "product_name", "unit_price",
        "quantity", "discount", "company_name", "category_name", "revenue"
    ]
    df = df_raw[[c for c in cols_essenciais if c in df_raw.columns]].copy()
    return df

# Se houver arquivo carregado, processa os dados e define o filtro de período
if uploaded_file:
    df_raw = load_and_process_data(uploaded_file)
    if "order_date" in df_raw.columns:
        min_date = df_raw["order_date"].min().date()
        max_date = df_raw["order_date"].max().date()
        # Filtro de período – indicação do formato brasileiro (dd/mm/aaaa)
        st.markdown("### Selecione o Período de Análise (dd/mm/aaaa)")
        start_date, end_date = st.date_input("Período de Análise", [min_date, max_date])
        if isinstance(start_date, list):
            start_date, end_date = start_date
        # Função para filtrar por período
        def filtrar_periodo(df, data_col, start, end):
            mask = (df[data_col] >= pd.to_datetime(start)) & (df[data_col] <= pd.to_datetime(end))
            return df[mask]
        df = filtrar_periodo(df_raw, "order_date", start_date, end_date)
        # Definir período anterior para comparação – se aplicável
        delta_days = (end_date - start_date).days + 1
        prev_end_date = pd.to_datetime(start_date) - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=delta_days - 1)
        df_previous = filtrar_periodo(df_raw, "order_date", prev_start_date, prev_end_date)
    else:
        df = df_raw.copy()
        df_previous = pd.DataFrame(columns=df.columns)
else:
    st.info("Por favor, carregue um arquivo .xlsx para iniciar a análise.")

# ==============================
# FUNÇÕES AUXILIARES
# ==============================
def calcular_delta(novo_valor, antigo_valor):
    # Se o valor anterior for zero ou inválido, retorna 0 (para evitar N/A)
    if antigo_valor == 0 or pd.isnull(antigo_valor):
        return 0
    return (novo_valor - antigo_valor) / antigo_valor * 100

def get_time_group(df, group_by):
    df_temp = df.copy()
    if group_by == "Dia":
        df_temp["periodo"] = df_temp["order_date"].dt.date
    elif group_by == "Mês":
        df_temp["periodo"] = df_temp["order_date"].dt.to_period("M").astype(str)
    else:
        df_temp["periodo"] = df_temp["order_date"].dt.year.astype(str)
    return df_temp

def format_currency(val):
    return f"R$ {val:,.2f}"

# ==============================
# SEÇÃO: DASHBOARD GERAL
# ==============================
def render_dashboard(df, df_previous):
    st.header("Dashboard Geral")
    # KPIs
    total_revenue = df["revenue"].sum()
    previous_revenue = df_previous["revenue"].sum() if not df_previous.empty else 0
    delta_revenue = calcular_delta(total_revenue, previous_revenue)
    
    total_orders = df["order_id"].nunique() if "order_id" in df.columns else 0
    previous_orders = df_previous["order_id"].nunique() if "order_id" in df_previous.columns else 0
    delta_orders = calcular_delta(total_orders, previous_orders)
    
    total_freight = df["freight"].sum() if "freight" in df.columns else 0
    total_quantity = df["quantity"].sum() if "quantity" in df.columns else 0
    total_customers = df["company_name"].nunique() if "company_name" in df.columns else 0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    avg_discount = df["discount"].mean() * 100 if "discount" in df.columns else 0
    if "order_date" in df.columns and "shipped_date" in df.columns:
        shipping_time = (df["shipped_date"] - df["order_date"]).dt.days
        avg_shipping_time = shipping_time.mean()
    else:
        avg_shipping_time = 0
    unique_products = df["product_id"].nunique() if "product_id" in df.columns else 0

    st.subheader("Principais Indicadores")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Receita Total", format_currency(total_revenue),
                        delta=f"{delta_revenue:.1f}%")
    kpi_cols[1].metric("Nº de Pedidos", f"{total_orders:,}",
                        delta=f"{delta_orders:.1f}%")
    kpi_cols[2].metric("Custo de Frete", format_currency(total_freight))
    kpi_cols[3].metric("Quantidade Vendida", f"{total_quantity:,}")
    kpi_cols[4].metric("Nº de Clientes", f"{total_customers:,}")
    
    kpi_cols2 = st.columns(4)
    kpi_cols2[0].metric("Ticket Médio", format_currency(avg_order_value))
    kpi_cols2[1].metric("Desconto Médio", f"{avg_discount:.1f}%")
    kpi_cols2[2].metric("Tempo Médio de Envio (dias)", f"{avg_shipping_time:.1f}")
    kpi_cols2[3].metric("Produtos Únicos", f"{unique_products:,}")
    
    st.markdown("---")
    st.markdown("### Tendência de Receita")
    group_by = st.selectbox("Agrupar por:", ("Dia", "Mês", "Ano"), index=1, key="dash_group")
    df_time = get_time_group(df, group_by)
    df_grouped = df_time.groupby("periodo").agg({"revenue": "sum"}).reset_index().sort_values("periodo")
    fig_area = px.area(df_grouped, x="periodo", y="revenue",
                       title="Evolução da Receita ao Longo do Tempo",
                       labels={"periodo": group_by, "revenue": "Receita (US$)"},
                       color_discrete_sequence=["#4CA1AF"])
    fig_area.update_traces(line=dict(width=3))
    st.plotly_chart(fig_area, use_container_width=True)

# ==============================
# SEÇÃO: ANÁLISES DE VENDAS
# ==============================
def render_vendas(df):
    st.header("Análises de Vendas")
    st.markdown("#### Evolução da Receita e Número de Pedidos")
    group_by = st.selectbox("Agrupar por:", ("Dia", "Mês", "Ano"), index=1, key="vendas_group")
    df_time = get_time_group(df, group_by)
    sales_by_time = df_time.groupby("periodo").agg({
        "revenue": "sum",
        "order_id": pd.Series.nunique
    }).reset_index().sort_values("periodo")
    fig_line = px.line(sales_by_time, x="periodo", y="revenue", markers=True,
                       title="Receita ao Longo do Tempo",
                       labels={"periodo": group_by, "revenue": "Receita (US$)"},
                       color_discrete_sequence=["#2C3E50"])
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("#### Top 10 Produtos por Receita")
    if "product_name" in df.columns:
        prod_sales = df.groupby("product_name")["revenue"].sum().reset_index()
        prod_sales = prod_sales.sort_values("revenue", ascending=False).head(10)
        fig_bar = px.bar(prod_sales, x="revenue", y="product_name", orientation="h",
                         title="Produtos com Maior Receita",
                         labels={"product_name": "Produto", "revenue": "Receita (US$)"},
                         color="revenue", color_continuous_scale=px.colors.sequential.Plasma)
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("#### Receita por Categoria")
    if "category_name" in df.columns:
        cat_sales = df.groupby("category_name")["revenue"].sum().reset_index()
        fig_pie = px.pie(cat_sales, names="category_name", values="revenue",
                         title="Distribuição de Receita por Categoria",
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

# ==============================
# SEÇÃO: ANÁLISES DE QUANTIDADE
# ==============================
def render_quantidade(df):
    st.header("Análises de Quantidade")
    st.markdown("#### Quantidade Vendida ao Longo do Tempo")
    group_by = st.selectbox("Agrupar por:", ("Dia", "Mês", "Ano"), index=1, key="qtd_group")
    df_time = get_time_group(df, group_by)
    qty_by_time = df_time.groupby("periodo").agg({"quantity": "sum"}).reset_index().sort_values("periodo")
    fig_area = px.area(qty_by_time, x="periodo", y="quantity",
                       title="Quantidade Vendida ao Longo do Tempo",
                       labels={"periodo": group_by, "quantity": "Quantidade"},
                       color_discrete_sequence=["#4CA1AF"])
    fig_area.update_traces(line=dict(width=3))
    st.plotly_chart(fig_area, use_container_width=True)
    
    st.markdown("#### Top 10 Destinos (Países) por Quantidade")
    if "ship_country" in df.columns:
        dest_qty = df.groupby("ship_country")["quantity"].sum().reset_index()
        dest_qty = dest_qty.sort_values("quantity", ascending=False).head(10)
        fig_bar = px.bar(dest_qty, x="quantity", y="ship_country", orientation="h",
                         title="Países com Maior Quantidade Vendida",
                         labels={"ship_country": "País", "quantity": "Quantidade"},
                         color="quantity", color_continuous_scale=px.colors.sequential.Viridis)
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("#### Distribuição da Quantidade por Pedido")
    fig_hist = px.histogram(df, x="quantity", nbins=20,
                            title="Histograma da Quantidade por Pedido",
                            labels={"quantity": "Quantidade"},
                            color_discrete_sequence=["#2C3E50"])
    st.plotly_chart(fig_hist, use_container_width=True)

# ==============================
# SEÇÃO: ANÁLISES DE CLIENTES
# ==============================
def render_clientes(df):
    st.header("Análises de Clientes")
    st.markdown("#### Top 10 Clientes por Receita")
    if "company_name" in df.columns:
        cust = df.groupby("company_name").agg({
            "order_id": "nunique",
            "revenue": "sum",
            "quantity": "sum"
        }).reset_index().rename(columns={"order_id": "n_pedidos"})
        cust = cust.sort_values("revenue", ascending=False).head(10)
        fig_bar = px.bar(cust, x="revenue", y="company_name", orientation="h",
                         title="Clientes com Maior Receita",
                         labels={"company_name": "Cliente", "revenue": "Receita (US$)"},
                         color="revenue", color_continuous_scale=px.colors.sequential.Teal)
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("#### Relação: Número de Pedidos x Receita")
        fig_scatter = px.scatter(cust, x="n_pedidos", y="revenue",
                                 size="quantity", hover_name="company_name",
                                 title="Pedidos vs. Receita por Cliente",
                                 labels={"n_pedidos": "Nº de Pedidos", "revenue": "Receita (US$)", "quantity": "Quantidade Total"},
                                 color="revenue", color_continuous_scale=px.colors.sequential.Cividis)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Coluna 'company_name' não encontrada.")

# ==============================
# SEÇÃO: ANÁLISE DE PRODUTOS
# ==============================
def render_produtos(df):
    st.header("Análise de Produtos")
    cols = st.columns(4)
    if "product_id" in df.columns:
        cols[0].metric("Total de Produtos", f"{df['product_id'].nunique():,}")
    if "quantity" in df.columns:
        avg_qty = df.groupby("product_id")["quantity"].sum().mean()
        cols[1].metric("Qtd Média por Produto", f"{avg_qty:.1f}")
    if "unit_price" in df.columns:
        cols[2].metric("Preço Médio", format_currency(df["unit_price"].mean()))
    if "category_name" in df.columns:
        cols[3].metric("Total de Categorias", f"{df['category_name'].nunique():,}")
    
    st.markdown("---")
    st.markdown("#### Top 10 Produtos por Receita")
    if "product_name" in df.columns:
        prod = df.groupby("product_name").agg({
            "revenue": "sum",
            "quantity": "sum"
        }).reset_index().sort_values("revenue", ascending=False).head(10)
        fig_bar = px.bar(prod, x="revenue", y="product_name", orientation="h",
                         title="Produtos com Maior Receita",
                         labels={"product_name": "Produto", "revenue": "Receita (US$)"},
                         color="revenue", color_continuous_scale=px.colors.sequential.Plasma)
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("#### Top 10 Produtos por Quantidade Vendida")
    if "product_name" in df.columns:
        prod_qty = df.groupby("product_name")["quantity"].sum().reset_index().sort_values("quantity", ascending=False).head(10)
        fig_bar_qty = px.bar(prod_qty, x="quantity", y="product_name", orientation="h",
                             title="Produtos com Maior Quantidade Vendida",
                             labels={"product_name": "Produto", "quantity": "Quantidade"},
                             color="quantity", color_continuous_scale=px.colors.sequential.Teal)
        fig_bar_qty.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar_qty, use_container_width=True)
    
    st.markdown("#### Análise de Preço e Desconto")
    col1, col2 = st.columns(2)
    if "unit_price" in df.columns:
        fig_price = px.histogram(df, x="unit_price", nbins=30,
                                 title="Distribuição de Preços Unitários",
                                 labels={"unit_price": "Preço Unitário (US$)"},
                                 color_discrete_sequence=["#3498DB"])
        col1.plotly_chart(fig_price, use_container_width=True)
    if "discount" in df.columns and df["discount"].gt(0).any():
        df_disc = df[df["discount"] > 0].copy()
        df_disc["discount_pct"] = df_disc["discount"] * 100
        fig_disc = px.scatter(df_disc, x="unit_price", y="discount_pct",
                              title="Preço vs. Desconto",
                              labels={"unit_price": "Preço Unitário (US$)", "discount_pct": "Desconto (%)"},
                              size="quantity", color="quantity",
                              color_continuous_scale="Blues", opacity=0.7)
        col2.plotly_chart(fig_disc, use_container_width=True)

# ==============================
# SEÇÃO: SEGMENTAÇÕES AVANÇADAS
# ==============================
def render_segmentacoes(df):
    st.header("Segmentações Avançadas")
    
    st.markdown("#### Mapa de Correlação entre Variáveis Numéricas")
    num_df = df.select_dtypes(include=np.number)
    if not num_df.empty:
        corr = num_df.corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto",
                             color_continuous_scale=px.colors.sequential.RdBu,
                             title="Correlação entre Variáveis Numéricas")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("Sem variáveis numéricas suficientes.")
    
    st.markdown("#### Scatter Matrix de Métricas Estratégicas")
    # Scatter Matrix para visualizar relações entre receita, frete, quantidade e desconto
    if not num_df.empty:
        fig_matrix = px.scatter_matrix(df,
                                       dimensions=["revenue", "freight", "quantity", "discount"],
                                       title="Matriz de Dispersão: Receita, Frete, Quantidade e Desconto",
                                       color="revenue",
                                       color_continuous_scale=px.colors.sequential.Viridis)
        st.plotly_chart(fig_matrix, use_container_width=True)
    
    st.markdown("#### Frete Médio por País")
    if "ship_country" in df.columns:
        freight_by_country = df.groupby("ship_country")["freight"].mean().reset_index()
        fig_bar_freight = px.bar(freight_by_country, x="ship_country", y="freight",
                                 title="Frete Médio por País",
                                 labels={"ship_country": "País", "freight": "Frete Médio (US$)"},
                                 color="freight", color_continuous_scale=px.colors.sequential.Plasma)
        st.plotly_chart(fig_bar_freight, use_container_width=True)
    
    st.markdown("#### Tempo de Envio Médio por Mês")
    if "order_date" in df.columns and "shipped_date" in df.columns:
        df_time = get_time_group(df, "Mês")
        df_time["shipping_time"] = (df_time["shipped_date"] - df_time["order_date"]).dt.days
        avg_shipping_by_period = df_time.groupby("periodo")["shipping_time"].mean().reset_index()
        fig_line_shipping = px.line(avg_shipping_by_period, x="periodo", y="shipping_time",
                                    title="Tempo de Envio Médio por Mês",
                                    labels={"periodo": "Mês", "shipping_time": "Dias Médios para Envio"},
                                    markers=True, color_discrete_sequence=["#2C3E50"])
        st.plotly_chart(fig_line_shipping, use_container_width=True)
    
    st.markdown("#### Bubble Chart: Receita, Desconto e Quantidade")
    fig_bubble = px.scatter(df, x="discount", y="revenue",
                            size="quantity", hover_name="product_name",
                            title="Relação entre Desconto, Receita e Quantidade",
                            labels={"discount": "Desconto", "revenue": "Receita (US$)", "quantity": "Quantidade"},
                            color="quantity", color_continuous_scale=px.colors.sequential.Inferno, opacity=0.7)
    st.plotly_chart(fig_bubble, use_container_width=True)

# ==============================
# ROTEIRO PRINCIPAL – EXIBIÇÃO DE TODAS AS SEÇÕES
# ==============================
if uploaded_file:
    render_dashboard(df, df_previous)
    st.markdown("##")
    render_vendas(df)
    st.markdown("##")
    render_quantidade(df)
    st.markdown("##")
    render_clientes(df)
    st.markdown("##")
    render_produtos(df)
    st.markdown("##")
    render_segmentacoes(df)
else:
    st.info("Carregue um arquivo .xlsx para iniciar a análise.")
