CREATE TABLE entry_categories (
    feed TEXT NOT NULL,
    id TEXT NOT NULL,
    category TEXT NOT NULL,

    PRIMARY KEY (feed, id, category),
    FOREIGN KEY (feed, id) REFERENCES entries(feed, id) ON DELETE CASCADE
);
