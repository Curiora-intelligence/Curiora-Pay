import psycopg as sql,pandas as pd # Note: This is Psycopg 3, which supports native async
import os,asyncio
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
async def setup_database_async():
    # Establish an asynchronous connection
    con = await sql.AsyncConnection.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port"),autocommit=True)
    
    # Create an async cursor
    async with con.cursor() as cursor:
        # Users Table
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT NOT NULL,
                userid TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                balance NUMERIC(15, 2) DEFAULT 0.00,
                date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                cibil_score INTEGER DEFAULT -1
            )
        ''')
        
        # Transactions Table
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                transactionid TEXT NOT NULL UNIQUE,
                sender_username TEXT NOT NULL,
                sender_acc TEXT NOT NULL,
                receiver_acc TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                amount NUMERIC(15, 2) NOT NULL,
                status TEXT DEFAULT 'pending',
                date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                note TEXT DEFAULT 'NULL',
                method TEXT DEFAULT 'internal_transfer'
            )
        ''')
        
    await con.close()
# asyncio.run(setup_database_async())
# print("Database tables created successfully!")
