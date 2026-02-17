import pandas as pd
from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

logger = setup_logger("view_data")

def view_scoring_logs():
    try:
        db = DatabaseManager()
        query = "SELECT id, bank_name, result_status, monthly_payment, interest_rate, scraped_at, profile_data FROM scoring_logs ORDER BY id DESC;"
        
        with db.conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()

        if not data:
            logger.info("No records found in 'scoring_logs'.")
            return

        df = pd.DataFrame(data, columns=columns)
        
        # Extract 'loan_type' from profile_data if available
        df['loan_type'] = df['profile_data'].apply(lambda x: x.get('loan_type', 'N/A') if isinstance(x, dict) else 'N/A')
        
        # Adjust display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', 30)
        
        print("\n=== Scoring Logs (Top 20) ===")
        # Reorder columns to show loan_type near the front
        cols_to_show = ['id', 'bank_name', 'loan_type', 'result_status', 'monthly_payment', 'scraped_at']
        print(df[cols_to_show].head(20))
        print("\n=============================")
        
        # Show one full profile data example
        print("\n=== Example Profile Data (ID: 1) ===")
        if not df.empty:
            print(df.iloc[0]['profile_data'])
        print("=============================\n")

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    view_scoring_logs()
