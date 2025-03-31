# 1_load_data_to_sql.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Pegar a URL do banco de dados do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
EXCEL_FILE_PATH = "base_northwind.xlsx"
TABLE_NAME = "northwind_data" # Nome da tabela que será criada no SQL Server

if not DATABASE_URL:
    logging.error("Erro: A variável de ambiente DATABASE_URL não está definida.")
    exit()

if not os.path.exists(EXCEL_FILE_PATH):
    logging.error(f"Erro: O arquivo Excel '{EXCEL_FILE_PATH}' não foi encontrado.")
    exit()

def load_data_to_sql():
    """Lê dados do Excel e carrega para o SQL Server."""
    try:
        logging.info(f"Lendo dados do arquivo Excel: {EXCEL_FILE_PATH}...")
        # Assume que os dados estão na primeira planilha (sheet_name=0)
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=0)
        logging.info(f"Leitura do Excel concluída. {len(df)} linhas encontradas.")

        logging.info("Conectando ao banco de dados SQL Server...")
        # Criar a engine do SQLAlchemy
        engine = create_engine(DATABASE_URL, connect_args={"timeout": 50}) # Aumenta o timeout para 30 segundos

        # Verificar conexão (opcional, mas bom para debug)
        with engine.connect() as connection:
            logging.info("Conexão com o banco de dados estabelecida com sucesso.")

            # Limpar nomes de colunas (substituir espaços e caracteres especiais)
            df.columns = df.columns.str.replace(r'[^A-Za-z0-9_]+', '', regex=True)
            # Renomear colunas que possam ser palavras reservadas do SQL (ex: 'ORDER')
            df.rename(columns={'ORDER': 'Order_Col'}, inplace=True, errors='ignore') # Adicione outros se necessário

            logging.info(f"Carregando dados para a tabela '{TABLE_NAME}' no SQL Server...")
            # Usar to_sql para carregar o DataFrame
            # if_exists='replace': Se a tabela já existir, ela será excluída e recriada.
            #                  Use 'append' se quiser adicionar dados a uma tabela existente.
            #                  Use 'fail' se não quiser fazer nada caso a tabela exista.
            df.to_sql(TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000) # chunksize ajuda com tabelas grandes
            logging.info(f"Dados carregados com sucesso na tabela '{TABLE_NAME}'.")

    except FileNotFoundError:
        logging.error(f"Erro: Arquivo Excel não encontrado em '{EXCEL_FILE_PATH}'.")
    except ImportError:
        logging.error("Erro: Biblioteca 'openpyxl' necessária para ler arquivos .xlsx. Instale com 'pip install openpyxl'.")
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado durante o carregamento dos dados: {e}")
        logging.exception("Detalhes do erro:") # Loga o stack trace completo

if __name__ == "__main__":
    load_data_to_sql()