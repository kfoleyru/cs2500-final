import sqlite3 as sql
import hashlib

DB = "lost_and_found.db"


def get_connection():
    conn = sql.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str) -> str:
    """Simple SHA256 hash for password storage"""
    return hashlib.sha256(password.encode()).hexdigest()


# USERS
def add_user(user_id: str, name: str, email: str, password: str, phone: str = None, role: str = "student"):
    """
    Adds a new user to the Users table with password hashing.
    Includes full error handling for: duplicate user_id, duplicate email, invalid role
    """
    try:
        connection = sql.connect(DB)
        cursor = connection.cursor()

        password_hash = hash_password(password)

        cursor.execute("""
            INSERT INTO Users (user_id, name, email, password_hash, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, password_hash, phone, role))

        connection.commit()
        return True, "User successfully added."

    except sql.IntegrityError as e:
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


def get_user_by_id(user_id: str):
    """
    Retrieves a user's details by their user_id.
    Returns a dictionary with user info or None if not found.
    """
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sql.Row
        cur = conn.cursor()

        cur.execute("SELECT user_id, name, email, phone, role, date_joined FROM Users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()

        if row:
            return dict(row)
        return None

    except Exception as e:
        print("ERROR retrieving user:", e)
        return None
    finally:
        if conn:
            conn.close()


def verify_login(user_id: str, password: str):
    """
    Verifies login credentials.
    Returns user data (dict) if successful, None otherwise.
    """
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sql.Row
        cur = conn.cursor()

        password_hash = hash_password(password)

        cur.execute("""
            SELECT user_id, name, email, phone, role, date_joined 
            FROM Users 
            WHERE user_id = ? AND password_hash = ?
        """, (user_id, password_hash))

        row = cur.fetchone()

        if row:
            return dict(row)
        return None

    except Exception as e:
        print("ERROR verifying login:", e)
        return None
    finally:
        if conn:
            conn.close()


def get_all_users():
    """
    Retrieves a list of all users from the Users table.
    This is used by main.py to check if any accounts exist.
    """
    users = []
    conn = None
    try:
        conn = get_connection()
        conn.row_factory = sql.Row
        cur = conn.cursor()

        cur.execute("SELECT user_id, name, email, role, date_joined FROM Users")
        users = [dict(row) for row in cur.fetchall()]

    except Exception as e:
        print("ERROR retrieving all users:", e)
    finally:
        if conn:
            conn.close()
    return users


# POSTS
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
                "status": row[8]
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
                "status": row[9]
            }
            for row in rows
        ]
    except sql.Error as e:
        print("Error retrieving found posts:", e)
        return []
    finally:
        if conn:
            conn.close()


def get_found_post(found_id: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
        row = cur.fetchone()
        if not row:
            return None
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
    except sql.Error as e:
        print("Error retrieving found post:", e)
        return None
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


# MATCHING SYSTEM
def claim_item(lost_id: str, found_id: str, claiming_user_id: str, notes: str = ""):
    """
    Creates a match between a lost and found item.
    Updates both posts to 'matched' status.
    Returns (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Verify the claiming user isn't claiming their own post
        cur.execute("SELECT user_id FROM LostPosts WHERE lost_id = ?", (lost_id,))
        lost_owner = cur.fetchone()
        cur.execute("SELECT user_id FROM FoundPosts WHERE found_id = ?", (found_id,))
        found_owner = cur.fetchone()

        if lost_owner and lost_owner[0] == claiming_user_id:
            return False, "You cannot claim your own lost post."
        if found_owner and found_owner[0] == claiming_user_id:
            return False, "You cannot claim your own found post."

        # Create match entry
        cur.execute("""
            INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
            VALUES (?, ?, ?, ?)
        """, (lost_id, found_id, claiming_user_id, notes))

        # Update post statuses
        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, "Match created successfully!"

    except sql.IntegrityError as e:
        return False, f"Match creation failed: {e}"
    except Exception as e:
        return False, f"Error creating match: {e}"
    finally:
        if conn:
            conn.close()


def get_all_unresolved_matches():
    """
    Retrieves all unresolved matches with details from both posts.
    Returns a list of dictionaries containing match info.
    """
    try:
        conn = get_connection()
        conn.row_factory = sql.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                m.match_id,
                m.lost_id,
                m.found_id,
                m.matched_by_user_id,
                m.date_matched,
                m.notes,
                l.item_name as lost_item_name,
                l.user_id as lost_owner_id,
                f.item_name as found_item_name,
                f.user_id as found_owner_id
            FROM Matches m
            JOIN LostPosts l ON m.lost_id = l.lost_id
            JOIN FoundPosts f ON m.found_id = f.found_id
            WHERE m.resolved = 0
            ORDER BY m.date_matched DESC
        """)

        return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        print("ERROR retrieving unresolved matches:", e)
        return []
    finally:
        if conn:
            conn.close()


def get_matches_by_user(user_id: str):
    """
    Retrieves matches relevant to a specific user (their posts).
    """
    try:
        conn = get_connection()
        conn.row_factory = sql.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                m.match_id,
                m.lost_id,
                m.found_id,
                m.matched_by_user_id,
                m.date_matched,
                m.resolved,
                m.notes,
                l.item_name as lost_item_name,
                l.user_id as lost_owner_id,
                f.item_name as found_item_name,
                f.user_id as found_owner_id
            FROM Matches m
            JOIN LostPosts l ON m.lost_id = l.lost_id
            JOIN FoundPosts f ON m.found_id = f.found_id
            WHERE l.user_id = ? OR f.user_id = ?
            ORDER BY m.date_matched DESC
        """, (user_id, user_id))

        return [dict(row) for row in cur.fetchall()]

    except Exception as e:
        print("ERROR retrieving user matches:", e)
        return []
    finally:
        if conn:
            conn.close()


"""
Admin Tools
"""


def admin_match_items(lost_id: str, found_id: str, admin_user_id: str, notes: str = ""):
    """
    Creates a match between a lost and found item (admin version).
    Sets statuses to 'matched'.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
            VALUES (?, ?, ?, ?)
        """, (lost_id, found_id, admin_user_id, notes))

        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, "Items matched successfully!"

    except sql.IntegrityError as e:
        return False, f"Matching failed: {e}"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def admin_resolve_match(match_id: int):
    """
    Marks a match as resolved and updates post statuses.
    Returns (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Get the lost_id and found_id from the match
        cur.execute("SELECT lost_id, found_id FROM Matches WHERE match_id = ?", (match_id,))
        match = cur.fetchone()

        if not match:
            return False, "Match not found."

        lost_id, found_id = match

        # Update match status
        cur.execute("UPDATE Matches SET resolved = 1 WHERE match_id = ?", (match_id,))

        # Update post statuses
        cur.execute("UPDATE LostPosts SET status = 'closed' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'returned' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, f"Match {match_id} resolved successfully."

    except Exception as e:
        return False, f"Error resolving match: {e}"
    finally:
        conn.close()


print("Database module loaded with authentication + matching system.")

# TESTING
if __name__ == "__main__":
    print("\n--- TEST 1: Add user with password ---")
    success, msg = add_user("u900", "Test User", "test@college.edu", "password123", "555-1234", "student")
    print(msg)

    print("\n--- TEST 2: Verify login ---")
    user = verify_login("u900", "password123")
    print("Login successful!" if user else "Login failed!")
    if user:
        print(f"Welcome {user['name']}, role: {user['role']}")

    print("\n--- TEST 3: Wrong password ---")
    user = verify_login("u900", "wrongpassword")
    print("Login successful!" if user else "Login failed (as expected)!")