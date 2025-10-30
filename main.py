import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- Configuração da Página e Tema ---
st.set_page_config(layout="wide", page_title="Dashboard Instagram", page_icon="📊")

# Cores base (Python)
COLOR_NAVY = "#0a192f"      # Azul Marinho Profissional
COLOR_LIGHT_GRAY = "#EAEAEA" # Cinza Claro (Texto)
COLOR_GRID = "#444444"      # Cinza (Grades do gráfico)
COLOR_ORANGE = "#FFA500"    # Laranja Profissional (para títulos)

# Paleta para os gráficos (CSS/Hex)
COLOR_POSITIVE = "#90EE90"  # Verde Suave
COLOR_NEGATIVE = "#F08080"  # Vermelho Suave
COLOR_NEUTRAL = "#ADD8E6"   # Azul Claro (Neutro)
COLOR_PURPLE = "#8A2BE2"    # Roxo

# --- Injeção de CSS para o Tema da Página (COM CORREÇÃO DO MODAL E LARGURA DOS FILTROS) ---
st.markdown(f"""
<style>
    /* 1. Define as variáveis de tema globais do Streamlit */
    :root {{
        --background-color: {COLOR_NAVY};
        --secondary-background-color: {COLOR_NAVY}; /* Chave para o Fundo do Modal */
        --text-color: {COLOR_LIGHT_GRAY};
        --font: "sans serif"; /* Garante consistência */
    }}
    
    /* 2. Garante que o corpo E O .stApp usem essas variáveis */
    body, .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    
    /* 3. Customizações Específicas */
    
    /* Cor dos títulos (Laranja) */
    .stApp h1, .stApp h2, .stApp h3 {{
        color: {COLOR_ORANGE}; 
    }}
    
    /* Garante que o Header (barra superior) também pegue a cor */
    [data-testid="stHeader"] {{
        background: var(--background-color);
    }}

    /* Garante que o texto dos gráficos (títulos, eixos) fique claro */
    .stApp .stAltairChart {{
        background-color: transparent;
    }}
    
    /* Garante que o texto no modal também fique claro */
    [data-testid="stModal"] h3 {{
        color: var(--text-color);
    }}

    /* --- AJUSTE NA LARGURA DOS FILTROS --- */
    /* Aponta para o contêiner principal dos seletores */
    div[data-testid="stSelectbox"],
    div[data-testid="stMultiSelect"] {{
        max-width: 250px; /* Define uma largura máxima */
        width: 100%; /* Permite que ele se ajuste até a max-width */
    }}
    
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label {{
        font-size: 0.9rem !important;
        margin-bottom: 5px !important; /* Ajusta o espaçamento abaixo da label */
    }}
    
    [data-testid="stSelectbox"] div[data-baseweb="select"],
    [data-testid="stMultiSelect"] div[data-baseweb="base-input"] {{
        min-height: unset !important;
        height: unset !important;
        font-size: 0.9rem !important;
    }}
    
</style>
""", unsafe_allow_html=True)


# --- Tema Customizado do Altair (Corrigido) ---
@alt.theme.register("custom_dark_theme", enable=True)
def custom_dark_theme():
    return alt.theme.ThemeConfig(
        config={ 
            "background": "transparent",
            "title": {"color": COLOR_LIGHT_GRAY, "fontSize": 18},
            "style": {
                "guide-label": {"fill": COLOR_LIGHT_GRAY, "fontSize": 12},
                "guide-title": {"fill": COLOR_LIGHT_GRAY, "fontSize": 14}
            },
            "axis": {
                "domainColor": COLOR_LIGHT_GRAY,
                "gridColor": COLOR_GRID,
                "tickColor": COLOR_LIGHT_GRAY,
            },
            "legend": {
                "labelColor": COLOR_LIGHT_GRAY,
                "titleColor": COLOR_LIGHT_GRAY
            }
        }
    )


# --- Funções de Carregamento de Dados (com Cache) ---
@st.cache_data
def load_data(file_path):
    """Carrega um arquivo CSV com tratamento de erro."""
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        return None 
    except Exception as e:
        st.error(f"Erro inesperado ao carregar '{file_path}': {e}")
        return None

