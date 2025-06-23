#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from llama_cpp import Llama

# Load the GGUF model (change the path if different)
llm = Llama(
    model_path="models/sqlcoder-7b-2-q4_k_m.gguf",
    n_ctx=2048,
    n_threads=6,  # adjust based on your CPU
    verbose=False
)

def translate_to_sql(question: str, schema: str) -> str:
    prompt = (
        f"You are a SQLite expert. Given the following schema:\n\n"
        f"{schema}\n\n"
        f"Write a SQL SELECT query to answer this question:\n"
        f"Question: {question}\nSQL:"
    )

    output = llm(prompt, max_tokens=256, stop=["\n\n", ";"])
    sql = output["choices"][0]["text"].strip()

    if not sql.lower().startswith("select"):
        raise ValueError(f"⚠️ Invalid SQL: {sql}")
    return sql


# In[ ]:




