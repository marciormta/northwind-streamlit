# 2_ask_sql_question.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent, AgentExecutor
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Pegar credenciais do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TABLE_NAME = "northwind_data" # O mesmo nome de tabela usado no script 1

# Verificar se as variáveis de ambiente foram carregadas
if not DATABASE_URL:
    logging.error("Erro: A variável de ambiente DATABASE_URL não está definida no .env.")
    exit()
if not OPENAI_API_KEY:
    logging.error("Erro: A variável de ambiente OPENAI_API_KEY não está definida no .env.")
    exit()

def ask_sql_database():
    """Configura o agente Langchain e permite fazer perguntas ao banco de dados."""
    try:
        logging.info("Conectando ao banco de dados SQL Server...")
        engine = create_engine(DATABASE_URL)

        # Criar a instância do SQLDatabase do Langchain
        # include_tables: Especifica quais tabelas o agente deve considerar. MUITO IMPORTANTE!
        logging.info(f"Configurando Langchain para acessar a tabela: {TABLE_NAME}")
        db = SQLDatabase(engine=engine, include_tables=[TABLE_NAME])

        # Configurar o modelo LLM (GPT-4o)
        logging.info("Configurando o modelo LLM (gpt-4o)...")
        llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=OPENAI_API_KEY)

        # Criar o Toolkit e o Agente SQL
        # O toolkit fornece as ferramentas necessárias para o agente interagir com o DB
        logging.info("Criando o SQL Agent Toolkit...")
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)

        logging.info("Criando o SQL Agent Executor...")
        # agent_type="openai-tools": Utiliza as capacidades de "tools" da OpenAI
        # verbose=True: Mostra os pensamentos e ações do agente (útil para debug)
        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            agent_type="openai-tools"
        )

        logging.info("Agente SQL pronto. Digite sua pergunta ou 'sair' para terminar.")

        # Loop para fazer perguntas
        while True:
            user_question = input("\nSua pergunta: ")
            if user_question.lower() in ['sair', 'exit', 'quit']:
                logging.info("Encerrando...")
                break
            if not user_question:
                continue

            # Invocar o agente com a pergunta
            try:
                logging.info(f"Processando pergunta: {user_question}")
                # O agente decide se precisa consultar o DB, qual query usar, etc.
                result = agent_executor.invoke({"input": user_question})
                print("\nResposta:")
                print(result['output'])
            except Exception as e:
                logging.error(f"Erro ao processar a pergunta: {e}")
                print("\nOcorreu um erro ao tentar obter a resposta. Verifique os logs.")
                logging.exception("Detalhes do erro:") # Loga o stack trace

    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado na configuração ou execução: {e}")
        logging.exception("Detalhes do erro:")

if __name__ == "__main__":
    ask_sql_database()