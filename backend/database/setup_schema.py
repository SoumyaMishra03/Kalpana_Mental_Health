# backend/database/setup_schema.py
from database.connection import get_db_connection

def create_modular_schema():
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    queries = [
        "CREATE SCHEMA IF NOT EXISTS core;",
        """
        CREATE TABLE IF NOT EXISTS core.users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            anonymized_alias VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS core.chat_sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES core.users(user_id),
            started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP WITH TIME ZONE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS core.message_logs (
            message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES core.chat_sessions(session_id),
            sender_type VARCHAR(50) CHECK (sender_type IN ('user', 'listener_agent', 'system')),
            message_text TEXT NOT NULL,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        "CREATE SCHEMA IF NOT EXISTS clinical;",
        """
        CREATE TABLE IF NOT EXISTS clinical.profiles (
            profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES core.chat_sessions(session_id),
            valence INT CHECK (valence >= 1 AND valence <= 10),
            arousal INT CHECK (arousal >= 1 AND arousal <= 10),
            primary_distress VARCHAR(255),
            risk_score INT GENERATED ALWAYS AS ((11 - valence) + arousal) STORED,
            evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        "CREATE SCHEMA IF NOT EXISTS triage;",
        """
        CREATE TABLE IF NOT EXISTS triage.assessments (
            assessment_id UUID DEFAULT gen_random_uuid(),
            profile_id UUID,
            risk_score INT NOT NULL,
            routing_decision VARCHAR(50) NOT NULL,
            assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (assessment_id, risk_score)
        ) PARTITION BY RANGE (risk_score);
        """,
        """
        CREATE TABLE IF NOT EXISTS triage.assessments_low_risk 
        PARTITION OF triage.assessments FOR VALUES FROM (2) TO (11);
        """,
        """
        CREATE TABLE IF NOT EXISTS triage.assessments_moderate_risk 
        PARTITION OF triage.assessments FOR VALUES FROM (11) TO (17);
        """,
        """
        CREATE TABLE IF NOT EXISTS triage.assessments_high_risk 
        PARTITION OF triage.assessments FOR VALUES FROM (17) TO (22);
        """,
        "CREATE SCHEMA IF NOT EXISTS matchmaking;",
        """
        CREATE TABLE IF NOT EXISTS matchmaking.support_groups (
            group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            distress_topic VARCHAR(255) NOT NULL,
            target_risk_level VARCHAR(20) CHECK (target_risk_level IN ('LOW', 'MODERATE')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS matchmaking.peer_connections (
            connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES core.users(user_id),
            group_id UUID REFERENCES matchmaking.support_groups(group_id),
            pinecone_vector_id VARCHAR(255),
            matched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]

    for q in queries:
        cursor.execute(q)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_modular_schema()