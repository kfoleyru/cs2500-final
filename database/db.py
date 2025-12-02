import sqlite3 as sql

DB = "lost_and_found.db"

def get_connection():
    conn = sql.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

#USERS
def add_user(user_id: str, name: str, email: str, phone: str = None, role: str = "student"):
    """
    Adds a new user to the Users table.
    Includes full error handling for: duplicate user_idduplicate email, invalid role
    """
    try:
        connection = sql.connect(DB)
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO Users (user_id, name, email, phone, role)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, email, phone, role))

        connection.commit()
        return True, "User successfully added."

    except sql.IntegrityError as e:
        # SQLite constraint violations (UNIQUE, CHECK, FOREIGN KEY)
        if "UNIQUE constraint failed: Users.email" in str(e):
            return False, "Error: Email is already registered."
        elif "UNIQUE constraint failed: Users.user_id" in str(e):
            return False, "Error: This user ID already exists."
        elif "CHECK constraint failed" in str(e):
            return False, "Error: Invalid role. Must be student/staff/admin."
        else:
            return False, f"Integrity error: {e}"

    except Exception as e:
        return False, f"Unknown error: {e}"

    finally:
        connection.close()


def get_all_users():
    """
    Retrieves a list of all users from the Users table.
    This is used by main.py to check if any accounts exist.
    """
    users = []
    conn = None
    try:
        conn = get_connection()
        # Allows accessing columns by name instead of index
        conn.row_factory = sql.Row
        cur = conn.cursor()

        # Select key user details
        cur.execute("SELECT user_id, name, email, role, date_joined FROM Users")

        # Convert sql.Row objects to standard dictionaries
        users = [dict(row) for row in cur.fetchall()]

    except Exception as e:
        print("ERROR retrieving all users:", e)
        # Note: We return an empty list on error, which is appropriate for a getter function.
    finally:
        # Ensure connection is closed if it was successfully opened
        if conn:
            conn.close()
    return users
#POSTS
def get_lost_posts():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM LostPosts")
        rows = cur.fetchall()
        return [
            {
                "lost_id": row[0],
                "user_id": row[1],
                "item_name": row[2],
                "category": row[3],
                "description": row[4],
                "date_lost": row[5],
                "last_seen_location": row[6],
                "date_posted": row[7],
                "status": row[8]  # should be 'open' or 'matched'
            }
            for row in rows
        ]
    except sql.Error as e:
        print("Error retrieving lost posts:", e)
        return []
    finally:
        if conn:
            conn.close()


def get_lost_post(lost_id: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
        row = cur.fetchone()
        if not row:
            return None
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
    except sql.Error as e:
        print("Error retrieving lost post:", e)
        return None
    finally:
        if conn:
            conn.close()


def add_lost_post(lost_id, user_id, item_name, category,
                  description, date_lost, last_seen_location):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO LostPosts (lost_id, user_id, item_name, category,
                description, date_lost, last_seen_location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lost_id, user_id, item_name, category,
              description, date_lost, last_seen_location))

        conn.commit()
    except sql.Error as e:
        print("Error adding lost post:", e)
    finally:
        if conn:
            conn.close()


def delete_lost_post(lost_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM LostPosts WHERE lost_id = ?", (lost_id,))
        conn.commit()
    except sql.Error as e:
        print("Error deleting lost post:", e)
    finally:
        if conn:
            conn.close()


def get_found_posts():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM FoundPosts")
        rows = cur.fetchall()
        return [
            {
                "found_id": row[0],
                "user_id": row[1],
                "item_name": row[2],
                "category": row[3],
                "description": row[4],
                "date_found": row[5],
                "found_location": row[6],
                "storage_location": row[7],
                "date_posted": row[8],
                "status": row[9]  # available, matched
            }
            for row in rows
        ]
    except sql.Error as e:
        print("Error retrieving found posts:", e)
        return []
    finally:
        if conn:
            conn.close()


def add_found_post(found_id, user_id, item_name, category,
                   description, date_found, found_location,
                   storage_location="Campus Security Office"):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO FoundPosts (found_id, user_id, item_name, category,
                description, date_found, found_location, storage_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (found_id, user_id, item_name, category, description,
              date_found, found_location, storage_location))

        conn.commit()
    except sql.Error as e:
        print("Error adding found post:", e)
    finally:
        if conn:
            conn.close()


def delete_found_post(found_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM FoundPosts WHERE found_id = ?", (found_id,))
        conn.commit()
    except sql.Error as e:
        print("Error deleting found post:", e)
    finally:
        if conn:
            conn.close()


"""
Admin Tools
"""
def admin_match_items(lost_id: str, found_id: str, admin_user_id: str, notes: str = ""):
    """
    Creates a match between a lost and found item.
    Sets statuses to 'matched'.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Insert match
        cur.execute("""
            INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
            VALUES (?, ?, ?, ?)
        """, (lost_id, found_id, admin_user_id, notes))

        # Update statuses
        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit()
        print("Items matched successfully!")

    except sql.IntegrityError as e:
        print("ERROR: Matching failed:", e)
    finally:
        conn.close()


def admin_resolve_match(match_id: int):
    """
    Marks a match as resolved (1 = resolved)
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Matches SET resolved = 1 WHERE match_id = ?", (match_id,))
        conn.commit()
        print(f"Match {match_id} marked as resolved.")
    except Exception as e:
        print("ERROR resolving match:", e)
    finally:
        conn.close()


print("Database module loaded with error handling + admin tools. (This is in the dat db.py file)")



# TESTING
if __name__ == "__main__":

    print("\n--- TEST 1 (this should work) ---")
    add_user("u900", "Test User", "test@college.edu", "555-1234", "student")

    print("\n--- TEST 2  ---")
    add_lost_post("lost900", "u900", "Backpack", "Accessories",
                  "Blue backpack with laptop compartment", "2025-02-01", "Library")

    print("\n--- TEST 3 (this should fail should FAIL) ---")
    # category "Food" is NOT allowed under category constraint
    add_lost_post("lost901", "u900", "Sandwich", "Food",
                  "Turkey sandwich", "2025-02-01", "Cafeteria")

    print("\nLost Posts Now:")
    print(get_lost_posts())