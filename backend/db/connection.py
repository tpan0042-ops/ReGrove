import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

#establish connection to the database using the DATABASE_URL environment variable
def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])