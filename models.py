from __main__ import sqlquery

sqlquery("""
    CREATE TABLE "containers" (
        "id"	INTEGER UNIQUE,
        "uuid"	VARCHAR(255),
        "owner_api"	VARCHAR(255),
        PRIMARY KEY("id" AUTOINCREMENT)
    );
""")

sqlquery("""
    CREATE TABLE "settings" (
        "api_key"	VARCHAR(255)
    );
""")