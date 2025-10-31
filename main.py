import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# --- Configuração da Página e Tema ---
# O tema agora é lido automaticamente do config.toml
st.set_page_config(layout="wide", page_title="Dashboard Instagram", page_icon="📊")

# Cores base (Python) - AINDA USADAS PELOS GRÁFICOS
COLOR_NAVY = "#0a192f"
COLOR_LIGHT_GRAY = "#EAEAEA" 
COLOR_GRID = "#444444"
COLOR_ORANGE = "#FFA500" 

# Paleta para os gráficos (CSS/Hex)
COLOR_POSITIVE = "#90EE90"
COLOR_NEGATIVE = "#F08080"
COLOR_NEUTRAL = "#ADD8E6"
COLOR_PURPLE = "#8A2BE2"

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
    # --- Carregar os Dados ---
    df_ent_sai = load_data('EntSaiSeg.csv')
    df_eng = load_data('EngXEnt.csv')
    df_total_int = load_data('TotalInteracoes.csv')
    
    # --- PREPARAÇÃO DE DADOS (Gráficos 3 e 4) ---
    eng_cols = ['Curt_Pub', 'Com_Pub', 'Sal_Pub', 'Comp_Pub', 
                'Curt_Reels', 'Com_Reels', 'Sal_Reels', 'Comp_Reels', 
                'Resp_Sto', 'Comp_Sto']

    if df_eng is not None:
        try:
            # Garante que colunas de engajamento existam
            for col in eng_cols + ['entrada_seguidores']:
                if col not in df_eng.columns:
                    df_eng[col] = 0

            num_rows = len(df_eng)
            date_range = pd.date_range(start='2024-06-01', periods=num_rows, freq='MS')
            df_eng['mes_dt'] = date_range
            df_eng['mes_str'] = df_eng['mes_dt'].dt.strftime('%B de %Y').str.capitalize()
            
            # CÁLCULO DE EFICIÊNCIA (IDEIA 3)
            df_eng['engajamento_total'] = df_eng[eng_cols].sum(axis=1)
            
            # Custo (Engajamentos) por Novo Seguidor (Menor é Melhor)
            df_eng['taxa_conversao_eng'] = np.where(
                df_eng['entrada_seguidores'] > 0, # Se ganhou seguidores
                df_eng['engajamento_total'] / df_eng['entrada_seguidores'], # Calcula o custo
                np.nan # Se não, marca como Nulo (para não plotar)
            )
            df_eng.replace([np.inf, -np.inf], np.nan, inplace=True) # Limpa infinitos

        except Exception as e:
            st.error(f"Erro ao preparar datas do arquivo 'EngXEnt.csv': {e}")
            df_eng = None

    # --- PREPARAÇÃO DE DADOS (Gráfico 1 e KPI 1) ---
    opcoes_mes_crescimento = ['Visão Geral (Mensal)']
    df_mensal = pd.DataFrame() # Inicializa df_mensal
    meses_crescimento = set()
    
    if df_ent_sai is not None:
        try:
            df_ent_sai['data'] = pd.to_datetime(df_ent_sai['data'], errors='coerce')
            df_ent_sai = df_ent_sai.dropna(subset=['data'])
            if not df_ent_sai.empty:
                # Agrupa por mês, incluindo 'saida_seguidor' para o KPI
                df_mensal = df_ent_sai.set_index('data').resample('MS').sum(numeric_only=True)[['entrada_seguidor', 'saida_seguidor']]
                df_mensal = df_mensal.reset_index().rename(columns={'data': 'mes_dt'})
                df_mensal['mes_str'] = df_mensal['mes_dt'].dt.strftime('%B de %Y').str.capitalize()
                opcoes_mes_crescimento.extend(df_mensal['mes_str'].tolist())
                meses_crescimento = set(df_mensal['mes_str'])
            else:
                st.warning("Gráfico 1: O arquivo 'EntSaiSeg.csv' está vazio ou não contém datas válidas.")
        except Exception as e:
            st.error(f"Erro ao preparar filtro do Gráfico 1: {e}")
            df_ent_sai = None

    # --- PREPARAÇÃO DE DADOS (Gráfico 2 e KPIs 2, 3) ---
    meses_interacoes = set()
    if df_total_int is not None:
        try:
            df_total_int['mes_dt'] = df_total_int['mes'].apply(parse_mes_string)
            df_total_int = df_total_int.dropna(subset=['mes_dt'])
            df_total_int['mes_str'] = df_total_int['mes_dt'].dt.strftime('%B de %Y').str.capitalize()
            meses_interacoes = set(df_total_int['mes_str'])
            if df_total_int.empty:
                st.error("Gráfico 2: Falha ao converter a coluna 'mes' para data. Verifique o formato.")
        except Exception:
            df_total_int = None # Invalida em caso de erro

    # --- INÍCIO DA SIDEBAR ---
    with st.sidebar:
        st.title("📊 Dashboard de Performance")
        
        st.sidebar.header("Filtros de Crescimento")
        # O filtro 1 usa 'opcoes_mes_crescimento' preparado acima
        mes_selecionado_grafico1 = st.selectbox("Filtrar por mês:", opcoes_mes_crescimento)
        
        st.sidebar.header("Filtros de Engajamento")
        
        # Prepara opções do filtro 3
        opcoes_mes_eng = ['Visão Geral (Total)']
        if df_eng is not None:
            opcoes_mes_eng.extend(df_eng['mes_str'].tolist())
            
        mes_selecionado_eng = st.selectbox(
            "Filtrar Engajamento por mês:", 
            opcoes_mes_eng, 
            key='eng_filter' # Chave única
        )
        
    # --- FIM DA SIDEBAR ---


    # --- INÍCIO DO LAYOUT PRINCIPAL DA PÁGINA ---
    
    # --- VISÃO EXECUTIVA (KPI CARDS) ---
    st.markdown(f"## :orange[Visão Executiva]")
    
    # --- CORREÇÃO DA ORDENAÇÃO DO FILTRO ---
    df_meses_1 = pd.DataFrame()
    if not df_mensal.empty:
        df_meses_1 = df_mensal[['mes_dt', 'mes_str']]
        
    df_meses_2 = pd.DataFrame()
    if df_total_int is not None and not df_total_int.empty:
        df_meses_2 = df_total_int[['mes_dt', 'mes_str']]

    df_meses_unificados = pd.concat([df_meses_1, df_meses_2]).drop_duplicates(subset=['mes_str'])
    df_meses_unificados = df_meses_unificados.sort_values(by='mes_dt')
    
    todos_os_meses_ordenados = df_meses_unificados['mes_str'].tolist()
    opcoes_kpi = ['Período Completo'] + todos_os_meses_ordenados
    
    kpi_mes_selecionado = st.selectbox("Filtrar KPIs por mês:", opcoes_kpi)

    kpi1, kpi2, kpi3 = st.columns(3)

    # --- Lógica de Filtro para KPIs ---
    
    # KPI 1: Saldo Líquido
    if df_mensal.empty:
        kpi1.metric("Saldo Líquido", "N/A", "Arquivo 'EntSaiSeg.csv' não encontrado")
    else:
        # 1. Seleciona o DataFrame (completo ou filtrado)
        if kpi_mes_selecionado == 'Período Completo':
            df_kpi_1 = df_mensal
        else:
            df_kpi_1 = df_mensal[df_mensal['mes_str'] == kpi_mes_selecionado]
        
        # 2. Verifica se o resultado tem dados
        if df_kpi_1.empty:
            kpi1.metric(f"Saldo Líquido ({kpi_mes_selecionado})", "N/A", "Sem dados para este mês")
        else:
            # 3. Calcula as métricas (funciona para 1 ou N linhas)
            total_ganho = df_kpi_1['entrada_seguidor'].sum()
            total_perdido = df_kpi_1['saida_seguidor'].sum()
            saldo_liquido = total_ganho - total_perdido
            
            # 4. CRIA O DELTA DINÂMICO
            delta_str = f"{total_ganho:,.0f} Ganhos vs {total_perdido:,.0f} Perdas"
            
            kpi1.metric(f"Saldo Líquido ({kpi_mes_selecionado})", f"{saldo_liquido:,.0f}", delta_str)

    # KPI 2 & 3: Interações
    if df_total_int is None or df_total_int.empty:
        kpi2.metric("Total de Interações", "N/A", "Arquivo 'TotalInteracoes.csv' não encontrado")
        kpi3.metric("Média de Interações", "N/A")
    else:
        # 1. Seleciona o DataFrame
        if kpi_mes_selecionado == 'Período Completo':
            df_kpi_2_3 = df_total_int
        else:
            df_kpi_2_3 = df_total_int[df_total_int['mes_str'] == kpi_mes_selecionado]
        
        # 2. Verifica se o resultado tem dados
        if df_kpi_2_3.empty:
            kpi2.metric(f"Total de Interações ({kpi_mes_selecionado})", "N/A", "Sem dados para este mês")
            kpi3.metric(f"Média de Interações ({kpi_mes_selecionado})", "N/A")
        else:
            # 3. Calcula as métricas (sum() e mean() funcionam para 1 ou N linhas)
            total_interacoes = df_kpi_2_3['total_interacoes'].sum()
            media_interacoes = df_kpi_2_3['total_interacoes'].mean()
            
            kpi2.metric(f"Total de Interações ({kpi_mes_selecionado})", f"{total_interacoes:,.0f}")
            kpi3.metric(f"Média de Interações ({kpi_mes_selecionado})", f"{media_interacoes:,.0f}")


    st.markdown("---") # Linha horizontal
    # --- ^ ^ ^ FIM DA VISÃO EXECUTIVA ^ ^ ^ ---


    st.markdown(f"## :orange[Análise de Crescimento e Interações]")
    col1, col2 = st.columns(2)

    # --- Gráfico 1: Linha de entrada de seguidores (COM FILTRO) ---
    with col1:
        if df_ent_sai is None:
            st.error("Arquivo 'EntSaiSeg.csv' não encontrado. Gráfico 1 não pode ser gerado.")
        elif df_mensal.empty and mes_selecionado_grafico1 == 'Visão Geral (Mensal)':
             st.warning("Gráfico 1: Não há dados mensais para exibir.")
        else:
            try:
                # LÓGICA DO FILTRO (baseada na variável 'mes_selecionado_grafico1' da sidebar)
                if mes_selecionado_grafico1 == 'Visão Geral (Mensal)':
                    # PLOTAR O GRÁFICO MENSAL (Sem destaques)
                    chart1 = alt.Chart(df_mensal).mark_line(point=True, color=COLOR_NEUTRAL).encode(
                        x=alt.X('mes_dt:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                        y=alt.Y('entrada_seguidor:Q', axis=alt.Axis(title='Novos Seguidores')),
                        tooltip=[alt.Tooltip('mes_dt:T', title='Mês', format='%b/%Y'), 'entrada_seguidor:Q']
                    ).properties(
                        title='Entrada de Novos Seguidores (Mensal)'
                    ).interactive()
                
                else:
                    # PLOTAR O GRÁFICO DIÁRIO (FILTRADO)
                    mes_dt_selecionado = df_mensal[df_mensal['mes_str'] == mes_selecionado_grafico1]['mes_dt'].iloc[0]
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
                        title=f'Entrada Diária de Seguidores ({mes_selecionado_grafico1})'
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
                    # Plotar APENAS A LINHA
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

    st.markdown(f"## :orange[Análise Detalhada de Engajamento]")
    
    col3, col4 = st.columns(2)

    # --- Gráfico 3: Barras (Altair) COM FILTRO ---
    with col3:
        if df_eng is None:
            st.error("Arquivo 'EngXEnt.csv' não encontrado. Gráficos 3 e 4 não podem ser gerados.")
        else:
            try:
                cols_existentes = [col for col in eng_cols if col in df_eng.columns]
                
                if not cols_existentes:
                    st.warning("Gráfico 3: Nenhuma coluna de engajamento encontrada em 'EngXEnt.csv'.")
                else:
                    # LÓGICA DO FILTRO (baseada na variável 'mes_selecionado_eng' da sidebar)
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

    # --- Gráfico 4: "Gráfico de Eficiência" (SEM DESTAQUES) ---
    with col4:
        if df_eng is None:
            pass # Erro já reportado no Gráfico 3
        else:
            try:
                # Filtra os meses onde a taxa_conversao não pôde ser calculada
                df_plot_4 = df_eng.dropna(subset=['taxa_conversao_eng'])

                if df_plot_4.empty:
                    st.warning("Gráfico 4: Não há dados suficientes para calcular a eficiência (ex: meses sem novos seguidores).")
                else:
                    base = alt.Chart(df_plot_4).mark_bar(color=COLOR_NEUTRAL).encode(
                        x=alt.X('mes_dt:T', axis=alt.Axis(title='Mês', format='%Y-%m')),
                        y=alt.Y('taxa_conversao_eng:Q', axis=alt.Axis(title='Engajamentos por Novo Seguidor')),
                        tooltip=[
                            alt.Tooltip('mes_str:N', title='Mês'),
                            alt.Tooltip('taxa_conversao_eng:Q', title='Custo (Engaj./Seguidor)', format='.1f'),
                            alt.Tooltip('engajamento_total:Q', title='Total de Engajamentos'),
                            alt.Tooltip('entrada_seguidores:Q', title='Novos Seguidores')
                        ]
                    ).properties(
                        title='Eficiência: Custo de Engajamento por Novo Seguidor (Menor é Melhor)'
                    )
                    
                    chart4 = base.interactive()
                    st.altair_chart(chart4, use_container_width=True)

            except Exception as e:
                st.error(f"Erro ao gerar Gráfico 4 (Eficiência): {e}")

if __name__ == "__main__":
    main()

