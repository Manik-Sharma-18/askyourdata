#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sqlite3
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "suriya7/t5-base-text-to-sql"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def translate_to_sql(question: str) -> str:
    input_text = f"translate English to SQL: {question}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True)
    outputs = model.generate(**inputs, max_length=128)
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if not sql.lower().startswith("select"):
        raise ValueError(f"⚠️ Invalid SQL: {sql}")
    return sql

def run_query(sql_query: str, db_path="data/chinook.db") -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn)
    finally:
        conn.close()
    return df

