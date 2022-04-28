CREATE TABLE entries (
    feed TEXT NOT NULL,
    id TEXT NOT NULL,
    timestamp timestamptz NOT NULL,
    title TEXT NOT NULL,
    link TEXT NULL,
    body TEXT NULL,

    PRIMARY KEY (feed, id)
);
