CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY NOT NULL,
    feed TEXT NOT NULL UNIQUE,
    title TEXT NULL,
    site TEXT NULL,
    icon BLOB NULL
);
