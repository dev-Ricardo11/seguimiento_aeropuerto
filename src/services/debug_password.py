
import sys
import os
import pyodbc
from api import get_db_connection, DB_CONFIG

# Add current dir to path to ensure we can import api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def inspect_user(email, password_input):
    print(f"\n--- Inspecting User: {email} ---")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Check if user exists (ignoring password)
            print("1. Checking if user exists...")
            cursor.execute("SELECT id, email, nombre_completo, [contraseña] FROM dbo.usuarios WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                print("❌ User NOT FOUND in database.")
                return
            
            print(f"✅ User FOUND: ID={user[0]}, Name={user[2]}")
            stored_hash = user[3]
            print(f"   Stored Hash (bytes): {stored_hash.hex() if stored_hash else 'None'}")
            
            # 2. Check hash generation
            print("\n2. Comparing Hashes...")
            # We use a separate query to let SQL Server compute the hash of the input, 
            # to see exactly what HASHBYTES('SHA2_256', ?) produces for this input
            cursor.execute("SELECT HASHBYTES('SHA2_256', ?)", (password_input,))
            computed_hash_row = cursor.fetchone()
            computed_hash = computed_hash_row[0]
            
            print(f"   Input Password: {password_input}")
            print(f"   Computed Hash (bytes): {computed_hash.hex() if computed_hash else 'None'}")
            
            if stored_hash == computed_hash:
                print("✅ Hashes MATCH using SQL HASHBYTES!")
            else:
                print("❌ Hashes DO NOT MATCH.")

    except Exception as e:
        print(f"\n❌ Error during inspection: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email = "gramirez@expresoviajes.com"
    test_password = "TestPassword123" # Placeholder, I don't know the real one, but I need to ask the user or use a dummy if I can't ask.
    # Wait, I shouldn't guess the password. 
    # But the user entered '800206979' in the screenshot? No, that looks like a password field masked, 
    # but the placeholder text says '800...'. Wait, the screenshot has '800206979' visible? 
    # Ah, the screenshot shows 'Contraseña' field with dots, but wait, looking closely at the previous screenshot...
    # The latest screenshot shows dots "...".
    # However, in the first screenshot (Step 0), the input was "gramirez@expresoviajes.com" and dots.
    # In Step 40 screenshot, user entered '800206979' in the password field but with the eye icon toggled? 
    # No, it looks like text. Let me double check the OCR or look closer.
    # Actually, often users put the password in the screenshot if they unmask it.
    # In screenshot of Step 40, the text '800206979' is visible in the password field. 
    # I will assume that is the password they are trying to use.
    
    real_password_attempt = "800206979"
    
    inspect_user(test_email, real_password_attempt)