# --- Função de Parsing de Mês (Corrigida) ---
def parse_mes_string(mes_str):
    """Converte 'Mês por extenso [de] AAAA' (ex: 'junho 2024' ou 'junho de 2024') para um objeto datetime."""
    mes_map = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04', 
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08', 
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    try:
        mes_str_clean = str(mes_str).lower().strip().replace(' de ', ' ')
        partes = mes_str_clean.split(' ')
        if len(partes) == 2:
            mes_nome, ano = partes
            mes_num = mes_map.get(mes_nome)
            if mes_num:
                return pd.to_datetime(f'01-{mes_num}-{ano}', format='%d-%m-%Y')
    except Exception as e:
        print(f"Erro ao converter '{mes_str}': {e}") 
        pass
    return pd.NaT 


def main():
    st.title("📊 Dashboard de Performance - Instagram")

    # --- Carregar os Dados ---
    df_ent_sai = load_data('EntSaiSeg.csv')
    df_eng = load_data('EngXEnt.csv')
    df_total_int = load_data('TotalInteracoes.csv')
    
    # --- PREPARAÇÃO DE DADOS (Gráficos 3 e 4) ---
    eng_cols = ['Curt_Pub', 'Com_Pub', 'Sal_Pub', 'Comp_Pub', 
                'Curt_Reels', 'Com_Reels', 'Sal_Reels', 'Comp_Reels', 
                'Resp_Sto', 'Comp_Sto']
    metric_cols = ['entrada_seguidores'] + eng_cols

    if df_eng is not None:
        try:
            num_rows = len(df_eng)
            date_range = pd.date_range(start='2024-06-01', periods=num_rows, freq='MS')
            df_eng['mes_dt'] = date_range
            df_eng['mes_str'] = df_eng['mes_dt'].dt.strftime('%B de %Y').str.capitalize()
            for col in metric_cols:
                if col not in df_eng.columns:
                    df_eng[col] = 0
        except Exception as e:
            st.error(f"Erro ao preparar datas do arquivo 'EngXEnt.csv': {e}")
            df_eng = None

    
    st.header("Análise de Crescimento e Interações")

    filt_col1, filt_col2 = st.columns(2)
    with filt_col1:
        # Prepara opções do filtro (mesmo se o DF falhar, para evitar erros)
        opcoes_mes = ['Visão Geral (Mensal)']
        
        if df_ent_sai is not None:
            try:
                # Converter datas ANTES de criar o filtro
                df_ent_sai['data'] = pd.to_datetime(df_ent_sai['data'], errors='coerce')
                df_ent_sai = df_ent_sai.dropna(subset=['data'])
                if not df_ent_sai.empty:
                    df_mensal = df_ent_sai.set_index('data').resample('MS').sum(numeric_only=True).reset_index()
                    df_mensal = df_mensal.rename(columns={'data': 'mes_dt'})
                    df_mensal['mes_str'] = df_mensal['mes_dt'].dt.strftime('%B de %Y').str.capitalize()
                    opcoes_mes.extend(df_mensal['mes_str'].tolist())
                else:
                    st.warning("Gráfico 1: O arquivo 'EntSaiSeg.csv' está vazio ou não contém datas válidas.")
            except Exception as e:
                st.error(f"Erro ao preparar filtro do Gráfico 1: {e}")
                df_ent_sai = None # Invalida se a preparação falhar

        # CRIAR O FILTRO (SELECTBOX)
        mes_selecionado = st.selectbox("Filtrar por mês:", opcoes_mes)
    
    with filt_col2:
        pass # Coluna 2 da linha de filtros fica vazia

    chart_col1, chart_col2 = st.columns(2)
    
    # --- Gráfico 1: Linha de entrada de seguidores ---
    with chart_col1:
        if df_ent_sai is None:
            st.error("Arquivo 'EntSaiSeg.csv' não encontrado. Gráfico 1 não pode ser gerado.")
        else:
            try:
                # LÓGICA DO FILTRO
                if mes_selecionado == 'Visão Geral (Mensal)':
                    # PLOTAR O GRÁFICO MENSAL
                    chart1 = alt.Chart(df_mensal).mark_line(point=True, color=COLOR_NEUTRAL).encode(
                        x=alt.X('mes_dt:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                        y=alt.Y('entrada_seguidor:Q', axis=alt.Axis(title='Novos Seguidores')),
                        tooltip=[alt.Tooltip('mes_dt:T', title='Mês', format='%b/%Y'), 'entrada_seguidor:Q']
                    ).properties(
                        title='Entrada de Novos Seguidores (Mensal)'
                    ).interactive()
                
                else:
                    # PLOTAR O GRÁFICO DIÁRIO (FILTRADO)
                    mes_dt_selecionado = df_mensal[df_mensal['mes_str'] == mes_selecionado]['mes_dt'].iloc[0]
                    inicio_mes = mes_dt_selecionado
                    fim_mes = inicio_mes + pd.offsets.MonthEnd(0)
                    
                    df_diario_filtrado = df_ent_sai[
                        (df_ent_sai['data'] >= inicio_mes) & (df_ent_sai['data'] <= fim_mes)
                    ]
                    
                    chart1 = alt.Chart(df_diario_filtrado).mark_area(point=True, color=COLOR_NEUTRAL).encode(
                        x=alt.X('data:T', axis=alt.Axis(title='Dia', format='%Y-%m-%d')),
                        y=alt.Y('entrada_seguidor:Q', axis=alt.Axis(title='Novos Seguidores')),
                        tooltip=['data:T', 'entrada_seguidor:Q']
                    ).properties(
                        title=f'Entrada Diária de Seguidores ({mes_selecionado})'
                    ).interactive()

                # Exibir o gráfico (seja ele o mensal ou o diário)
                st.altair_chart(chart1, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 1 (Altair): {e}")

    # --- Gráfico 2: Linha de interações ---
    with chart_col2:
        if df_total_int is None:
            st.error("Arquivo 'TotalInteracoes.csv' não encontrado. Gráfico 2 não pode ser gerado.")
        else:
            try:
                if df_total_int.empty:
                    st.warning("Gráfico 2: O arquivo 'TotalInteracoes.csv' está vazio.")
                else:
                    # 1. Aplicar a função 'parse_mes_string'
                    df_total_int['mes_dt'] = df_total_int['mes'].apply(parse_mes_string)
                    df_total_int = df_total_int.dropna(subset=['mes_dt']) 

                    if df_total_int.empty:
                        st.error("Gráfico 2: Falha ao converter a coluna 'mes' para data. Verifique o formato.")
                    else:
                        # 2. Plotar APENAS A LINHA
                        chart2 = alt.Chart(df_total_int).mark_line(point=True, color=COLOR_NEUTRAL).encode(
                            x=alt.X('mes_dt:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                            y=alt.Y('total_interacoes:Q', axis=alt.Axis(title='Total de Interações')),
                            tooltip=[alt.Tooltip('mes:N', title='Mês'), 'total_interacoes:Q']
                        ).properties(
                            title='Total de Interações por Mês'
                        ).interactive()
                        
                        st.altair_chart(chart2, use_container_width=True)
                        
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 2 (Altair): {e}")

    st.header("Análise Detalhada de Engajamento")
    
    filt_col3, filt_col4 = st.columns(2)
    
    with filt_col3:
        # Prepara opções do filtro 3
        opcoes_mes_eng = ['Visão Geral (Total)']
        if df_eng is not None:
            opcoes_mes_eng.extend(df_eng['mes_str'].tolist())
            
        mes_selecionado_eng = st.selectbox(
            "Filtrar Engajamento por mês:", 
            opcoes_mes_eng, 
            key='eng_filter' # Chave única
        )

    with filt_col4:
        # Prepara opções do filtro 4
        metric_options_existentes = []
        if df_eng is not None:
            metric_options_existentes = [col for col in metric_cols if col in df_eng.columns]
        
        selected_metrics = st.multiselect(
            "Selecione as métricas para comparar:",
            options=metric_options_existentes,
            default=['entrada_seguidores', 'Comp_Reels'] # Mantém o padrão
        )

    chart_col3, chart_col4 = st.columns(2)

    # --- Gráfico 3: Barras (Altair) COM FILTRO ---
    with chart_col3:
        if df_eng is None:
            st.error("Arquivo 'EngXEnt.csv' não encontrado. Gráficos 3 e 4 não podem ser gerados.")
        else:
            try:
                cols_existentes = [col for col in eng_cols if col in df_eng.columns]
                
                if not cols_existentes:
                    st.warning("Gráfico 3: Nenhuma coluna de engajamento encontrada em 'EngXEnt.csv'.")
                else:
                    # LÓGICA DO FILTRO (já temos o 'mes_selecionado_eng' da linha de cima)
                    if mes_selecionado_eng == 'Visão Geral (Total)':
                        df_para_plotar = df_eng[cols_existentes].sum().reset_index()
                        plot_title = 'Total de Engajamento por Tipo (Período Completo)'
                    else:
                        df_filtrado_eng = df_eng[df_eng['mes_str'] == mes_selecionado_eng]
                        df_para_plotar = df_filtrado_eng[cols_existentes].T.reset_index()
                        plot_title = f'Total de Engajamento por Tipo ({mes_selecionado_eng})'
                    
                    df_para_plotar.columns = ['Tipo de Engajamento', 'Total'] # Renomear colunas
                    
                    # Mapeamento de cores
                    color_domain = []
                    color_range = []
                    for col in df_para_plotar['Tipo de Engajamento']:
                        color_domain.append(col)
                        if 'Reels' in col: color_range.append(COLOR_POSITIVE)
                        elif 'Pub' in col: color_range.append(COLOR_NEUTRAL)
                        elif 'Sto' in col: color_range.append(COLOR_PURPLE)
                        else: color_range.append(COLOR_GRID)

                    # PLOTAR
                    chart3 = alt.Chart(df_para_plotar).mark_bar().encode(
                        x=alt.X('Tipo de Engajamento:N', sort=None),
                        y=alt.Y('Total:Q'),
                        color=alt.Color('Tipo de Engajamento:N', 
                                        scale=alt.Scale(domain=color_domain, range=color_range),
                                        legend=None),
                        tooltip=['Tipo de Engajamento:N', 'Total:Q']
                    ).properties(
                        title=plot_title # Usar título dinâmico
                    )
                    st.altair_chart(chart3, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 3 (Altair): {e}")

    # --- Gráfico 4: Linha (Altair) COM FILTRO ---
    with chart_col4:
        if df_eng is None:
            pass # Erro já reportado no Gráfico 3
        else:
            try:
                if not selected_metrics:
                    st.warning("Gráfico 4: Selecione pelo menos uma métrica para exibir.")
                else:
                    # PREPARAR DADOS (já temos o 'selected_metrics' da linha de cima)
                    cols_to_plot = ['mes_dt'] + selected_metrics
                    df_plot_4_data = df_eng[cols_to_plot].copy()
                    df_plot_4_data = df_plot_4_data.rename(columns={'mes_dt': 'Mês'})
                    
                    df_melted = df_plot_4_data.melt('Mês', var_name='Métrica', value_name='Valor')
                    
                    # PLOTAR
                    chart4 = alt.Chart(df_melted).mark_line(point=True).encode(
                        x=alt.X('Mês:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                        y=alt.Y('Valor:Q', axis=alt.Axis(title='Contagem')),
                        color=alt.Color('Métrica:N'), 
                        tooltip=['Mês:T', 'Métrica:N', 'Valor:Q']
                    ).properties(
                        title='Comparação de Métricas (Mensal)'
                    ).interactive()
                    
                    st.altair_chart(chart4, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 4 (Altair): {e}")

if __name__ == "__main__":
    main()
