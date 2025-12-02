import sqlite3 as sql

DB = "lost_and_found.db"

def get_lost_posts():
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM LostPosts")
    rows = cursor.fetchall()
    connection.close()

    lost_posts = []
    for row in rows:
        lost_posts.append({
            "lost_id": row[0],
            "user_id": row[1],
            "item_name": row[2],
            "category": row[3],
            "description": row[4],
            "date_lost": row[5],
            "last_seen_location": row[6],
            "date_posted": row[7],
            "status": row[8]
        })
    return lost_posts


def get_lost_post(lost_id: str):
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
    row = cursor.fetchone()
    connection.close()

    if row:
        return {
            "lost_id": row[0],
            "user_id": row[1],
            "item_name": row[2],
            "category": row[3],
            "description": row[4],
            "date_lost": row[5],
            "last_seen_location": row[6],
            "date_posted": row[7],
            "status": row[8]
        }
    return None


def add_lost_post(lost_id: str, user_id: str, item_name: str,
                  category: str, description: str,
                  date_lost: str, last_seen_location: str):

    connection = sql.connect(DB)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO LostPosts (lost_id, user_id, item_name, category,
                               description, date_lost, last_seen_location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lost_id, user_id, item_name, category,
          description, date_lost, last_seen_location))

    connection.commit()
    connection.close()


def delete_lost_post(lost_id: str):
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM LostPosts WHERE lost_id = ?", (lost_id,))
    connection.commit()
    connection.close()


def get_found_posts():
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM FoundPosts")
    rows = cursor.fetchall()
    connection.close()

    found_posts = []
    for row in rows:
        found_posts.append({
            "found_id": row[0],
            "user_id": row[1],
            "item_name": row[2],
            "category": row[3],
            "description": row[4],
            "date_found": row[5],
            "found_location": row[6],
            "storage_location": row[7],
            "date_posted": row[8],
            "status": row[9]
        })
    return found_posts


def get_found_post(found_id: str):
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
    row = cursor.fetchone()
    connection.close()

    if row:
        return {
            "found_id": row[0],
            "user_id": row[1],
            "item_name": row[2],
            "category": row[3],
            "description": row[4],
            "date_found": row[5],
            "found_location": row[6],
            "storage_location": row[7],
            "date_posted": row[8],
            "status": row[9]
        }
    return None


def add_found_post(found_id: str, user_id: str, item_name: str,
                   category: str, description: str,
                   date_found: str, found_location: str,
                   storage_location: str = "Campus Security Office"):

    connection = sql.connect(DB)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO FoundPosts (found_id, user_id, item_name, category,
                                description, date_found, found_location,
                                storage_location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (found_id, user_id, item_name, category,
          description, date_found, found_location, storage_location))

    connection.commit()
    connection.close()


def delete_found_post(found_id: str):
    connection = sql.connect(DB)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM FoundPosts WHERE found_id = ?", (found_id,))
    connection.commit()
    connection.close()

print("Database module loaded.")


"""
testing code
"""

if __name__ == "__main__":
    # Add a lost post
    add_lost_post("lost123", "user100", "Wallet", "Accessories",
                  "Black leather wallet", "2024-06-15", "Library")

    # Retrieve and print lost posts
    lost_posts = get_lost_posts()
    print("Lost Posts:", lost_posts)

    # Add a found post
    add_found_post("found123", "user100", "Keys", "Keys",
                   "Set of car keys with a red keychain", "2024-06-16", "Cafeteria")

    # Retrieve and print found posts
    found_posts = get_found_posts()
    print("Found Posts:", found_posts)
