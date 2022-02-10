ALTER TABLE `measurements`
    base_visible INTEGER NOT NULL DEFAULT 0,
    base_range_min REAL NOT NULL DEFAULT -1,
    base_range_max REAL NOT NULL
        CONSTRAINT base_min_max CHECK(base_range_min <= base_range_max)
        DEFAULT -1;