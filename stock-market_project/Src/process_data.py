from database import get_connection
import pandas as pd
import numpy as np

def save_table(conn, df, table_name):
    temp_name = f"{table_name}_df"

    conn.register(temp_name, df)

    conn.sql(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM {temp_name}
    """)

def process_data():
    conn = get_connection()

    try:
        # Carrega os dados das tabelas de origem
        amex = conn.sql("SELECT * FROM amex_active").df()
        nasdaq = conn.sql("SELECT * FROM nasdaq_active").df()
        nyse = conn.sql("SELECT * FROM nyse_active").df()

        # Junta as três bolsas
        daily_data = (
            amex
            .merge(nasdaq, how="outer", on="Data")
            .merge(nyse, how="outer", on="Data")
        )

        # CONVERTE E ORDENA POR DATA
        daily_data["Data"] = pd.to_datetime(daily_data["Data"])
        daily_data = daily_data.sort_values("Data").reset_index(drop=True)

        # Filtra o período
        daily_data = daily_data[
            (daily_data["Data"] >= "2000-01-01") &
            (daily_data["Data"] < "2025-09-01")
        ]

        # Remove linhas onde todas as ações são NA (ignora a coluna Data)
        asset_cols = daily_data.columns.drop("Data")
        daily_data = daily_data.dropna(how="all", subset=asset_cols)

        # Remove colunas com mais de 90% de NA
        na_ratio = daily_data.isna().mean()
        cols_to_keep = na_ratio[na_ratio <= 0.9].index
        daily_data = daily_data[cols_to_keep]

        # Renomeia as colunas
        daily_data.columns = (
            daily_data.columns
            .str.replace("PU\najust p/ prov\nEm moeda orig\n", "", regex=False)
        )

        # Remove colunas cujo nome contém "."
        daily_data = daily_data.loc[:, ~daily_data.columns.str.contains(r"\.")]

        # Calcula os retornos logarítmicos diários
        cols = daily_data.select_dtypes(include=np.number).columns

        daily_data[cols] = np.log(
            daily_data[cols] /
            daily_data[cols].shift(1)
        )

        # Agregação mensal
        monthly_data = (
            daily_data
            .groupby(daily_data["Data"].dt.to_period("M"))[cols]
            .sum(min_count=1)
            .reset_index()
        )
        monthly_data["Data"] = monthly_data["Data"].astype(str)

        # Estatísticas descritivas
        numeric_monthly = monthly_data[cols]
        estats = pd.DataFrame({
            "Media": numeric_monthly.mean(),
            "Máximo": numeric_monthly.max(),
            "Mínimo": numeric_monthly.min(),
            "Mediana": numeric_monthly.median(),
            "Assimetria": numeric_monthly.skew(),
            "Kurtose": numeric_monthly.kurtosis(),
            "Devio Padrão": numeric_monthly.std()
        }).T.round(4)

        estats_to_db = estats.reset_index().rename(columns={"index": "Metrica"})

        # Formata a data diária para string antes de exportar ao SQL
        daily_data["Data"] = daily_data["Data"].dt.strftime("%Y-%m-%d")

        # --- monta asset_info comparando nomes já limpos ---
        def clean_cols(cols):
            return (
                pd.Index(cols)
                .str.replace("PU\najust p/ prov\nEm moeda orig\n", "", regex=False)
            )

        nasdaq_tickers = set(clean_cols(nasdaq.columns[1:]))
        nyse_tickers = set(clean_cols(nyse.columns[1:]))

        asset_info = pd.DataFrame(
            {"Ticker" : daily_data.columns[1:]}
        )
        asset_info["Exchange"] = np.where(
            asset_info["Ticker"].isin(nasdaq_tickers),
            "NASDAQ",
            np.where(
                asset_info["Ticker"].isin(nyse_tickers),
                "NYSE",
                "AMEX"
            )
        )

        corr = monthly_data.select_dtypes(include=np.number).corr()
        correlation_matrix = (
            corr
            .stack()
            .reset_index()
        )

        correlation_matrix.columns = [
            "Ticker1",
            "Ticker2",
            "Correlation"
        ]



        # Salva todas as tabelas no Banco de Dados SQL
        save_table(conn, daily_data, "daily_data")
        save_table(conn, monthly_data, "monthly_data")
        save_table(conn, estats_to_db, "estatisticas_mensais")
        save_table(conn, asset_info, "asset_info")
        save_table(conn, correlation_matrix, "correlation_matrix")

        print("Tabelas 'daily_data', 'monthly_data' e 'estatisticas_mensais' atualizadas no SQL com sucesso!")

    finally:
        conn.close()

if __name__ == "__main__":
    process_data()

