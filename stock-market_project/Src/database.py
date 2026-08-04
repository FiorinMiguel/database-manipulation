from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "Data" / "database.duckdb"

def get_connection():
    return duckdb.connect(DB_PATH)