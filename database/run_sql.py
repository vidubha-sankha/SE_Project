import sqlite3
import sys

def run_query(db_path, query):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Commit changes (for INSERT, UPDATE, DELETE, CREATE)
        conn.commit()
        
        # Fetch results if it's a SELECT query
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            print("Query Results:")
            for row in results:
                print(row)
        else:
            print("✅ Query executed successfully!")
            
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_file = "road_damage.db"
    
    # Replace the query below with your actual SQL query
    sql_query = """
    CREATE TABLE IF NOT EXISTS type_affinity_demo (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        description TEXT,
        price FLOAT,
        score REAL,
        created_at DATETIME,
        image BLOB
    );
    """
    
    run_query(db_file, sql_query)
