import pandas as pd
import openai
import sqlite3
import streamlit as st

# Load the csv data and create and get the colunm names
df = pd.read_csv('E:\\Projects\\Infogain_usecase\\GenAI-Solutions\\genai_health_data\\health_data_merged.csv')
columns = df.columns.tolist()
##Connecting to sqlite3 database
conn = sqlite3.connect(':memory:')
df.to_sql('health_dataset', conn, index=False, if_exists='replace')

# Function to generate SQL query according to the dataset
def generate_sql_query(question, columns):
    prompt = f"""
    I have a health dataset with the following columns: {', '.join(columns)}. Column physical activity is continuous with float data type, Blood_Pressure_Abnormality is categorical where 0 means normal and 1 means abnormal.
    Level_of_Hemoglobin is continuous and float datatype. Genetic_Pedigree_Coefficient ranges from 0 to 1 where 0 means very 
    distant occurrence of that disease in his/her pedigree and 1 means immediate occurrence of that disease in his/her pedigree.
    Columns Age and BMI are continuous values with integer datatype. Columns Sex, Pregnancy and Smoking are categorical variables with 0 or 1 as 
    values. 0 in Sex means male and 1 means female. 0 in Pregnancy means not pregnant and 1 means pregnant. 0 in Smoking means person is a non-smoker
    and 1 means a smoker. Column salt_content_in_the_diet is a continuous value with integer data type. Column alcohol_consumption_per_day is a continuous value with float as data type.
    Level_of_Stress is a categorical column which has values 1, 2, and 3. 1 means low stress, 2 means medium stress, and 3 means high stress.
    Chronic_kidney_disease and Adrenal_and_thyroid_disorders are categorical columns with 0 and 1 as values. 1 means presence of disease and 0 means absence of disease. 
    For the user query, "{question}", generate only the SQL query that retrieves data relevant to this user's condition in relation to the dataset.
    Provide only the SQL query, no additional text.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a data scientist."},
            {"role": "user", "content": prompt}
        ]
    )
    
    sql_query = response['choices'][0]['message']['content'].strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    
    return sql_query

# Function to execute the SQL query
def subset(sql_query, conn):
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        return f"{str(e)}"

# Function to generate content with respect to result, sql query generated and user inut
def generate_nlp_content(result, sql_query, question):
    if not result:
        return "No relevant data found........."

    prompt = f"""
    User Query: {question}
    SQL Query Executed: {sql_query}
    
    The SQL query was executed against a health dataset and the following results were obtained:
    {result}
    
    Based on this information, provide a detailed response that answers the user's query and includes any relevant insights from the data.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in health data analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response['choices'][0]['message']['content'].strip()

st.title("GenAI Solution for Conducting Health Data Analysis")

question = st.text_input("Please enter your question:", "")

if st.button("Analyze") and question:
    sql_query = generate_sql_query(question, columns)
    st.write("SQL Query is:")
    st.code(sql_query, language="sql")

    # Step for running SQL query on the provided data
    result = subset(sql_query, conn)
    
    if isinstance(result, str):
        st.error(result)
    else:
        if len(result) > 0:
            df_result = pd.DataFrame(result, columns=df.columns)  
            st.write("SQL Query Result:")
            st.dataframe(df_result)
        else:
            st.write("No records found. Please try again")

        nl_response = generate_nlp_content(result, sql_query, question)
        st.write("Here is the solution for your query:")
        st.write(nl_response)
