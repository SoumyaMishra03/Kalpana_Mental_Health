# backend/database/setup_pgvector.py
import psycopg2
import os

def setup_vector_schema():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "root123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    conn.autocommit = True
    cursor = conn.cursor()

    queries = [
        "CREATE EXTENSION IF NOT EXISTS vector;",
        "CREATE SCHEMA IF NOT EXISTS matchmaking;",
        """
        CREATE TABLE IF NOT EXISTS matchmaking.peer_groups (
            group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            trauma_type VARCHAR(255) NOT NULL,
            description TEXT,
            embedding VECTOR(768)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS matchmaking.user_vectors (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID,
            last_embedding VECTOR(768),
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    for q in queries:
        cursor.execute(q)
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup_vector_schema()