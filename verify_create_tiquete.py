
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src', 'services'))

from api import create_tiquete, TiqueteCreate, get_db_connection
from datetime import datetime

def verify_creation():
    # Test Data 1: IDA
    tiquete_ida = TiqueteCreate(
        ds_records="TEST_REC_IDA",
        cd_tiquete="TEST_ID_IDA",
        ds_paxname="TEST PASSENGER IDA",
        dt_salida="2025-01-01T10:00:00",
        tipo_vuelo="IDA"
    )
    
    # Test Data 2: REG
    tiquete_reg = TiqueteCreate(
        ds_records="TEST_REC_REG",
        cd_tiquete="TEST_ID_REG", 
        ds_paxname="TEST PASSENGER REG",
        dt_salida="2025-01-15T15:00:00", # Will be mapped to dt_llegada in logic
        tipo_vuelo="REG"
    )

    print("Testing creation logic...")
    
    # 1. Test IDA Creation
    try:
        print("Creating IDA ticket...")
        result = create_tiquete(tiquete_ida)
        print(f"IDA Result: {result}")
    except Exception as e:
        print(f"IDA Creation Failed: {e}")

    # 2. Test REG Creation
    try:
        print("Creating REG ticket...")
        result = create_tiquete(tiquete_reg)
        print(f"REG Result: {result}")
    except Exception as e:
        print(f"REG Creation Failed: {e}")

    # 3. Verify in DB
    print("\nVerifying in Database...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check IDA
        cursor.execute("SELECT id_documento, dt_salida FROM dbo.VueloIDA WHERE id_documento = 'TEST_ID_IDA'")
        row_ida = cursor.fetchone()
        if row_ida:
            print(f"✅ Found in VueloIDA: {row_ida}")
            # Cleanup
            cursor.execute("DELETE FROM dbo.VueloIDA WHERE id_documento = 'TEST_ID_IDA'")
            print("Cleaned up IDA test record.")
        else:
            print("❌ NOT Found in VueloIDA")

        # Check REG
        cursor.execute("SELECT id_documento, dt_llegada FROM dbo.VueloREG WHERE id_documento = 'TEST_ID_REG'")
        row_reg = cursor.fetchone()
        if row_reg:
            print(f"✅ Found in VueloREG: {row_reg}")
            # Cleanup
            cursor.execute("DELETE FROM dbo.VueloREG WHERE id_documento = 'TEST_ID_REG'")
            print("Cleaned up REG test record.")
        else:
            print("❌ NOT Found in VueloREG")
            
        conn.commit()

if __name__ == "__main__":
    verify_creation()
