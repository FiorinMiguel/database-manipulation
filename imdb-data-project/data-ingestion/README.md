# IMDb SQLite Database

Project to build a SQLite database from IMDb `.tsv` files using R.

## Objective
Efficiently import large datasets while ensuring data integrity.

## Technologies
- R
- SQLite
- PowerShell
- DBI, RSQLite, readr, glue

## Methodology
- Create `IMDB.db`
- Chunked import (200,000 rows per batch)
- Convert `\N` to `NA`
- Reusable ingestion function

## Tables
- ratings  
- basics  
- principals  

## Validation
Row count comparison between `.tsv` files and SQLite (`SELECT COUNT(*)`).

##  Report

The full methodology, implementation details, and results are available in the PDF report:

 [View Report](imdb-sqlite-database-report.pdf)


