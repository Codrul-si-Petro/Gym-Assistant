import psycopg2
import os

def delete_test_user(username: str):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("DELETE FROM authentication_user WHERE username = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()
