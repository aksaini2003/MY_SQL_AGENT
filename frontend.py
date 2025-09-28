
import streamlit as st 
from backend import workflow

# Page config
st.set_page_config(page_title="Smart DB Agent", layout="wide")

# Title
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🧠 Smart DB Agent</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Ask your database anything in natural language</h4>", unsafe_allow_html=True)

st.write("---")

# Large text input for user statement
user_statement = st.text_area(
    "💬 Enter your question here:",
    height=150,
    placeholder="Example: what are top 10 customers by sales"
)

# # Button to execute
# if st.button("🚀 Run Query"):
#     if user_statement.strip():
#         with st.spinner("Generating SQL query and fetching results..."):
#             initial_state = {"user_statement": user_statement}
#             final_state = workflow.invoke(initial_state)

#             # Show generated SQL query (if available)
#             query = final_state.get("query", None)
#             if query:
#                 st.markdown("### 📜 Generated SQL Query")
#                 st.code(query, language="sql")

#             # Show results
#             results = final_state.get("results", None)
#             if results is not None and not results.empty:
#                 st.markdown("### 📊 Query Results")
#                 if len(results) > 50:
#                     st.info(f"Showing first 50 rows (out of {len(results)} rows)")
#                     st.dataframe(results.head(50), use_container_width=True)
#                 else:
#                     st.dataframe(results, use_container_width=True)
#             else:
#                 st.warning("⚠️ No results found.")
#     else:
#         st.warning("⚠️ Please enter a question before running the query.")
import pandas as pd

if st.button("🚀 Run Query"):
    if user_statement.strip():
        with st.spinner("Generating SQL query and fetching results..."):
            initial_state = {"user_statement": user_statement}
            try:
                final_state = workflow.invoke(initial_state)

                # Show generated SQL query (if available)
                query = final_state.get("sql_query", None)
                if query:
                    st.markdown("### 📜 Generated SQL Query")
                    st.code(query, language="sql")

                # Show results
                
                results = final_state.get("results", None)
                if results is not None:
                    if isinstance(results, pd.DataFrame):
                        st.markdown("### 📊 Query Results")
                        if len(results) > 50:
                            st.info(f"Showing first 50 rows (out of {len(results)} rows)")
                            st.dataframe(results.head(50), use_container_width=True)
                        else:
                            st.dataframe(results, use_container_width=True)
                    else:
                        # If results is not a dataframe, show it as a warning
            
            
                        st.warning(f"{results}")
                else:
            
                    st.warning("⚠️ No results found.")
            except: 
                st.info('Sorry, but i am not able to understand your Statement, please provide an understandable statement')
            
            
            
    else:
        st.warning("⚠️ Please enter a question before running the query.")
