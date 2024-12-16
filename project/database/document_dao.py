import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


def validate_env_vars():
    """Ensure all necessary environment variables are loaded"""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    for var in required_vars:
        if not os.getenv(var):
            print(f"Warning: Environment variable {var} is not set!")


def get_db_connection():
    """Create and return a database connection"""
    try:
        # Validate environment variables
        validate_env_vars()

        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'document_ocr')
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None


def save_document_data(data):
    """Save document data to database"""
    try:
        connection = get_db_connection()
        if connection is None:
            return False

        cursor = connection.cursor()

        query = """
            INSERT INTO documents 
            (document_type, full_name, id_number, date_of_birth, place_of_birth, expiry_date, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            data.get('document_type', ''),
            data.get('full_name', ''),
            data.get('id_number', ''),
            data.get('date_of_birth'),
            data.get('place_of_birth', ''),
            data.get('expiry_date'),
            data.get('address', '')
        )

        # Ensure no required fields are missing
        if not all(values):
            print("Error: Missing required fields in document data.")
            return False

        cursor.execute(query, values)
        connection.commit()
        print("Document data saved successfully.")
        return True

    except Error as e:
        print(f"Error saving document data: {e}")
        return False

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
