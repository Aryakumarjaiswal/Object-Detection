from datetime import datetime
from typing import Dict, Any
from app.config.database import DatabaseConfig

class InspectionDBService:
    def __init__(self):
        self.db_config = DatabaseConfig()

    def create_tables(self):
        """Create the necessary tables if they don't exist"""
        connection = self.db_config.get_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspection_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    has_dust BOOLEAN,
                    has_tear BOOLEAN,
                    has_stain BOOLEAN,
                    is_broken BOOLEAN,
                    is_crack BOOLEAN,
                    general_description TEXT,
                    created_at DATETIME
                )
            """)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def save_inspection_result(self, result: Dict[str, Any]) -> bool:
        """
        Save inspection result to database
        
        Args:
            result: Dictionary containing inspection results
            
        Returns:
            bool: True if successful, False otherwise
        """
        connection = self.db_config.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO inspection_results 
                (has_dust, has_tear, has_stain, is_broken, is_crack, 
                general_description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                result['has_dust'],
                result['has_tear'],
                result['has_stain'],
                result['is_broken'],
                result['is_crack'],
                result['general_description'],
                datetime.now()
            )
            
            cursor.execute(query, values)
            connection.commit()
            return True
            
        except Exception as e:
            print(f"Error saving inspection result: {str(e)}")
            return False
            
        finally:
            cursor.close()
            connection.close()
