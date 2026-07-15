# Database connector and pooling class
import logging
import mysql.connector
from mysql.connector import pooling, Error
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT, handlers=[
    logging.FileHandler(config.LOG_FILE),
    logging.StreamHandler()
])
logger = logging.getLogger("Database")

class DatabaseManager:
    """Manages the MySQL connection pool and database transactions."""
    _pool = None

    @classmethod
    def initialize_pool(cls):
        """Initializes the MySQL connection pool if it does not exist."""
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="warehouse_pool",
                    pool_size=10,
                    pool_reset_mode='session',
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    database=config.DB_NAME
                )
                logger.info("Database connection pool initialized successfully.")
            except Error as e:
                logger.critical(f"Failed to initialize database connection pool: {e}")
                raise e

    @classmethod
    def get_connection(cls):
        """Gets a connection from the pool."""
        cls.initialize_pool()
        try:
            return cls._pool.get_connection()
        except Error as e:
            logger.error(f"Failed to retrieve connection from pool: {e}")
            raise e

    @classmethod
    def execute_query(cls, query, params=None):
        """Executes a SELECT query and returns the results."""
        conn = None
        cursor = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            logger.error(f"Error executing SELECT query: {e}\nQuery: {query}\nParams: {params}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @classmethod
    def execute_update(cls, query, params=None):
        """Executes an INSERT, UPDATE, or DELETE query and returns the row count or last insert ID."""
        conn = None
        cursor = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            affected_rows = cursor.rowcount
            return last_id if last_id else affected_rows
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error executing UPDATE/INSERT: {e}\nQuery: {query}\nParams: {params}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @classmethod
    def execute_transaction(cls, operations):
        """Executes a list of operations in a single transaction.
        
        operations: List of tuples (query_string, parameters_tuple)
        """
        conn = None
        cursor = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            conn.start_transaction()
            
            for query, params in operations:
                cursor.execute(query, params)
                
            conn.commit()
            return True
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Transaction failed, rolling back. Error: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
