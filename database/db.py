# imports
import sqlite3

# Connect to database
conn = sqlite3.connect("lost_and_found.db")
cur = conn.cursor()

# Enable foreign keys
cur.execute("PRAGMA foreign_keys = ON;")

# DROP TABLES needed
cur.execute("DROP TABLE IF EXISTS Matches")
cur.execute("DROP TABLE IF EXISTS FoundPosts")
cur.execute("DROP TABLE IF EXISTS LostPosts")
cur.execute("DROP TABLE IF EXISTS Users")

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS Users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    role TEXT DEFAULT 'student' CHECK(role IN ('student', 'staff', 'admin')),
    date_joined DATE DEFAULT CURRENT_DATE
)
""")

# LOST POSTS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS LostPosts (
    lost_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT CHECK(category IN (
        'Electronics', 'Clothing', 'Accessories', 
        'Documents', 'Keys', 'Books', 'Other'
    )),
    description TEXT,
    date_lost DATE,
    last_seen_location TEXT,
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'matched', 'closed')),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
)
""")

# FOUND POSTS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS FoundPosts (
    found_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT CHECK(category IN (
        'Electronics', 'Clothing', 'Accessories',
        'Documents', 'Keys', 'Books', 'Other'
    )),
    description TEXT,
    date_found DATE,
    found_location TEXT,
    storage_location TEXT DEFAULT 'Campus Security Office',
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'available' CHECK(status IN ('available', 'matched', 'returned')),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
)
""")

# MATCHES TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS Matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lost_id TEXT NOT NULL,
    found_id TEXT NOT NULL,
    matched_by_user_id TEXT,
    date_matched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (lost_id) REFERENCES LostPosts(lost_id) ON DELETE CASCADE,
    FOREIGN KEY (found_id) REFERENCES FoundPosts(found_id) ON DELETE CASCADE,
    FOREIGN KEY (matched_by_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
)
""")

# INDEXES
cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_category ON LostPosts(category)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_status ON LostPosts(status)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_date ON LostPosts(date_lost)")

cur.execute("CREATE INDEX IF NOT EXISTS idx_found_category ON FoundPosts(category)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_found_status ON FoundPosts(status)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_found_date ON FoundPosts(date_found)")

cur.execute("CREATE INDEX IF NOT EXISTS idx_match_resolved ON Matches(resolved)")

# Save changes and close
conn.commit()
conn.close()

print("Database schema created successfully!")