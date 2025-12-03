# db.py (reworked for safer concurrent use with Uvicorn/FastAPI)
import sqlite3 as sql
import os

DB = os.path.join(os.path.dirname(__file__), "lost_and_found.db")

def get_connection():
    """
    Return a new sqlite3 connection configured for multithreaded use by Uvicorn.
    - timeout: wait up to 5 seconds for locks to clear
    - check_same_thread=False: allow connections to be used across threads
    """
    conn = sql.connect(DB, timeout=5, check_same_thread=False)
    conn.row_factory = sql.Row
    # ensure foreign keys are enabled on each connection
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def table_has_column(table: str, column: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(?)", (table,))  # placeholder not allowed for PRAGMA, fallback:
    except Exception:
        # PRAGMA table_info doesn't accept bound parameters in sqlite3, use formatted query but sanitize name
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
    cols = [r["name"] for r in cur.fetchall()]
    conn.close()
    return column in cols

# --- USERS/AUTH FUNCTIONS ---

def add_user(user_id: str, name: str, email: str, password: str, phone: str = None, role: str = "student"):
    """
    Adds a new user. Stores the plain text password in whichever column exists:
    'password' preferred, fallback to 'password_hash'.
    Returns (success: bool, message: str)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if table_has_column("Users", "password"):
            pw_col = "password"
        elif table_has_column("Users", "password_hash"):
            pw_col = "password_hash"
        else:
            return False, "Database schema missing password column (password or password_hash)."

        cursor.execute(f"""
            INSERT INTO Users (user_id, name, email, {pw_col}, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, password, phone, role))
        conn.commit()
        return True, "User successfully added."
    except sql.IntegrityError as e:
        msg = str(e)
        if "UNIQUE constraint failed: Users.email" in msg:
            return False, "Error: Email is already registered."
        elif "UNIQUE constraint failed: Users.user_id" in msg:
            return False, "Error: This user ID already exists."
        elif "CHECK constraint failed" in msg:
            return False, "Error: Invalid role specified."
        return False, f"Database error: {e}"
    finally:
        conn.close()

def verify_login(user_id_or_email: str, password: str):
    """
    Verifies user login using user_id or email and plain text password.
    Returns user dict without password field on success, otherwise None.
    """
    conn = get_connection()
    cur = conn.cursor()
    field = 'email' if '@' in user_id_or_email else 'user_id'
    cur.execute(f"SELECT * FROM Users WHERE {field} = ?", (user_id_or_email,))
    user_row = cur.fetchone()
    conn.close()

    if not user_row:
        return None

    user = dict(user_row)
    # Compare plaintext against whichever password column exists
    if 'password' in user:
        if password == user['password']:
            del user['password']
            return user
    elif 'password_hash' in user:
        if password == user['password_hash']:
            del user['password_hash']
            return user

    return None

def get_user_by_id(user_id: str):
    """Retrieves user details by user_id (excludes any password column)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, phone, role FROM Users WHERE user_id = ?", (user_id,))
    user_row = cur.fetchone()
    conn.close()
    return dict(user_row) if user_row else None

def get_lost_posts(status: str = 'open') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

def get_lost_posts_by_user(user_id: str, status: str = 'open') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE user_id = ? AND status = ? ORDER BY date_posted DESC", (user_id, status))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

def get_lost_post(lost_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None

def add_lost_post(lost_id: str, user_id: str, item_name: str, category: str, description: str, date_lost: str,
                  last_seen_location: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO LostPosts (lost_id, user_id, item_name, category, description, date_lost, last_seen_location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lost_id, user_id, item_name, category, description, date_lost, last_seen_location))
        conn.commit()
    finally:
        conn.close()

def delete_lost_post(lost_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM LostPosts WHERE lost_id = ?", (lost_id,))
        conn.commit()
    finally:
        conn.close()

# FOUND POST CRUD
def get_found_posts(status: str = 'available') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

def get_found_post(found_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None

def add_found_post(found_id: str, user_id: str, item_name: str, category: str, description: str, date_found: str,
                   found_location: str, storage_location: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO FoundPosts (found_id, user_id, item_name, category, description, date_found, found_location, storage_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (found_id, user_id, item_name, category, description, date_found, found_location, storage_location))
        conn.commit()
    finally:
        conn.close()

def delete_found_post(found_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM FoundPosts WHERE found_id = ?", (found_id,))
        conn.commit()
    finally:
        conn.close()

# MATCHING FUNCTIONS
def get_all_unresolved_matches() -> list:
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
    """
    Create a match when an owner claims a found item.
    Use a single connection for the entire transaction to avoid database locking due to nested connections.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Use same connection for selects to avoid nested connections
        cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
        lost_post = cur.fetchone()
        cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
        found_post = cur.fetchone()

        if not lost_post or lost_post['status'] != 'open':
            return False, "Lost item not found or is already matched/closed."
        if not found_post or found_post['status'] != 'available':
            return False, "Found item not found or is already matched/returned."
        if lost_post['user_id'] != claimant_user_id:
            return False, "You can only claim items you have reported as lost."

        cur.execute("""
            INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
            VALUES (?, ?, ?, ?)
        """, (lost_id, found_id, claimant_user_id, "Item claimed by owner."))

        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit()
        return True, "Match created successfully. Awaiting admin resolution."
    except Exception as e:
        # If something goes wrong, rollback to be safe
        try:
            conn.rollback()
        except Exception:
            pass
        return False, f"Error creating match: {e}"
    finally:
        conn.close()

def admin_resolve_match(match_id: int) -> tuple[bool, str]:
    """
    Resolve a match and update related post statuses. Use single connection for transaction.
    """
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
        cur.execute("UPDATE Matches SET resolved = 1, notes = ? WHERE match_id = ?",
                    ("Match successfully resolved by admin. Item returned.", match_id))
        cur.execute("UPDATE LostPosts SET status = 'closed' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'returned' WHERE found_id = ?", (found_id,))
        conn.commit()
        return True, f"Match {match_id} resolved successfully."
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, f"Error resolving match: {e}"
    finally:
        conn.close()

# Helpful quick confirmation (optional)
if __name__ == "__main__":
    print("DB module loaded; connection settings: timeout=5, check_same_thread=False")


print("DONE this is db.py")