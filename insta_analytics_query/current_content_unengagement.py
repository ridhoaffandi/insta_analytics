import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

SOURCE_DB_CONFIG = {
    "host": "10.140.159.152",
    "port": 5432,
    "dbname": "intermediatedb",
    "user": "admindb",
    "password": "admin"
}
CSV_OUTPUT_PATH = "current_content_unengagement.csv"

SOURCE_SQL = """
select *
from
(select distinct 
	ir."ID",
	ir."CREATED_TIME",
	ir."USER_ID",
	ir."MEDIA_TYPE",
	ir."MEDIA_PRODUCT_TYPE",
	SUM(ir."REEL_VIEWS")-SUM(ir."REEL_TOTAL_INTERACTIONS") as "UNENGAGEMENT"
	from insta_reel ir
	group by
	ir."ID",ir."CREATED_TIME",ir."USER_ID",ir."MEDIA_TYPE",ir."MEDIA_PRODUCT_TYPE"
	order by ir."USER_ID",ir."ID" asc) as ir
union 
(select distinct 
	ia."ID",
	ia."CREATED_TIME",
	ia."USER_ID",
	ia."MEDIA_TYPE",
	ia."MEDIA_PRODUCT_TYPE",
	SUM(ia."CAROUSEL_ALBUM_VIEWS")-SUM(ia."CAROUSEL_ALBUM_ENGAGEMENT") as "UNENGAGEMENT"
	from insta_album ia
	group by
	ia."ID",ia."CREATED_TIME",ia."USER_ID",ia."MEDIA_TYPE",ia."MEDIA_PRODUCT_TYPE"
	order by ia."USER_ID",ia."ID" asc)
union
(select distinct 
	ip."ID",
	ip."CREATED_TIME",
	ip."USER_ID",
	ip."MEDIA_TYPE",
	ip."MEDIA_PRODUCT_TYPE",
	SUM(ip."VIDEO_PHOTO_VIEWS")-SUM(ip."VIDEO_PHOTO_ENGAGEMENT") as "UNENGAGEMENT"
	from insta_photo ip
	group by
	ip."ID",ip."CREATED_TIME",ip."USER_ID",ip."MEDIA_TYPE",ip."MEDIA_PRODUCT_TYPE"
	order by ip."USER_ID",ip."ID" asc)
	order by "USER_ID","CREATED_TIME","ID" asc
"""

# =========================
# FUNCTION: SOURCE QUERY → CSV
# =========================
def extract_query_to_csv(sql, csv_path, db_config):
    conn = psycopg2.connect(**db_config)
    df = pd.read_sql(sql, conn)
    conn.close()

    if df.empty:
        print("Query source tidak menghasilkan data.")
        return False

    df.to_csv(csv_path, index=False)
    print(f"Extract {len(df)} rows ke {csv_path}")
    return True

TARGET_DB_CONFIG = {
    "host": "10.140.159.152",
    "port": 5432,
    "dbname": "insta_analyticdb",
    "user": "admindb",
    "password": "admin"
}
INTERMEDIATE_TABLE = "current_content_unengagement"

def upload_csv_to_postgres(csv_path, table_name, db_config):
    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False)

    df = df.replace(
        to_replace=r"^\s*(nan|NULL|null|NaN|NAN)?\s*$",
        value=None,
        regex=True
    )

    df = df.where(pd.notnull(df), None)

    if df.empty:
        print("CSV kosong, skip upload.")
        return

    records = [tuple(row) for row in df.itertuples(index=False, name=None)]
    columns = ",".join(df.columns)

    insert_query = f"""
       INSERT INTO current_content_unengagement (
            "ID",
	        "CREATED_TIME",
	        "USER_ID",
	        "MEDIA_TYPE",
	        "MEDIA_PRODUCT_TYPE",
	        "UNENGAGEMENT")
            VALUES %s
    """

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE current_content_unengagement")
    execute_values(cursor, insert_query, records)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Upload {len(records)} rows ke tabel {table_name} berhasil")


# =========================
# MAIN PIPELINE
# =========================
if __name__ == "__main__":
    success = extract_query_to_csv(
        sql=SOURCE_SQL,
        csv_path=CSV_OUTPUT_PATH,
        db_config=SOURCE_DB_CONFIG
    )
    if success:
        upload_csv_to_postgres(
            csv_path=CSV_OUTPUT_PATH,
            table_name=INTERMEDIATE_TABLE,
            db_config=TARGET_DB_CONFIG
        )
