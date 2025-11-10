from pathlib import Path
import pandas as pd
import csv
import re
import unicodedata
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

NAME_DATA_FILE = 'amazon.csv'

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def generate_path(filename: str='') -> str:
    parent_folder = Path(__file__).resolve().parent
    current_path = parent_folder / filename
    return str(current_path)

def clean_text(text):
    # normalize accents
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    # keep letters and digits, remove everything else
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # lowercase
    text = text.lower().strip()
    # remove stopwords and lemmatize
    words = [
        lemmatizer.lemmatize(w)
        for w in text.split()
        if w not in stop_words
    ]
    return ' '.join(words)

def keep_keyboard_chars(val) -> str:
    if isinstance(val, str):
        return ''.join(c for c in val if 32 <= ord(c) <= 126)
    return val

if __name__ == '__main__':
    df = pd.read_csv(generate_path(NAME_DATA_FILE))
    # df = df.head(1000)
    # explore data
    # print(df.isnull().sum())
    df.dropna(inplace=True)
    print(df.isnull().sum())
    
    # drop duplicate
    df.drop_duplicates(subset='product_id', inplace=True)

    # drop review_id
    df.drop(columns=['user_id', 'user_name', 'review_id'], inplace=True)

            # split categories in to 7 levels
    new_cat_level = ['ctgr_1', 'ctgr_2', 'ctgr_3', 'ctgr_4', 'ctgr_5', 'ctgr_6', 'ctgr_7']
    splitted_ctgr = df['category'].apply(lambda x: re.split(r'\s*[|]\s*', str(x)))
    print(splitted_ctgr)

    for i in range(7):
        new_column = []
        for sublist_ctgr in splitted_ctgr:
            if len(sublist_ctgr) > i:
                new_column.append(sublist_ctgr[i])
            else:
                new_column.append('Blank')
            
        df[new_cat_level[i]] = new_column
    df.drop(df[df['ctgr_4'] == 'Blank'].index, inplace=True)

    df.drop(columns=['category', 'ctgr_5', 'ctgr_6', 'ctgr_7'], inplace=True)
    
    def count_blank_ctgr(df):
        ctgr_cols = [col for col in df.columns if col.startswith('ctgr_')]
        return (df[ctgr_cols] == 'Blank').sum()

    result = count_blank_ctgr(df)
    print(result)
    # ctgr_1    5
    # ctgr_2    10
    # ...

    #  'ctgr_5', 'ctgr_6', 'ctgr_7']
    
    # remove symbols
    # df['discounted_price'] = df['discounted_price'].str.replace('₹', '').str.replace(',', '').astype(float)
    df['actual_price'] = df['actual_price'].str.replace('₹', '').str.replace(',', '').astype(float)
    df.rename({'actual_price': 'price'}, axis=1, inplace=True)
    
    # df['discount_percentage'] = df['discount_percentage'].str.replace('%', '').astype(float)
    df.drop(columns=['discounted_price', 'discount_percentage'], inplace=True)
    for col in df.select_dtypes(include='object'):
        df[col] = df[col].apply(keep_keyboard_chars)

    df['rating_count'] = df['rating_count'].replace(',', '', regex=True).astype(int)
    df['review_title'] = df['review_title'].apply(clean_text)
    df['review_content'] = df['review_content'].apply(clean_text)

    result = count_blank_ctgr(df)
    print(result)
    # print(df)

    df.head(1000).to_csv(generate_path('amazon_query_data.csv'), index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f'Preprocessed QUERY data saved to: {generate_path()}')
