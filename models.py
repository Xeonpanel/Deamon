from __main__ import sqlquery

sqlquery("""
    CREATE TABLE "containers" (
        "id"	INTEGER UNIQUE,
        "uuid"	VARCHAR(255),
        "user_token"	VARCHAR(255),
        PRIMARY KEY("id" AUTOINCREMENT)
    );
""")

sqlquery("""
    CREATE TABLE "settings" (
        "system_token"	VARCHAR(255)
    );
""")