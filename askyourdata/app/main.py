#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import re
import io
import streamlit as st
import pandas as pd
from pandas import ExcelWriter
from query_engine import (
    get_db_schema,
    run_query,
    translate_to_sql,
    fix_table_names_in_sql,
    normalize_sql_identifiers,
    fix_postgres_syntax,
    preview_table
)

# Constants
DEFAULT_DB_PATH = "data/chinook.db"

# App config
st.set_page_config(page_title="AskYourData", page_icon="🧠", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>🧠 AskYourData</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Ask questions in natural language and get accurate SQL-backed answers — offline.</p>", unsafe_allow_html=True)

# Sidebar uploader
st.sidebar.title("📁 Upload SQLite DB")
uploaded_file = st.sidebar.file_uploader("Upload a `.db` file", type=["db"])

# Handle uploaded or fallback DB
def save_uploaded_file(uploaded_file):
    upload_dir = "uploaded_dbs"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if uploaded_file is not None:
    db_file_path = save_uploaded_file(uploaded_file)
    st.session_state.db_path = db_file_path
    st.success(f"✅ Using uploaded database: {uploaded_file.name}")
else:
    db_file_path = DEFAULT_DB_PATH
    st.session_state.db_path = db_file_path
    st.info("ℹ️ Using default database: `chinook.db`")

# Show schema
st.subheader("🗃️ Available Tables")
schema_dict = get_db_schema(st.session_state.db_path)
for table, columns in schema_dict.items():
    st.markdown(f"**{table}**: {', '.join(columns)}")

# Table preview
with st.expander("🔍 Preview Table"):
    selected_table = st.selectbox("Choose a table to preview", list(schema_dict.keys()))
    st.dataframe(preview_table(selected_table, st.session_state.db_path))

# Ask a question
st.subheader("💬 Ask Your Data")
user_question = st.text_input("What do you want to know? (e.g., 'List all customers from Canada')")

if user_question:
    try:
        # Translate + clean SQL
        schema_str = "\n".join([f"Table: {table} (columns: {', '.join(cols)})" for table, cols in schema_dict.items()])
        sql_query = translate_to_sql(user_question, schema_str)
        sql_query = fix_table_names_in_sql(sql_query, schema_dict)
        sql_query = normalize_sql_identifiers(sql_query, schema_dict)
        sql_query = fix_postgres_syntax(sql_query)

        # Display SQL and let user edit
        st.subheader("🧠 Generated SQL")
        sql_editable = st.text_area("Edit SQL before executing:", value=sql_query, height=150)

        if st.button("Run Edited SQL"):
            result_df = run_query(sql_editable, st.session_state.db_path)
            st.success("✅ Query executed successfully!")
            st.dataframe(result_df)
            st.session_state.query_history.append((user_question, sql_editable, result_df.head().to_markdown()))
        else:
            result_df = run_query(sql_query, st.session_state.db_path)
            st.success("✅ Query executed successfully!")
            st.dataframe(result_df)
            st.session_state.query_history.append((user_question, sql_query, result_df.head().to_markdown()))

        # ---------------------- 💾 Export Section ----------------------
        if not result_df.empty:
            st.subheader("📤 Export Query Results")

            # CSV Export
            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download as CSV",
                data=csv_data,
                file_name="query_result.csv",
                mime="text/csv"
            )

            # Excel Export
            excel_buffer = io.BytesIO()
            with ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                result_df.to_excel(writer, index=False, sheet_name='Results')
                writer.save()

            st.download_button(
                label="Download as Excel",
                data=excel_buffer.getvalue(),
                file_name="query_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")

# Query history
with st.expander("📜 Query History"):
    for idx, (q, sql, preview) in enumerate(reversed(st.session_state.query_history)):
        st.markdown(f"**Q{len(st.session_state.query_history)-idx}: {q}**")
        st.code(sql, language="sql")
        st.markdown("Result (first few rows):")
        st.markdown(preview)
        st.markdown("---")

