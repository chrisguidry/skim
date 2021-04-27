CREATE TABLE entry_creators (
    feed TEXT NOT NULL,
    id TEXT NOT NULL,
    creator TEXT NOT NULL,

    PRIMARY KEY (feed, id, creator),
    FOREIGN KEY (feed, id) REFERENCES entries(feed, id) ON DELETE CASCADE
);
