CREATE TABLE "containers" (
    "id"	INTEGER UNIQUE,
    "uuid"	VARCHAR(255),
    "user_token"	VARCHAR(255),
    "port"	VARCHAR(255),
    "memory"	VARCHAR(255),
    PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "settings" (
    "system_token"	VARCHAR(255)
);