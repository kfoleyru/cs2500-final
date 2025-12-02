import sqlite3 as sql
import hashlib

DB = "lost_and_found.db"


def get_connection():
    conn = sql.connect(DB)
    # Enable row factory for dictionary-like access
    conn.row_factory = sql.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str) -> str:
    """Simple SHA256 hash for password storage"""
    # NOTE: Use a production-ready library (e.g., bcrypt) for real applications
    return hashlib.sha256(password.encode()).hexdigest()


# --- USERS/AUTH FUNCTIONS ---

def add_user(user_id: str, name: str, email: str, password: str, phone: str = None, role: str = "student"):
    """Adds a new user to the Users table with password hashing."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO Users (user_id, name, email, password_hash, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, password_hash, phone, role))
        conn.commit()
        return True, "User successfully added."
    except sql.IntegrityError as e:
        if "UNIQUE constraint failed: Users.email" in str(e):
            return False, "Error: Email is already registered."
        elif "UNIQUE constraint failed: Users.user_id" in str(e):
            return False, "Error: This user ID already exists."
        elif "CHECK constraint failed" in str(e):
            return False, "Error: Invalid role specified."
        return False, f"Database error: {e}"
    finally:
        conn.close()


def verify_login(user_id_or_email: str, password: str) -> dict or None:
    """Verifies user login using user_id or email and password."""
    conn = get_connection()
    cur = conn.cursor()

    # Determine if input is email or user_id
    field = 'email' if '@' in user_id_or_email else 'user_id'

    cur.execute(f"SELECT * FROM Users WHERE {field} = ?", (user_id_or_email,))
    user_row = cur.fetchone()
    conn.close()

    if user_row:
        user = dict(user_row)
        if hash_password(password) == user['password_hash']:
            del user['password_hash']
            return user

    return None


def get_user_by_id(user_id: str) -> dict or None:
    """Retrieves user details by user_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, phone, role FROM Users WHERE user_id = ?", (user_id,))
    user_row = cur.fetchone()
    conn.close()
    return dict(user_row) if user_row else None


# --- LOST POST CRUD (Including helper for user's open posts) ---

def get_lost_posts(status: str = 'open') -> list:
    """Retrieves all lost posts with a specific status."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts


def get_lost_posts_by_user(user_id: str, status: str = 'open') -> list:
    """Retrieves lost posts by a specific user with a specific status."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE user_id = ? AND status = ? ORDER BY date_posted DESC", (user_id, status))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts


def get_lost_post(lost_id: str) -> dict or None:
    """Retrieves a single lost post by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None


def add_lost_post(lost_id: str, user_id: str, item_name: str, category: str, description: str, date_lost: str,
                  last_seen_location: str):
    """Inserts a new lost post."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO LostPosts (lost_id, user_id, item_name, category, description, date_lost, last_seen_location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lost_id, user_id, item_name, category, description, date_lost, last_seen_location))
    conn.commit()
    conn.close()


def delete_lost_post(lost_id: str):
    """Deletes a lost post."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM LostPosts WHERE lost_id = ?", (lost_id,))
    conn.commit()
    conn.close()


# --- FOUND POST CRUD ---

def get_found_posts(status: str = 'available') -> list:
    """Retrieves all found posts with a specific status."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts


def get_found_post(found_id: str) -> dict or None:
    """Retrieves a single found post by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None


def add_found_post(found_id: str, user_id: str, item_name: str, category: str, description: str, date_found: str,
                   found_location: str, storage_location: str):
    """Inserts a new found post."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO FoundPosts (found_id, user_id, item_name, category, description, date_found, found_location, storage_location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (found_id, user_id, item_name, category, description, date_found, found_location, storage_location))
    conn.commit()
    conn.close()


def delete_found_post(found_id: str):
    """Deletes a found post."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM FoundPosts WHERE found_id = ?", (found_id,))
    conn.commit()
    conn.close()


# --- MATCHING FUNCTIONS ---

def get_all_unresolved_matches() -> list:
    """Retrieves all unresolved matches (resolved=0) for admin view."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.*, 
            lp.item_name AS lost_item_name, 
            fp.item_name AS found_item_name,
            u.name AS matched_by_user_name
        FROM Matches m
        JOIN LostPosts lp ON m.lost_id = lp.lost_id
        JOIN FoundPosts fp ON m.found_id = fp.found_id
        LEFT JOIN Users u ON m.matched_by_user_id = u.user_id
        WHERE m.resolved = 0
        ORDER BY m.date_matched DESC
    """)
    matches = [dict(row) for row in cur.fetchall()]
    conn.close()
    return matches


def get_matches_by_user(user_id: str) -> list:
    """Retrieves matches related to posts created by a specific user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            m.*, 
            lp.item_name AS lost_item_name, 
            fp.item_name AS found_item_name,
            u_matched.name AS matched_by_user_name
        FROM Matches m
        JOIN LostPosts lp ON m.lost_id = lp.lost_id
        JOIN FoundPosts fp ON m.found_id = fp.found_id
        LEFT JOIN Users u_matched ON m.matched_by_user_id = u_matched.user_id
        WHERE lp.user_id = ? OR fp.user_id = ?
        ORDER BY m.resolved ASC, m.date_matched DESC
    """, (user_id, user_id))
    matches = [dict(row) for row in cur.fetchall()]
    conn.close()
    return matches


def claim_item(lost_id: str, found_id: str, claimant_user_id: str) -> tuple[bool, str]:
    """Creates a match between a lost and found item."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        lost_post = get_lost_post(lost_id)
        found_post = get_found_post(found_id)

        if not lost_post or lost_post['status'] != 'open':
            return False, "Lost item not found or is already matched/closed."
        if not found_post or found_post['status'] != 'available':
            return False, "Found item not found or is already matched/returned."

        # Check if the claimant is the lost poster
        if lost_post['user_id'] != claimant_user_id:
            return False, "You can only claim items you have reported as lost."

        # Create the match
        cur.execute("""
            INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
            VALUES (?, ?, ?, ?)
        """, (lost_id, found_id, claimant_user_id, "Item claimed by owner."))

        # Update post statuses
        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, "Match created successfully. Awaiting admin resolution."

    except Exception as e:
        return False, f"Error creating match: {e}"
    finally:
        conn.close()


def admin_resolve_match(match_id: int) -> tuple[bool, str]:
    """Sets a match to resolved (1) and updates both post statuses to final states."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT lost_id, found_id, resolved FROM Matches WHERE match_id = ?", (match_id,))
        match = cur.fetchone()

        if not match:
            return False, "Match not found."

        if match['resolved'] == 1:
            return False, "Match is already resolved."

        lost_id, found_id = match['lost_id'], match['found_id']

        # Update match status
        cur.execute("UPDATE Matches SET resolved = 1, notes = ? WHERE match_id = ?",
                    ("Match successfully resolved by admin. Item returned.", match_id))

        # Update post statuses
        cur.execute("UPDATE LostPosts SET status = 'closed' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'returned' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, f"Match {match_id} resolved successfully."

    except Exception as e:
        return False, f"Error resolving match: {e}"
    finally:
        conn.close()