"""
This script is a tool to be used when we want to quickly copy tables from one environment to another
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
import argparse

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env.dev')
dev_env = dotenv_values(BASE_DIR / '.env.dev')

dev_db_url = dev_env["DATABASE_URL"]

load_dotenv(BASE_DIR / '.env.prod', override=True)
prod_env = dotenv_values(BASE_DIR / '.env.prod')
prod_db_url = prod_env["DATABASE_URL"]

dev_engine = create_engine(dev_db_url)
prod_engine = create_engine(prod_db_url)

# test connection
try:
    with dev_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print(f"Dev DB connection failed: {e}")

try:
    with prod_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print(f"Prod DB connection failed: {e}")

# define cli arg
parser = argparse.ArgumentParser()
parser.add_argument(
        "--source",
        choices=["dev", "prod"],
        required=True,
        help="Source environment to copy tables from"
        )

parser.add_argument(
        "--target",
        choices=["dev", "prod"],
        required=True,
        help="Source environment to copy tables from"
        )

parser.add_argument(
    "--tables",
    nargs="+",  # allows multiple table names
    required=True,
    help="List of table names to sync"
)

args = parser.parse_args()

if args.source == args.target:
    raise ValueError("\033[91mSource and target environments must be different\033[0m")
# map engines 
engine_map={"dev": dev_engine, "prod": prod_engine}

source_engine = engine_map[args.source]
target_engine = engine_map[args.target]

# copy
for table_name in args.tables:
    print(f"Syncing table {table_name} from {args.source} to {args.target}...")

    df = pd.read_sql_table(table_name, source_engine)

    with target_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))

    df.to_sql(table_name, target_engine, if_exists="append", index=False)


    print(f"\033[92mTable {table_name} synced successfully\033[0m")
