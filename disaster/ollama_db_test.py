import requests
import psycopg2
import re

# -----------------------------
# CONFIGURATION
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"

DB_CONFIG = {
    "dbname": "disaster_db ",  # removed extra space
    "user": "postgres",
    "password": "abbasi08",
    "host": "localhost",
    "port": "5432"
}

# -----------------------------
# TALK TO OLLAMA
# -----------------------------
def ask_ollama(prompt):
    payload = {
        "model": "llama3.1",
        "prompt": prompt,
        "stream": False
    }
    res = requests.post(OLLAMA_URL, json=payload)
    return res.json()["response"]

# -----------------------------
# RUN SQL ON POSTGIS
# -----------------------------
def run_postgis_query(sql):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# -----------------------------
# CLEAN SQL (Fix Ollama Mistakes)
# -----------------------------
def clean_sql(sql):
    # Remove markdown/code fences
    sql = sql.replace("```sql", "").replace("```", "").strip()

    # Merge accidental double WHERE into AND
    sql = re.sub(r";\s*WHERE", " AND", sql, flags=re.IGNORECASE)

    # Remove any accidental semicolons in middle of query
    parts = sql.split(";")
    if len(parts) > 1 and not sql.strip().endswith(";"):
        sql = parts[0]  # Keep only before the first semicolon

    return sql.strip()

# -----------------------------
# MAIN SPATIAL CHAT FUNCTION
# -----------------------------
def spatial_chat(user_question):
    # Step 1: Generate SQL
    llm_prompt = f"""
You are a GIS database assistant. 
Return ONLY a valid SQL query for my PostGIS database.
No explanations, no comments, no markdown.

Database tables:

earthquake_data(
    time INTEGER,  -- Unix timestamp
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    mag DOUBLE PRECISION,
    place TEXT,
    id TEXT
)

disaster_landslide(
    event_id INTEGER,
    event_title TEXT,
    event_description TEXT,
    location_description TEXT,
    location_accuracy TEXT,
    landslide_category TEXT,
    landslide_trigger TEXT,
    landslide_size TEXT,
    fatality_count INTEGER,
    injury_count INTEGER,
    event_import_id TEXT,
    country_name TEXT
)

hurricane_data(
    sid VARCHAR,
    number INTEGER,
    basin VARCHAR,
    subbasin VARCHAR,
    iso_time TIMESTAMP WITHOUT TIME ZONE,
    nature VARCHAR,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
)

Rules:
- Only query ONE table unless the user explicitly requests combining multiple datasets.
- Do NOT join earthquake_data, disaster_landslide, and hurricane_data unless there is a shared column name and meaning AND the user explicitly requests a join.
- For earthquakes:
    - `time` is a Unix timestamp — use `to_timestamp(time)` for date filtering.
    - Location = latitude, longitude → use `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)` for spatial queries.
- For hurricanes:
    - Location = lat, lon → use `ST_SetSRID(ST_MakePoint(lon, lat), 4326)` for spatial queries.
- For landslides:
    - Use location_description or country_name for location filtering.
- Avoid unnecessary subqueries.
- Use ILIKE for partial text matches.
- Use BETWEEN for date/time ranges.
- Return only plain SQL text. No ``` or markdown.

Question: {user_question}
"""
    raw_response = ask_ollama(llm_prompt).strip()

    # Extract only SQL that starts with SELECT or WITH
    match = re.search(r"(SELECT|WITH).*", raw_response, re.S | re.I)
    if match:
        sql_query = match.group(0).strip()
    else:
        sql_query = raw_response  # fallback

    # Final cleanup
    sql_query = clean_sql(sql_query)

    print("\n[Generated SQL]")
    print(sql_query)

    # Step 2: Run SQL
    try:
        results = run_postgis_query(sql_query)
        print("\n[Query Results]")
        for row in results:
            print(row)

        # Step 3: Human‑friendly answer
        answer_prompt = f"""
The user asked: "{user_question}"
The database returned these rows: {results}

Write a short, clear answer in plain English.
"""
        friendly_answer = ask_ollama(answer_prompt)
        print("\n[Chatbot Answer]")
        print(friendly_answer)

    except Exception as e:
        print("\n[ERROR Running SQL]")
        print(str(e))

# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":
    question = "Show all earthquakes in Lahore in 2023"
    spatial_chat(question)
