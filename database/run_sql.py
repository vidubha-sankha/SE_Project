import sqlite3


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
    CREATE TABLE IF NOT EXISTS road_damage_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_filename VARCHAR(255) NOT NULL,
        image_path VARCHAR(500) NOT NULL,
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL,
        location_name VARCHAR(500),
        prediction_class VARCHAR(50) NOT NULL,
        confidence_score FLOAT NOT NULL,
        severity VARCHAR(50),
        damage_type VARCHAR(100),
        description TEXT,
        reported_by VARCHAR(100),
        status VARCHAR(50) DEFAULT 'pending',
        priority VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    run_query(db_file, sql_query)

    # Adding indexes separately because run_query uses cursor.execute which only runs one statement at a time.
    # To run multiple, we use executescript, or we just run them one by one.
    run_query(db_file, "CREATE INDEX IF NOT EXISTS idx_status ON road_damage_reports(status);")
    run_query(db_file, "CREATE INDEX IF NOT EXISTS idx_severity ON road_damage_reports(severity);")
    run_query(db_file, "CREATE INDEX IF NOT EXISTS idx_prediction ON road_damage_reports(prediction_class);")
