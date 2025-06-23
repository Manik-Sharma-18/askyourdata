#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from llama_cpp import Llama

# Load the GGUF model (change the path if different)
llm = Llama(
    model_path=r"C:\Users\Manik\AskYourData Project\models\sqlcoder-7b-2-q4_k_m.gguf",
    n_ctx=2048,
    n_threads=6,
    verbose=False
)

def translate_to_sql(question: str, schema: str) -> str:
    prompt = f"""You are an expert data analyst writing SQLite queries ONLY.
You are given a database schema. You must follow these rules:
- Only use table and column names from the schema
- Do NOT use PostgreSQL syntax like ILIKE, NULLS LAST, or LIMIT ALL
- Use only standard SQLite syntax (LIKE instead of ILIKE)
- Match case-sensitive table names exactly
- Always use table names in lowercase if that’s how they appear in schema
- Write simple, clean SELECT queries
- Do NOT alias table names unless absolutely necessary

Schema:
{schema}

Question: {question}
SQL:"""

    response = llm(prompt, max_tokens=256, stop=["\n\n", ";"])
    return response["choices"][0]["text"].strip()


# In[ ]:




