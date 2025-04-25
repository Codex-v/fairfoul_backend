import sqlite3

# Create or connect to a database
conn = sqlite3.connect('example.db')  # This creates a file named 'example.db' in the current directory
cursor = conn.cursor()

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
''')

# Insert sample data
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Alice", "alice@example.com"))
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Bob", "bob@example.com"))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and table created, sample data inserted.")
