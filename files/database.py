import psycopg2
import time
import json

# Database configuration
DB_HOST = 'YOUR_HOST'   #localhost
DB_PORT = 'YOUR_PORT'   #5432
DB_NAME = 'YOUR_USERNAME'
DB_USER = 'YOUR_USER'   #posgres
DB_PASSWORD = 'YOUR_PASSWORD'


# Connect to the PostgreSQL database
def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Create a table for users11 if it doesn't exist
def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        email VARCHAR(100) UNIQUE NOT NULL,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(50) NOT NULL,
                        keystroke_timing JSONB,
                        login_attempts INT DEFAULT 3,
                        reset_token VARCHAR(255)
                    );
                    
                    CREATE TABLE IF NOT EXISTS keystrokes (
                        login_time TIMESTAMP ,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        stored_keystrokes JSONB,
                        captured_keystrokes JSONB,
                        key_up_time FLOAT,
                        key_down_time FLOAT,
                        key_total_time FLOAT
                    );

                    CREATE TABLE IF NOT EXISTS Keystrokes_Data (
                        username VARCHAR(255),
                        H_key1 FLOAT,
                        DD_key1_key2 FLOAT,
                        UD_key1_key2 FLOAT,
                        H_key2 FLOAT,
                        DD_key2_key3 FLOAT,
                        UD_key2_key3 FLOAT,
                        H_key3 FLOAT,
                        DD_key3_key4 FLOAT,
                        UD_key3_key4 FLOAT,
                        H_key4 FLOAT,
                        DD_key4_key5 FLOAT,
                        UD_key4_key5 FLOAT,
                        H_key5 FLOAT,
                        DD_key5_key6 FLOAT,
                        UD_key5_key6 FLOAT,
                        H_key6 FLOAT,
                        DD_key6_key7 FLOAT,
                        UD_key6_key7 FLOAT,
                        H_key7 FLOAT,
                        DD_key7_key8 FLOAT,
                        UD_key7_key8 FLOAT,
                        H_key8 FLOAT,
                        Target VARCHAR(255)
                    )
    ''')
    conn.commit()
    conn.close()