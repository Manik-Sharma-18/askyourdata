#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sqlite3
import pandas as pd
import re
import difflib
from sql_model_runner import translate_to_sql

# 🔧 Get schema as {table: [column1, column2, ...]}
def get_db_schema(db_path="data/chinook.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        columns = [row[1] for row in cursor.fetchall()]
        schema[table] = columns

    conn.close()
    return schema

# 🧠 Extract table and column names from SQL query
def extract_identifiers(sql):
    table_matches = re.findall(r'\bfrom\s+(\w+)|\bjoin\s+(\w+)', sql, re.IGNORECASE)
    tables = [t for pair in table_matches for t in pair if t]

    column_match = re.search(r'\bselect\s+(.*?)\s+from', sql, re.IGNORECASE)
    if column_match:
        raw_columns = column_match.group(1)
        columns = [col.strip().split('.')[-1] for col in raw_columns.split(',')]
    else:
        columns = []

    return tables, columns

# 🛡️ Optional: validate if tables/columns exist
def validate_sql(sql_query, db_path="data/chinook.db"):
    schema = get_db_schema(db_path)
    tables_in_db = set(schema.keys())

    tables, columns = extract_identifiers(sql_query)

    for table in tables:
        if table not in tables_in_db:
            raise ValueError(f"❌ Table `{table}` not found in database.")
        for col in columns:
            if col == '*':
                continue
            if col not in schema[table]:
                raise ValueError(f"❌ Column `{col}` not found in table `{table}`.")

# 🚀 Run a SQL query on a database (after validation)
def run_query(sql_query: str, db_path="data/chinook.db") -> pd.DataFrame:
    validate_sql(sql_query, db_path)

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn)
    finally:
        conn.close()

    return df

#To return sample rows from any table
def preview_table(table_name, db_path="data/chinook.db", limit=5):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
    finally:
        conn.close()
    return df

# 👀 Return first N rows of a given table
def preview_table(table_name, db_path="data/chinook.db", limit=5):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
    finally:
        conn.close()
    return df

#Helper function in case of slight name mismatches
def fix_table_names_in_sql(sql: str, schema_dict: dict) -> str:
    existing_tables = set(schema_dict.keys())

    # Extract candidate table names from SQL
    matches = re.findall(r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)', sql, re.IGNORECASE)
    used_tables = [m for pair in matches for m in pair if m]

    corrected_sql = sql
    for table in used_tables:
        if table not in existing_tables:
            # Try fuzzy matching to find closest valid table
            closest = difflib.get_close_matches(table, existing_tables, n=1)
            if closest:
                corrected_sql = re.sub(
                    rf'\b{table}\b',
                    closest[0],
                    corrected_sql,
                    flags=re.IGNORECASE
                )
    return corrected_sql

#Global case insensitivity
def normalize_sql_identifiers(sql: str, schema: dict) -> str:
    table_map = {t.lower(): t for t in schema}
    column_map = {}

    for cols in schema.values():
        for col in cols:
            column_map[col.lower()] = col

    # Fix table names
    for wrong, correct in table_map.items():
        sql = re.sub(rf'\b{wrong}\b', correct, sql, flags=re.IGNORECASE)

    # Fix column names
    for wrong, correct in column_map.items():
        sql = re.sub(rf'\b{wrong}\b', correct, sql, flags=re.IGNORECASE)

    return sql

#postgres syntax misbehaving
def fix_postgres_syntax(sql: str) -> str:
    # Replace ILIKE → LIKE
    sql = re.sub(r'\bILIKE\b', 'LIKE', sql, flags=re.IGNORECASE)

    # Remove NULLS FIRST / LAST
    sql = re.sub(r'\s+NULLS\s+(FIRST|LAST)', '', sql, flags=re.IGNORECASE)

    # Replace TRUE/FALSE with 1/0
    sql = re.sub(r'\bTRUE\b', '1', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bFALSE\b', '0', sql, flags=re.IGNORECASE)

    return sql

