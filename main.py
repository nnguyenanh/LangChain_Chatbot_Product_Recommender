# BUILT-IN LIBRARIES
import os

# THIRD-PARTY LIBRARIES
    # data
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError

# USER-DEFINED LIBRARIES
from create_agent.create_agent import create_custom_agent


@st.fragment
def connect_database():
    if 'engine' in st.session_state:
        return

    try:
        st.session_state.engine = create_engine(st.secrets['DATABASE_CONFIGURATION']['URI'])
        with st.session_state.engine.connect() as conn:
            conn.execute(text('SELECT 1'))

    except SQLAlchemyError as e:
        st.error('Failed to connect to database. Please check configuration or MySQL server.')
        st.caption(f'**Error detail:** {e}')
        st.stop()  # dừng Streamlit tại đây

    except Exception as e:
        st.error('Unexpected error while connecting to database.')
        st.caption(str(e))
        st.stop()

@st.fragment
def set_environment_key() -> None:
    os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']['key']
   
@st.fragment
def display_tables_preview(engine: Engine) -> None:
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text('SELECT * FROM amazon_query_data LIMIT 300'), conn)
    except Exception as e:
        st.error(f'Cannot connect to database: {e}')
        return

    st.subheader('Preview Table')
    st.dataframe(df, height=350)

    
@st.fragment
def create_all_agents() -> None:
    if 'agent' not in st.session_state:
        st.session_state.agent = create_custom_agent()

@st.fragment
def setup():
    # title
    st.title('Products Recommender')
    # connect to database
    connect_database()
    # set OPENAI_API_KEY
    set_environment_key()
    
def render_recent_chat(max_history: int):
    recent = st.session_state.chat_history[max_history:]
    for i in range(len(recent) - 2, -1, -2):
        q = recent[i]; 
        a = recent[i + 1]
        st.markdown('<i><span style="color: orange;">Question</span></i>', unsafe_allow_html=True)
        st.markdown(f'{q['content']}')
        st.markdown('<i><span style="color: orange;">Answer</span></i>', unsafe_allow_html=True)
        st.markdown(f'{a['content']}')
        st.markdown('---')

# invoke chatbot
def run_chatbot() -> None:
    st.subheader('Agent')
    
    col_input, col_ask = st.columns([9, 1])
    with col_input:
        input_question = st.text_input(
            'Enter your question',
            label_visibility='collapsed',
            key='chat_input',
            placeholder='Ask me about the products'
        )
    with col_ask:
        ask_clicked = st.button('Ask', use_container_width=True)

    st.caption('*Note: Clear and well-structured questions deliver the best results.*')
   
    max_history = -6
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    spinner_placeholder = st.empty()
    chat_placeholder = st.empty()
    with chat_placeholder.container():
        render_recent_chat(max_history)
    
    if input_question and ask_clicked:
        with spinner_placeholder, st.spinner('*Thinking...*'):
            try:
                # retrive agents from state_session
                st.session_state.chat_history.append({
                    'role': 'user', 'content': input_question
                })
                
                context = st.session_state.chat_history
                
                # retrive and run
                agent = st.session_state.agent
                response = agent.invoke({
                    'messages': context,
                    'recursion_limit': 3
                    })
                
                output_custom_agent = response['messages'][-1].content
                
                st.session_state.chat_history.append({
                    'role': 'assistant', 
                    'content': output_custom_agent
                    })

                st.session_state.chat_history = st.session_state.chat_history[max_history:]
                    
                with chat_placeholder.container():
                    render_recent_chat(max_history)   
                    st.write(response['messages'])
                                    
            except Exception as e:
                st.error(f'Error: {e}')

if __name__ == '__main__':
    with st.spinner('*Connecting to database ...*'):
        setup()
        display_tables_preview(st.session_state.engine)
    
    with st.spinner('*Checking required cache and component ...*'):
        create_all_agents() # create all agents
    
    run_chatbot()
