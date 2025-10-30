import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- Configuração da Página e Tema ---
st.set_page_config(layout="wide", page_title="Dashboard Instagram", page_icon='📊')

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

# --- Injeção de CSS para o Tema da Página (COM CORREÇÃO DO MODAL) ---
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
    
    st.header("Análise de Crescimento e Interações")
    col1, col2 = st.columns(2)

    # --- Gráfico 1: Linha de entrada de seguidores (COM FILTRO) ---
    with col1:
        if df_ent_sai is None:
            st.error("Arquivo 'EntSaiSeg.csv' não encontrado. Gráfico 1 não pode ser gerado.")
        else:
            try:
                # 1. Converter coluna 'data'
                df_ent_sai['data'] = pd.to_datetime(df_ent_sai['data'], errors='coerce')
                df_ent_sai = df_ent_sai.dropna(subset=['data'])
                
                if df_ent_sai.empty:
                    st.warning("Gráfico 1: O arquivo 'EntSaiSeg.csv' está vazio ou não contém datas válidas.")
                else:
                    # 2. AGRUPAR POR MÊS (para o selectbox e visão geral)
                    df_mensal = df_ent_sai.set_index('data').resample('MS').sum(numeric_only=True).reset_index()
                    df_mensal = df_mensal.rename(columns={'data': 'mes_dt'})
                    df_mensal['mes_str'] = df_mensal['mes_dt'].dt.strftime('%B de %Y').str.capitalize() # ex: 'Junho de 2024'

                    # 3. CRIAR O FILTRO (SELECTBOX)
                    # Criar a lista de opções, começando com a visão geral
                    opcoes_mes = ['Visão Geral (Mensal)'] + df_mensal['mes_str'].tolist()
                    mes_selecionado = st.selectbox("Filtrar por mês:", opcoes_mes)

                    # 4. LÓGICA DO FILTRO
                    if mes_selecionado == 'Visão Geral (Mensal)':
                        # PLOTAR O GRÁFICO MENSAL (o que já tínhamos)
                        chart1 = alt.Chart(df_mensal).mark_line(point=True, color=COLOR_NEUTRAL).encode(
                            x=alt.X('mes_dt:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                            y=alt.Y('entrada_seguidor:Q', axis=alt.Axis(title='Novos Seguidores')),
                            tooltip=[alt.Tooltip('mes_dt:T', title='Mês', format='%b/%Y'), 'entrada_seguidor:Q']
                        ).properties(
                            title='Entrada de Novos Seguidores (Mensal)'
                        ).interactive()
                    
                    else:
                        # PLOTAR O GRÁFICO DIÁRIO (FILTRADO)
                        
                        # Achar a data de início do mês selecionado
                        mes_dt_selecionado = df_mensal[df_mensal['mes_str'] == mes_selecionado]['mes_dt'].iloc[0]
                        
                        # Calcular o início e fim desse mês
                        inicio_mes = mes_dt_selecionado
                        fim_mes = inicio_mes + pd.offsets.MonthEnd(0)
                        
                        # Filtrar o DataFrame DIÁRIO original
                        df_diario_filtrado = df_ent_sai[
                            (df_ent_sai['data'] >= inicio_mes) & (df_ent_sai['data'] <= fim_mes)
                        ]
                        
                        # Criar o gráfico diário
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

    # --- Gráfico 2: Linha de interações (SEM DESTAQUES) ---
    with col2:
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
    col3, col4 = st.columns(2)

    # --- Gráfico 3: Barras (Altair) ---
    with col3:
        if df_eng is None:
            st.error("Arquivo 'EngXEnt.csv' não encontrado. Gráficos 3 e 4 não podem ser gerados.")
        else:
            try:
                eng_cols = ['Curt_Pub', 'Com_Pub', 'Sal_Pub', 'Comp_Pub', 
                            'Curt_Reels', 'Com_Reels', 'Sal_Reels', 'Comp_Reels', 
                            'Resp_Sto', 'Comp_Sto']
                cols_existentes = [col for col in eng_cols if col in df_eng.columns]
                if not cols_existentes:
                    st.warning("Gráfico 3: Nenhuma coluna de engajamento encontrada em 'EngXEnt.csv'.")
                else:
                    df_eng_totals = df_eng[cols_existentes].sum().reset_index()
                    df_eng_totals.columns = ['Tipo de Engajamento', 'Total']
                    color_domain = []
                    color_range = []
                    for col in df_eng_totals['Tipo de Engajamento']:
                        color_domain.append(col)
                        if 'Reels' in col: color_range.append(COLOR_POSITIVE)
                        elif 'Pub' in col: color_range.append(COLOR_NEUTRAL)
                        elif 'Sto' in col: color_range.append(COLOR_PURPLE)
                        else: color_range.append(COLOR_GRID)
                    chart3 = alt.Chart(df_eng_totals).mark_bar().encode(
                        x=alt.X('Tipo de Engajamento:N', sort=None),
                        y=alt.Y('Total:Q'),
                        color=alt.Color('Tipo de Engajamento:N', 
                                        scale=alt.Scale(domain=color_domain, range=color_range),
                                        legend=None),
                        tooltip=['Tipo de Engajamento:N', 'Total:Q']
                    ).properties(
                        title='Total de Engajamento por Tipo'
                    )
                    st.altair_chart(chart3, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 3 (Altair): {e}")

    # --- Gráfico 4: Linha (Altair) ---
    with col4:
        if df_eng is None:
            pass 
        else:
            try:
                if 'entrada_seguidores' not in df_eng.columns or 'Comp_Reels' not in df_eng.columns:
                    st.warning("Gráfico 4: Colunas 'entrada_seguidores' ou 'Comp_Reels' não encontradas.")
                elif df_eng.empty:
                    st.warning("Gráfico 4: O arquivo 'EngXEnt.csv' está vazio.")
                else:
                    num_rows = len(df_eng)
                    date_range = pd.date_range(start='2024-06-01', periods=num_rows, freq='MS')
                    df_plot_4 = df_eng[['entrada_seguidores', 'Comp_Reels']].copy()
                    df_plot_4['Mês'] = date_range
                    df_melted = df_plot_4.melt('Mês', var_name='Métrica', value_name='Valor')
                    chart4 = alt.Chart(df_melted).mark_line(point=True).encode(
                        x=alt.X('Mês:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                        y=alt.Y('Valor:Q', axis=alt.Axis(title='Contagem')),
                        color=alt.Color('Métrica:N', 
                                        scale=alt.Scale(domain=['entrada_seguidores', 'Comp_Reels'],
                                                        range=[COLOR_POSITIVE, COLOR_NEUTRAL])),
                        tooltip=['Mês:T', 'Métrica:N', 'Valor:Q']
                    ).properties(
                        title='Seguidores vs. Comp. Reels (Mensal)'
                    ).interactive()
                    
                    st.altair_chart(chart4, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 4 (Altair): {e}")

if __name__ == "__main__":
    main()
