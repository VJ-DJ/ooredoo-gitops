
import os
import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "sslmode": "require",
    "connect_timeout": 5,
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200

@app.get("/db-check")
def db_check():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user")
                database, user = cur.fetchone()

        return jsonify(
            status="connected",
            database=database,
            user=user
        ), 200
    except Exception:
        app.logger.exception("Database connection failed")
        return jsonify(status="database connection failed"), 503

@app.route("/items", methods=["GET", "POST"])
def items():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sample_items (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                if request.method == "POST":
                    data = request.get_json(silent=True) or {}
                    name = data.get("name")

                    if not isinstance(name, str) or not name.strip():
                        return jsonify(error="name is required"), 400

                    cur.execute(
                        "INSERT INTO sample_items (name) VALUES (%s) RETURNING *",
                        (name.strip(),)
                    )
                    item = cur.fetchone()
                    return jsonify(item), 201

                cur.execute(
                    "SELECT * FROM sample_items ORDER BY id"
                )
                return jsonify(cur.fetchall()), 200

    except Exception:
        app.logger.exception("Items database operation failed")
        return jsonify(error="database operation failed"), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
