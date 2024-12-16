import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def validate_env_vars():
    """Ensure all necessary environment variables are loaded"""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    for var in required_vars:
        if not os.getenv(var):
            logger.warning(f"Environment variable {var} is not set!")

def init_database():
    try:
        # Validate environment variables
        validate_env_vars()

        # Connect to the database
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'document_ocr')
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Create documents table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_type VARCHAR(50),
                    full_name VARCHAR(255),
                    id_number VARCHAR(50),
                    date_of_birth DATE,
                    place_of_birth VARCHAR(255),
                    expiry_date DATE,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()
            logger.info(f"Database {os.getenv('DB_NAME')} initialized successfully")
            return True

    except Error as e:
        logger.error(f"Error initializing database: {e}")
        return False

    finally:
        # Ensure cursor and connection are properly closed
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logger.debug("Database connection closed.")
