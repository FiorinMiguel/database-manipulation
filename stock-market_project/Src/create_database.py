import pandas as pd
from pathlib import Path

from database import get_connection

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "Data" / "Raw"

def duckdb_create(xlsx, conn):

    tabela = xlsx.stem

    pd.read_excel(
        xlsx,
        skiprows=3,
        na_values=["", "-"]
    ).to_sql(
        tabela,
        conn,
        if_exists="replace",
        index=False
    )

def create_database():

    conn = get_connection()

    try:

        for arquivo in RAW_DIR.glob("*.xlsx"):
            duckdb_create(arquivo, conn)

    finally:
        conn.close()


if __name__ == "__main__":
    create_database()

