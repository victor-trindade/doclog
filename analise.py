import pandas as pd

# Carregar os arquivos Excel
file_path = 'CONSOLIDADO.xlsx'  # Arquivo principal
file_path_drivers = 'Relatório de Drivers - FRANQUIA_D&G_SP.xlsx'  # Arquivo de colaboradores ativos

print(f'Carregando Arquivos: {file_path} e {file_path_drivers}')
df = pd.read_excel(file_path)
df_drivers = pd.read_excel(file_path_drivers)

# Converter colunas para tipos adequados
df['data_do_periodo'] = pd.to_datetime(df['data_do_periodo'], format='%d/%m/%Y')
df_drivers['driver_uuid'] = df_drivers['driver_uuid'].astype(str)

# Filtrar apenas os colaboradores ativos com base no relatório de drivers
df = df[df['id_da_pessoa_entregadora'].astype(str).isin(df_drivers['driver_uuid'])]

# Criar novas colunas para o dia da semana e o dia do mês
df['dia_da_semana'] = df['data_do_periodo'].dt.day_name()  # Nome do dia da semana (ex: 'Monday')
df['dia_do_mes'] = df['data_do_periodo'].dt.day  # Número do dia do mês (1, 2, 3, ...)

# Agrupar as horas entregues por dia da semana
horas_por_dia_semana = df.groupby('dia_da_semana')['tempo_disponivel_absoluto'].sum().reset_index()
horas_por_dia_semana.columns = ['Dia da Semana', 'Total de Horas Entregues']

# Agrupar as horas entregues por dia do mês
horas_por_dia_mes = df.groupby('dia_do_mes')['tempo_disponivel_absoluto'].sum().reset_index()
horas_por_dia_mes.columns = ['Dia do Mês', 'Total de Horas Entregues']

# Contagem de colaboradores únicos que rodaram em cada dia da semana
colaboradores_que_rodaram_semana = df.groupby('dia_da_semana')['id_da_pessoa_entregadora'].nunique().reset_index()
colaboradores_que_rodaram_semana.columns = ['Dia da Semana', 'Colaboradores Que Rodaram']

# Contagem de colaboradores únicos que não rodaram em cada dia da semana
colaboradores_que_nao_rodaram_semana = pd.DataFrame()
colaboradores_que_nao_rodaram_semana['Dia da Semana'] = horas_por_dia_semana['Dia da Semana']
colaboradores_que_nao_rodaram_semana['Colaboradores Que Não Rodaram'] = colaboradores_que_rodaram_semana['Dia da Semana'].apply(
    lambda x: df_drivers[~df_drivers['driver_uuid'].isin(df[df['dia_da_semana'] == x]['id_da_pessoa_entregadora'])].shape[0]
)

# Calcular a média e a mediana para os colaboradores que rodaram na semana
colaboradores_que_rodaram_semana['Média Rodaram'] = colaboradores_que_rodaram_semana['Dia da Semana'].apply(
    lambda x: df[df['dia_da_semana'] == x]['tempo_disponivel_absoluto'].mean()
)
colaboradores_que_rodaram_semana['Mediana Rodaram'] = colaboradores_que_rodaram_semana['Dia da Semana'].apply(
    lambda x: df[df['dia_da_semana'] == x]['tempo_disponivel_absoluto'].median()
)

# Contagem de colaboradores únicos que rodaram em cada dia do mês
colaboradores_que_rodaram_mes = df.groupby('dia_do_mes')['id_da_pessoa_entregadora'].nunique().reset_index()
colaboradores_que_rodaram_mes.columns = ['Dia do Mês', 'Colaboradores Que Rodaram']

# Contagem de colaboradores únicos que não rodaram em cada dia do mês
colaboradores_que_nao_rodaram_mes = pd.DataFrame()
colaboradores_que_nao_rodaram_mes['Dia do Mês'] = horas_por_dia_mes['Dia do Mês']
colaboradores_que_nao_rodaram_mes['Colaboradores Que Não Rodaram'] = colaboradores_que_rodaram_mes['Dia do Mês'].apply(
    lambda x: df_drivers[~df_drivers['driver_uuid'].isin(df[df['dia_do_mes'] == x]['id_da_pessoa_entregadora'])].shape[0]
)

# Calcular a média e a mediana para os colaboradores que rodaram no mês
colaboradores_que_rodaram_mes['Média Rodaram'] = colaboradores_que_rodaram_mes['Dia do Mês'].apply(
    lambda x: df[df['dia_do_mes'] == x]['tempo_disponivel_absoluto'].mean()
)
colaboradores_que_rodaram_mes['Mediana Rodaram'] = colaboradores_que_rodaram_mes['Dia do Mês'].apply(
    lambda x: df[df['dia_do_mes'] == x]['tempo_disponivel_absoluto'].median()
)

# Ajuste de nomes das abas para não exceder 31 caracteres
output_file = 'relatorio_horas_entregues_com_media_mediana.xlsx'
with pd.ExcelWriter(output_file) as writer:
    horas_por_dia_semana.to_excel(writer, sheet_name='Horas por Semana', index=False)
    horas_por_dia_mes.to_excel(writer, sheet_name='Horas por Mês', index=False)
    colaboradores_que_rodaram_semana.to_excel(writer, sheet_name='Rodaram Semana', index=False)
    colaboradores_que_nao_rodaram_semana.to_excel(writer, sheet_name='Nao Rodaram Semana', index=False)
    colaboradores_que_rodaram_mes.to_excel(writer, sheet_name='Rodaram Mês', index=False)
    colaboradores_que_nao_rodaram_mes.to_excel(writer, sheet_name='Nao Rodaram Mês', index=False)

print(f'Relatório salvo em: {output_file}')
