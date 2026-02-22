# backend/database/vectorize_datasets.py
import os
import psycopg2
from psycopg2.extras import execute_values
from langchain_community.embeddings import OllamaEmbeddings

# 

def vectorize_datasets():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "root123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchmaking.dataset_vectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_name VARCHAR(255),
            text_content TEXT,
            self_harm INT,
            harming_others INT,
            reference_to_harm INT,
            embedding VECTOR(768)
        );
    """)

    datasets = ["ar_labeled", "arc_labeled", "few_shot_labeled", "harm_train", "mental_health"]
    embeddings_model = OllamaEmbeddings(model="nomic-embed-text")

    for dataset in datasets:
        try:
            cursor.execute(f"SELECT text, self_harm, harming_others, reference_to_harm FROM {dataset} WHERE text IS NOT NULL;")
            records = cursor.fetchall()
            
            if not records:
                continue

            texts = [str(record[0]) for record in records]
            
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_records = records[i:i + batch_size]
                
                vectors = embeddings_model.embed_documents(batch_texts)
                
                data_list = []
                for record, vector in zip(batch_records, vectors):
                    data_list.append((
                        dataset,
                        str(record[0]),
                        int(record[1]) if record[1] else 0,
                        int(record[2]) if record[2] else 0,
                        int(record[3]) if record[3] else 0,
                        vector
                    ))

                execute_values(
                    cursor,
                    """
                    INSERT INTO matchmaking.dataset_vectors 
                    (dataset_name, text_content, self_harm, harming_others, reference_to_harm, embedding) 
                    VALUES %s
                    """,
                    data_list
                )
        except Exception:
            continue

    cursor.close()
    conn.close()

if __name__ == "__main__":
    vectorize_datasets()