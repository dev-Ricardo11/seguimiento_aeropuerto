
import sys
import os
import traceback

# Add current dir to path to ensure we can import api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api import get_db_connection, DB_CONFIG
    import pyodbc
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_login_query(email, password):
    print(f"\n--- Starting Debug for: {email} ---")
    
    # Print non-sensitive config
    safe_config = {k:v for k,v in DB_CONFIG.items() if k != 'password'}
    print(f"DB Config Loaded: {safe_config}")
    
    conn = None
    try:
        print("1. Attempting get_db_connection()...")
        # get_db_connection is a context manager but also returns conn if used manually, 
        # but here we use it as context manager as designed
        try:
            with get_db_connection() as conn:
                print("   Connection Successful!")
                
                cursor = conn.cursor()
                print("2. Cursor created.")
                
                query = """
                SELECT id, email, nombre_completo, rol
                FROM dbo.usuarios
                WHERE email = ? 
                AND [contraseña] = HASHBYTES('SHA2_256', ?)
                """
                
                print("3. Executing Query...")
                print(f"   Query: {query.strip()}")
                print(f"   Params: ({email}, '******')")
                
                cursor.execute(query, (email, password))
                print("   Query Executed Successfully.")
                
                row = cursor.fetchone()
                if row:
                    print(f"4. Result: User found! ID: {row[0]}")
                else:
                    print("4. Result: No user found (Invalid credentials or user does not exist).")
                    
        except Exception:
            # We catch here to trace the inner block
            raise

    except Exception as e:
        print("\n❌ CRASH DETECTED ❌")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\nFull Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    # Using the email from the screenshot
    test_email = "gramirez@expresoviajes.com"
    test_password = "TestPassword123" 
    
    test_login_query(test_email, test_password)
