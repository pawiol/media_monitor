import sqlite3

# name of db file
# assuming that db file is in the same catalogue as the main script
sqlite_file = 'mmonitor.db'


tvp_news = """
                CREATE TABLE tvp_news
                (
                id_ TEXT,
                epoch_app_start INTEGER,
                date_app_start TEXT,
                epoch_app_save INTEGER,
                date_app_save TEXT,
                mm_name TEXT,
                art_id INTEGER,
                art_route TEXT,
                art_route_txt TEXT,
                headline_txt TEXT,
                article_txt TEXT,
                art_route_change TEXT,
                art_route_txt_change TEXT,
                headline_change TEXT,
                art_txt_change TEXT,
                article_hash TEXT,
                article_version INTEGER,
                last_checkup INTEGER
                )
            """

# Connecting to the database file
connection = sqlite3.connect(sqlite_file)
cursor = connection.cursor()

# Creating tables
cursor.execute(tvp_news)

# commiting changes ans closing connection
connection.commit()
connection.close()
