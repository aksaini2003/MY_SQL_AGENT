from langgraph.graph import StateGraph,START,END 
from langchain_groq import ChatGroq 
from dotenv import load_dotenv 
from pydantic import BaseModel,Field
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sqlite3
from typing import TypedDict,List,Literal
from langchain_google_genai import ChatGoogleGenerativeAI
import mysql.connector
import pandas as pd 
import streamlit as st 

#STATE SCHEMA OF OUR AGENT

#State Definition


class Graph_Schema(TypedDict):
    user_statement:str 
    sql_query: str 
    results: List[List[str]]
    error: str
    safety_msg:str  

load_dotenv()




#NOTE: llm for the initial checkup of user's statement
groq_api_key=st.secrets['GROQ_API_KEY']
                        #replace with your groq api key
llm2=ChatGroq(model='Llama-3.3-70b-versatile',api_key=groq_api_key)
#CODE FOR INITIAL CHECKUP
class Initial_check_schema(BaseModel): 
    validation: Literal['Safe', 'Irrelevant', 'Modification'] = Field(
        ...,
        description='''
Classification of the user's input:

- "Safe": A valid SQL query OR a natural-language request that can be translated into a safe, read-only query 
  (e.g., "SELECT...", "SHOW...", "DESCRIBE...", or "find all orders with order id X").
  These inputs do not modify the database.

- "Modification": Any query that attempts to change the database contents or structure 
  (e.g., DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE).

- "Irrelevant": Inputs that are unrelated to database usage, meaningless, or general conversation 
  (e.g., greetings, jokes, random text).
'''
    )


validation_llm=llm2.with_structured_output(Initial_check_schema)

def Initial_Check(state: Graph_Schema)->Literal['get_query','not_valid','contain_modification']:
    user_input=state['user_statement']
    validation_llm=llm.with_structured_output(Initial_check_schema)
    prompt = f"""
You are a **SQL Safety Checker**.

Your task is to classify the user's input into one of three categories:

1. **Modification** → The input tries to change the database.  
   This includes SQL commands like: DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE.  

2. **Irrelevant** → The input is meaningless, unrelated to data/queries, or has no intent of retrieving or working with database information.  
   Examples: greetings ("hello"), chit-chat, or completely random text.  

3. **Safe** → The input is either:
   - A valid SQL query that only retrieves data (e.g., SELECT, SHOW, DESCRIBE), **or**  
   - A natural language request that can be translated into such a retrieval query (e.g., "find all the orders where order id is CA-2018-138688").  

⚠️ Important:  
- Treat meaningful **data-related questions or requests** as "Safe", even if they are not written in SQL.  
- Only reply with one of these exact words: **"Modification"**, **"Irrelevant"**, or **"Safe"**.  
- Do not include any explanation or extra text.  

---

User Input:
{user_input}
"""

    response=validation_llm.invoke(prompt).validation 
    if response=='Irrelevant': 
        return 'not_valid' 
    elif response=='Modification':
        return 'contain_modification'
    
    else: 
        return 'get_query'
    





def Not_Valid(state: Graph_Schema)-> Graph_Schema: 
    #here we have to return a message that tell to theuser that it can't do any updation and deletion 
    # in Database
    #here we are directly providing a message to the user 
    msg='''⚠️ The input doesn't seem related to the agent's intended purpose.

Please provide a valid query or instruction that aligns with the system's capabilities.
'''
    state['results']=msg 
    return state 
def Contain_modification(state: Graph_Schema)-> Graph_Schema: 
    msg='''The input looks like it tries to change data (e.g. UPDATE / DELETE) or isn’t related to data analysis.
Only read-only queries are allowed.
Try asking something like “What are the top 10 users by sales?” instead.
'''
    state['results']=msg 
    return state 
    












