import mysql.connector

# Connect to DB
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # change this
        database="ai_bot"  # change if needed
    )
    cursor = db.cursor()
    print("Database connected successfully.")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
    exit()

cursor.execute("SELECT * FROM command_history ORDER BY id DESC LIMIT 20")

results = cursor.fetchall()

print("\n=== Command History ===\n")
for id, command, timestamp in results:
    print(f"{timestamp} ➤ {command}")
