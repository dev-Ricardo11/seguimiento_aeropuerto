
import sys
import os
import pyodbc
from api import get_db_connection

# Add current dir to path to ensure we can import api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def reset_password(email, new_password):
    print(f"\n--- Resetting Password for: {email} ---")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print(f"1. Updating password for {email} to '{new_password}'...")
            
            # Update password using HASHBYTES
            cursor.execute("""
                UPDATE dbo.usuarios 
                SET [contraseña] = HASHBYTES('SHA2_256', ?) 
                WHERE email = ?
            """, (new_password, email))
            
            if cursor.rowcount > 0:
                print("✅ Password UPDATED successfully.")
                conn.commit()
            else:
                print("❌ User NOT FOUND. Password NOT updated.")

    except Exception as e:
        print(f"\n❌ Error during password reset: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email = "gramirez@expresoviajes.com"
    new_password = "800206979" 
    
    reset_password(test_email, new_password)