#NOTE: LLM FOR THE QUERY GENERATION
# llm=ChatGroq(model='Llama-3.3-70b-versatile') 
google_api_key=st.secrets['GOOGLE_API_KEY']
llm=ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite',api_key=google_api_key) #yeah this is working well 
#this is better then the llama-3.3-70b-versatile
#lets also check with the google_gemini models 
class SQL_schema(BaseModel):
  
    sql_query: str=Field(...,description='Write a SQL Query for a given problem') 
    


row_limit = 50

schema_snippet = """table: super_store (Row ID, Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Customer Name, 
                Segment, Country/Region, City, State, Postal Code, Region, Product ID, Category, Sub-Category, 
                Product Name,Sales, Quantity, Discount, Profit"""


# business_glossary = '{"active_customer": "users.last_active > now() - interval \'30 days\'"}'

prompt = PromptTemplate.from_template("""
You are a SQL generator for a MYSQL database. Use the schema information below to write a single SQL query that answers the user's request. Do not modify data. Apply sensible defaults for ambiguous items, and ask follow-up question only if absolutely necessary.

Schema snippet:
{schema_snippet}


User request: {query}

Constraints:
- Use only SELECT queries. No DML or DDL.
- Limit returned rows to {row_limit} unless user asks for full export.
- You can't run any deletion query


Provide:
1. A single SQL query.

""")
sql_llm=llm.with_structured_output(SQL_schema)

chain=prompt|sql_llm 



    
avn_password=st.secrets['AVN_PASSWORD']

#DataBase Connection
# NOTE: Function for the Database setup_database
#here we are using mysql db hosted on aviencloud and we can use it online
def Database_Setup():
    conn = mysql.connector.connect(
        host="mysql-2cc1e931-kumarsainiaashish2003-0464.j.aivencloud.com",
        port=17784,
        user="avnadmin",            # your Aiven username
        password=avn_password,   # your Aiven password
        database="defaultdb",       # your schema name
        ssl_ca="ca_certificate/ca.pem"     # Aiven SSL certificate
    )
    return conn

#The following function is for structuring the result of the database table 


def print_table_output(cursor):
    """
    Converts SQL query results into a Pandas DataFrame.
    Assumes cursor has already executed a query.
    """
    # Extract column headers
    headers = [desc[0] for desc in cursor.description]

    # Fetch all rows
    rows = cursor.fetchall()

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)

    return df

def execute(query):
    # cursor=connection.cursor()]
    conn=Database_Setup()
    cursor=conn.cursor()
    cursor.execute(query)
    output=print_table_output(cursor)
    cursor.close()
    return output
    cursor.close()
    
#yeah this is working well now lets use it with the llm 



#Graph nodes implementation
#let make a function that will return the sql query corresponding to user's statement 
# def User_input(state: Graph_Schema)-> Graph_Schema:
#     user_statement=state['user_statement']
#     #now we have to pass it to the llm with metadata 
#     return {'user_statement':user_statement} 
#no need of this because here we are providind directly the input of user_statement
def Get_Query(state: Graph_Schema)-> Graph_Schema: 
    statement=state['user_statement'] 

    generated_query=chain.invoke({'query':statement,'schema_snippet':schema_snippet,'row_limit':row_limit})
    sql_query=generated_query.sql_query
    return {'sql_query':sql_query} 
def Execute_Query(state: Graph_Schema)-> Graph_Schema:
    query=state['sql_query'] 
    results=execute(query) 
    return {'results':results} 
    
    
graph=StateGraph(Graph_Schema)


#Graph Definition 
# graph.add_node('User_statement',User_input) graph.add_node('User_statement',User_input) 
graph.add_node('get_query',Get_Query)
graph.add_node('execute_query',Execute_Query) 

graph.add_node('not_valid',Not_Valid)
graph.add_node('contain_modification',Contain_modification)
# graph.add_edge(START,'User_statement') 

graph.add_conditional_edges(START,Initial_Check)
graph.add_edge('not_valid',END)
graph.add_edge('contain_modification',END)
graph.add_edge('get_query','execute_query') 
graph.add_edge('execute_query',END)



workflow=graph.compile()
