import sqlite3

# name of db file
# assuming that db file is in the same catalogue as the main script
sqlite_file = 'news_diff.db'


tvp_news = """
                CREATE TABLE tvp_news
                (
                id_ TEXT,
                epoch_app_start INTEGER,
                date_app_start TEXT,
                epoch_app_save INTEGER,
                date_app_save TEXT,
                page TEXT,
                art_id INTEGER,
                art_route TEXT,
                art_txt TEXT,
                change TEXT
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
