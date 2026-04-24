from langchain.tools import tool
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="c_details"
    )

@tool
def sql_executor(sql_query: str):
    """
    Executes a read-only SQL SELECT query on the college database.
    """

    print(f"Tool called of query:{sql_query}")

    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
    if any(word in sql_query.lower() for word in forbidden):
        return "❌ Only SELECT queries are allowed."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No results found."

    return rows