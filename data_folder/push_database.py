import pandas as pd
import streamlit as st
from sqlalchemy import Engine, create_engine

from preprocess_query_data import generate_path

# ==============================
# ||   TABLES CONFIGURATION   ||
# ==============================

TABLES_CONFIGURATION = {
    'amazon_query_data': {
        'filename': 'amazon_query_data.csv',
        'columns': [
            'product_id','product_name','price', 'rating','rating_count',
            'about_product','review_title','review_content',
            'img_link','product_link','ctgr_1','ctgr_2','ctgr_3','ctgr_4'
        ],
        'table_name': 'amazon_query_data'
    },

    'amazon_training_data': {
        'filename': 'amazon_training_data.csv',
        'columns': ['product_id', 'text_corpus'],
        'table_name': 'amazon_training_data'
    }
}

def push_table(engine: Engine, table_config: dict):
    data_path = generate_path(table_config['filename'])
    df = pd.read_csv(data_path)
    df = df[table_config['columns']] # ensure columns order
    df.to_sql(
        name=table_config['table_name'],
        if_exists='append',
        con=engine,
        index=False,
    )
    print(f"Inserted {len(df)} rows into table '{table_config['table_name']}' from: {data_path}")


if __name__ == '__main__':

    engine = create_engine(st.secrets['DATABASE_CONFIGURATION']['URI'])
    with engine.begin() as connection:
        push_table(connection, TABLES_CONFIGURATION['amazon_query_data'])
        push_table(connection, TABLES_CONFIGURATION['amazon_training_data'])

    print('Data pushed successfully.')
