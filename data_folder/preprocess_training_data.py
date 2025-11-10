import pandas as pd

from preprocess_query_data import (
    generate_path,
    clean_text
)

NAME_INPUT_FILE  = 'amazon_query_data.csv'
NAME_OUTPUT_FILE = 'amazon_training_data.csv'

if __name__ == '__main__':
    df = pd.read_csv(generate_path(NAME_INPUT_FILE))
    
    # explore data
    # print(df.isnull().sum())
    # df.dropna(inplace=True)
    print(df.isnull().sum())

    df['review_content'] = df['review_content'].astype(str).str.slice(0, 1500)

    df['text_corpus'] = (
        df['product_name'].astype(str) + ' ' +
        df['about_product'].astype(str) + ' ' +
        df['review_title'].astype(str) + ' ' +
        df['review_content'].astype(str) + ' ' +
        df['ctgr_1'].astype(str) + ' ' +
        df['ctgr_2'].astype(str) + ' ' +
        df['ctgr_3'].astype(str) + ' ' +
        df['ctgr_4'].astype(str)
    )
    # clean text
    df['text_corpus'] = df['text_corpus'].apply(clean_text)
    
    df[['product_id', 'text_corpus']].to_csv(
        generate_path(NAME_OUTPUT_FILE), index=False
    )
    
    dup_products = df[df.duplicated(subset=['product_id'], keep=False)]
    print(dup_products[['product_id', 'text_corpus']].sort_values('product_id'))
   
    df[['product_id', 'text_corpus']].to_csv(generate_path(NAME_OUTPUT_FILE), index=False)
    print(f'Preprocessed TRAINING data saved to {generate_path(NAME_OUTPUT_FILE)}.')


