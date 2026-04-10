import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="ai_assistant_db",
        user="postgres",
        password="Qwerty:29!03"
    )

    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            age INT
        );
    """)

    # Insert sample data
    cursor.execute("INSERT INTO users (name, age) VALUES (%s, %s)", ("Suchi", 22))

    conn.commit()

    print("✅ Table created & data inserted successfully!")

except Exception as e:
    print("❌ Error:", e)

finally:
    if conn:
        cursor.close()
        conn.close()