import pandas as pd
import psycopg2
from psycopg2 import extras

DB_CONFIG = {
    "host": "10.140.159.152",
    "port": 5432,
    "dbname": "stagingdb",
    "user": "admindb",
    "password": "admin"
}

CSV_FILE_PATH = "MEDIA_INSIGHTS.csv"
TABLE_NAME = "media_insights"

CSV_COLUMNS_TO_DB = [
    "ID",
    "LIKE_COUNT",
    "COMMENT_COUNT",
    "VIDEO_PHOTO_IMPRESSIONS",
    "VIDEO_PHOTO_REACH",
    "VIDEO_PHOTO_SAVED",
    "VIDEO_VIEWS",
    "CAROUSEL_ALBUM_ENGAGEMENT",
    "CAROUSEL_ALBUM_IMPRESSIONS",
    "CAROUSEL_ALBUM_REACH",
    "CAROUSEL_ALBUM_SAVED",
    "CAROUSEL_ALBUM_VIDEO_VIEWS",
    "STORY_IMPRESSIONS",
    "STORY_REACH",
    "NAVIGATION",
    "REEL_REACH",
    "REEL_SAVED",
    "VIDEO_PHOTO_ENGAGEMENT",
    "STORY_EXITS",
    "STORY_REPLIES",
    "STORY_TAPS_BACK",
    "STORY_TAPS_FORWARD",
    "STORY_SWIPE_FORWARD",
    "REEL_AGGREGATED_ALL_PLAYS_COUNT",
    "REEL_CLIPS_REPLAYS_COUNT",
    "REEL_COMMENTS",
    "REEL_LIKES",
    "REEL_PLAYS",
    "REEL_SHARES",
    "REEL_TOTAL_INTERACTIONS",
    "STORY_VIEWS",
    "REEL_VIEWS",
    "VIDEO_PHOTO_VIEWS",
    "VIDEO_PHOTO_SHARES",
    "CAROUSEL_ALBUM_SHARES",
    "CAROUSEL_ALBUM_VIEWS",
    "STORY_SHARES",
    "TIMESTAMP",
]


def upload_csv_to_postgres(csv_path, table_name, db_config, columns):
    try:

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
            print("CSV file kosong, tidak ada data untuk diupload.")
            return

        missing_cols = set(columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Kolom tidak ditemukan di CSV: {missing_cols}")

        df = df[columns]

        records = [tuple(row) for row in df.itertuples(index=False, name=None)]
        column_str = ",".join(columns)

        insert_query = f"""
            INSERT INTO media_insights (
                "ID",
                "LIKE_COUNT",
                "COMMENT_COUNT",
                "VIDEO_PHOTO_IMPRESSIONS",
                "VIDEO_PHOTO_REACH",
                "VIDEO_PHOTO_SAVED",
                "VIDEO_VIEWS",
                "CAROUSEL_ALBUM_ENGAGEMENT",
                "CAROUSEL_ALBUM_IMPRESSIONS",
                "CAROUSEL_ALBUM_REACH",
                "CAROUSEL_ALBUM_SAVED",
                "CAROUSEL_ALBUM_VIDEO_VIEWS",
                "STORY_IMPRESSIONS",
                "STORY_REACH",
                "NAVIGATION",
                "REEL_REACH",
                "REEL_SAVED",
                "VIDEO_PHOTO_ENGAGEMENT",
                "STORY_EXITS",
                "STORY_REPLIES",
                "STORY_TAPS_BACK",
                "STORY_TAPS_FORWARD",
                "STORY_SWIPE_FORWARD",
                "REEL_AGGREGATED_ALL_PLAYS_COUNT",
                "REEL_CLIPS_REPLAYS_COUNT",
                "REEL_COMMENTS",
                "REEL_LIKES",
                "REEL_PLAYS",
                "REEL_SHARES",
                "REEL_TOTAL_INTERACTIONS",
                "STORY_VIEWS",
                "REEL_VIEWS",
                "VIDEO_PHOTO_VIEWS",
                "VIDEO_PHOTO_SHARES",
                "CAROUSEL_ALBUM_SHARES",
                "CAROUSEL_ALBUM_VIEWS",
                "STORY_SHARES",
                "TIMESTAMP"
            )
            VALUES %s
        """

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE media_insights")
        extras.execute_values(cursor, insert_query, records)

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Berhasil upload {len(records)} rows ke tabel {table_name}")

    except Exception as e:
        print("Terjadi error:", e)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    upload_csv_to_postgres(
        csv_path=CSV_FILE_PATH,
        table_name=TABLE_NAME,
        db_config=DB_CONFIG,
        columns=CSV_COLUMNS_TO_DB
    )