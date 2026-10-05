import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def get_engine():
    url = (f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
           f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
    return create_engine(url)

if __name__ == "__main__":
    with get_engine().connect() as conn:
        print(conn.execute(text("SELECT schema_name FROM information_schema.schemata "
                                "WHERE schema_name IN ('raw','staging','mart')")).fetchall())