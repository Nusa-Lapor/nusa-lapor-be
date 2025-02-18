#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import psycopg2
from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nusa_lapor_backend.settings')

    # # Load environment variables from .env
    # load_dotenv()

    # # Fetch variables
    # USER = os.getenv("PROD_DATABASE_USER")
    # PASSWORD = os.getenv("PROD_DATABASE_PASSWORD")
    # HOST = os.getenv("PROD_DATABASE_HOST")
    # PORT = os.getenv("PROD_DATABASE_PORT")
    # DBNAME = os.getenv("PROD_DATABASE_NAME")

    try:
        from django.core.management import execute_from_command_line

        # # Connect to the database
        # try:
        #     connection = psycopg2.connect(
        #         user=USER,
        #         password=PASSWORD,
        #         host=HOST,
        #         port=PORT,
        #         dbname=DBNAME
        #     )
        #     print("Connection successful!")
            
        #     """EXAMPLE QUERY"""
        #     # # Create a cursor to execute SQL queries
        #     # cursor = connection.cursor()
            
        #     # # Example query
        #     # cursor.execute("SELECT NOW();")
        #     # result = cursor.fetchone()
        #     # print("Current Time:", result)

        #     # # Close the cursor and connection
        #     # cursor.close()
        #     connection.close()
        #     print("Connection closed.")
        #     # connection.close()
        #     # print("Connection closed.")

        # except Exception as e:
        #     print(f"Failed to connect: {e}")
            
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)



if __name__ == '__main__':
    main()
