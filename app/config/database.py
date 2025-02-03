from mysql.connector import connect
from mysql.connector.connection import MySQLConnection

class DatabaseConfig:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""  # Set your MySQL password here
        self.database = "inspection_db"

    def get_connection(self) -> MySQLConnection:
        return connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
