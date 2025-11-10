# BUILT-IN LIBRARIES
import os

# THIRD-PARTY LIBRARIES
from langchain_core.tools.base import BaseTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.agents import create_agent
from langchain_community.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import FAISS
import streamlit as st
import pandas as pd
from sqlalchemy import text

# USER-DEFINED LIBRARIES
# from prompt.prompts_sql import SYSTEM_PROMPT
from create_agent.prompt import SYSTEM_PROMPT

VECTOR_PATH = 'create_agent/recommender_vector_index'


def build_vector_cache(embeddings: OpenAIEmbeddings):
    # create FAISS index
    if not os.path.exists(VECTOR_PATH):
        print('Building FAISS vector index (first run)...')
        # get database connection from state_session
        engine = st.session_state.engine
        df = pd.read_sql(text('SELECT product_id, text_corpus FROM amazon_training_data;'), con=engine)

        texts = df['text_corpus'].astype(str).tolist()
        metas = [{'product_id': pid} for pid in df['product_id'].tolist()]

        texts = [t[:6000] for t in texts]

        vectorstore = FAISS.from_texts(
                texts=texts,
                embedding=embeddings,
                metadatas=metas
            )
        print(f'Embedded batch of {len(texts)} items into FAISS index.')

        vectorstore.save_local(VECTOR_PATH)
        print('FAISS vector index saved successfully.')

    else:
        print('Using cached FAISS index.')


def get_recommend_tools() -> list[BaseTool]:

    embeddings = OpenAIEmbeddings(model='text-embedding-3-large')  

    build_vector_cache(embeddings)

    # Load FAISS index 
    vectorstore = FAISS.load_local(
        VECTOR_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    # create tool
    @tool('recommend_products', return_direct=False)
    def recommend_products(query_text: str, top_k: int)-> str:
        '''
        Search for top-k semantically similar products using FAISS vector store.
        Return product_id only, after using this tool, for products in the product_query_table.
        '''
        top_k = min(12, top_k)
        results = vectorstore.similarity_search(query_text, k=top_k)
        if not results:
            return 'No similar products found.'

        output = []
        for doc in results:
            pid = doc.metadata.get('product_id')
            output.append(f'- {pid}')
        return 'Recommended Products:\n' + '\n'.join(output)
    
    return [recommend_products]


# def get_sql_tools(llm: ChatOpenAI):
def get_sql_tools() -> list[QuerySQLDatabaseTool]:
    
    db = SQLDatabase.from_uri(st.secrets['DATABASE_CONFIGURATION']['URI'])                 
    sql_tool_kit = QuerySQLDatabaseTool(db=db)
    # sql_toolkit_list = SQLDatabaseToolkit(db=db, llm=llm).get_tools()
    return [sql_tool_kit]

def get_helper_tools() -> list[BaseTool]:
    
    @tool('compare_products', return_direct=False)
    def compare_products(product_ids: list[str]) -> str:
        '''
        Compare key attributes (price, rating, discount, and top keywords in description)
        between given products.
        '''
        ids = '', ''.join(product_ids)
        query = f'''
            SELECT product_id, product_name, about_product,
                price, rating, rating_count
            FROM amazon_query_data
            WHERE product_id IN ('{ids}');
        '''
        return f'Compare the following products:\n{query}'
    
        
    @tool('detail_features', return_direct=False)
    def detail_features(product_ids: list[str]) -> str:
        '''
        Summarize product features from descriptions and reviews
        for one or multiple products.
        Example: detail_features(['B08LT9BMPP', 'B0XXXXXX'])
        '''
        # Build a safe comma-separated list for SQL IN clause
        ids = ', '.join(product_ids)
        query = f'''
            SELECT product_id, product_name, about_product, review_content,
                price, rating
            FROM amazon_query_data
            WHERE product_id IN ('{ids}')
            LIMIT {len(product_ids)};
        '''
        return f'Extract product details for summary:\n{query}'
        
    return [compare_products, detail_features]
    


def create_custom_agent():

    llm = ChatOpenAI(model='gpt-5-mini', temperature=0.1, disable_streaming=True)              
    
    toolkit = get_sql_tools() + get_recommend_tools() + get_helper_tools()
    
    agent = create_agent(
        model=llm,
        tools=toolkit,
        debug=True,
        system_prompt=SYSTEM_PROMPT
    )
    
    return agent