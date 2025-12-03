# imports
import sqlite3 as sql
import os

#pathing to the database
DB = os.path.join(os.path.dirname(__file__), "lost_and_found.db")


# connect this i found online because the datAbase kept not INTERACTING TO the database
def get_connection():
    """
    Return a new sqlite3 connection configureds, this waits for 5 seconds to acquire locks
    """
    conn = sql.connect(DB, timeout=5, check_same_thread=False)
    conn.row_factory = sql.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# PLANNING: Need a helper function to check if a column exists in a table.
def table_has_column(table: str, column: str) -> bool:
    # ACTION: Get connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(?)", (table,))  # Initial attempt with placeholder
    except Exception:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
    # ACTION: Extract column names and check if the target exists.
    print("cur.execute(f'PRAGMA table_info({table})') ran")
    cols = [r["name"] for r in cur.fetchall()]
    conn.close()
    return column in cols

# --- USERS/AUTH FUNCTIONS ---
# making a user
def add_user(user_id: str, name: str, email: str, password: str, phone: str = None, role: str = "student"):
    """
    Adds a new user. Stores the plain text password in whichever column exists:
    'password' preferred, fallback to 'password_hash'.
    Returns (success: bool, message: str)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
# dynamically check the schema for password column name.
        if table_has_column("Users", "password"):
            pw_col = "password"
        elif table_has_column("Users", "password_hash"):
            pw_col = "password_hash"
        else:
            return False, "Database schema missing password column (password or password_hash)."

        # ACTION: Execute the INSERT using the determined column name.
        cursor.execute(f"""
            INSERT INTO Users (user_id, name, email, {pw_col}, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, password, phone, role))
        conn.commit()
        return True, "User successfully added."
    # ERROR HANDLING: Catch integrity errors for duplicates
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
        # ACTION: close system everytime
        conn.close()

        #i need to make a verification now

# What I need: A flexible login check (ID or email) that handles either password column.
def verify_login(user_id_or_email: str, password: str):
    """
    Verifies user login using user_id or email and plain text password.
    Returns user dict without password field on success, otherwise None.
    """
    conn = get_connection()
    cur = conn.cursor()
    # DECISION POINT: Determine lookup field based on the presence of '@'.
    field = 'email' if '@' in user_id_or_email else 'user_id'
    cur.execute(f"SELECT * FROM Users WHERE {field} = ?", (user_id_or_email,))
    user_row = cur.fetchone()
    conn.close()

    if not user_row:
        return None

    user = dict(user_row)
    # LOGIC: Check against the column that exists in the fetched row.
    if 'password' in user:
        if password == user['password']:
            del user['password'] #delete apss
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
    #SQL that likee gett all the information needed for the profile
    cur.execute("SELECT user_id, name, email, phone, role FROM Users WHERE user_id = ?", (user_id,))
    user_row = cur.fetchone()
    conn.close()
    return dict(user_row) if user_row else None

# FRAMEWORK STEP 3: Lost Item Management (CRUD)
# What I need: List all posts, filtered by status, ordered by date.
def get_lost_posts(status: str = 'open') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

# What needs to happen for this to work: List posts for a just the user logging in.
def get_lost_posts_by_user(user_id: str, status: str = 'open') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE user_id = ? AND status = ? ORDER BY date_posted DESC", (user_id, status))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

# Whats needed: Retrieve a single post by ID.
def get_lost_post(lost_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None

# What I need: Insertion logic.
def add_lost_post(lost_id: str, user_id: str, item_name: str, category: str, description: str, date_lost: str,
                  last_seen_location: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # the insert: INSERT INTO LostPosts (lost_id, user_id, item_name, category, description, date_lost, last_seen_location)
        cur.execute("""
            INSERT INTO LostPosts (lost_id, user_id, item_name, category, description, date_lost, last_seen_location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lost_id, user_id, item_name, category, description, date_lost, last_seen_location))
        conn.commit()
    finally:
        conn.close()

# What I need: Deletion logic.
def delete_lost_post(lost_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try: #delete fromlthe table now
        cur.execute("DELETE FROM LostPosts WHERE lost_id = ?", (lost_id,))
        conn.commit()
    finally:
        conn.close()

# FOUND POST CRUD
# FRAMEWORK STEP 4: Found Item Management this is lowkey just the lost post one
# What I need: List all posts, using 'available' status as the default.
def get_found_posts(status: str = 'available') -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE status = ? ORDER BY date_posted DESC", (status,))
    posts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return posts

# What I need: Retrieve a single found post by ID.
def get_found_post(found_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
    post_row = cur.fetchone()
    conn.close()
    return dict(post_row) if post_row else None

# What I need: Insertion logic (must include storage_location).
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

# What I need: Deletion logic.
def delete_found_post(found_id: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM FoundPosts WHERE found_id = ?", (found_id,))
        conn.commit()
    finally:
        conn.close()
# What i still need to do is the matching function look at the social media and perhaps find something online thats like this

# MATCHING FUNCTIONS
# FRAMEWORK STEP 5: Matching and Transaction Logic (admin special priv perhaps)
# What I need: Admin view - all matches that haven't been resolved (resolved = 0). i need to join the tables and then
# check for the resolved status perhaps change the 0's to 1's
def get_all_unresolved_matches() -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            m.*,
            lp.item_name AS lost_item_name,  -- Pull the name of the lost item. We need a clear, friendly label for the report.
            fp.item_name AS found_item_name, -- Pull the name of the found item, again for clarity.
            u.name AS matched_by_user_name
        FROM Matches m
        JOIN LostPosts lp ON m.lost_id = lp.lost_id   -- Match must link to a lost post.
        JOIN FoundPosts fp ON m.found_id = fp.found_id -- Match must link to a found post.
        LEFT JOIN Users u ON m.matched_by_user_id = u.user_id --LEFT JOIN.
        WHERE m.resolved = 0 
        ORDER BY m.date_matched DESC
    """)
    matches = [dict(row) for row in cur.fetchall()]
    conn.close()
    return matches

# What I need: User view - matches relevant to their lost or found posts.
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
        -- LOGIC: The user is involved if they posted the lost item OR the found item.
        WHERE lp.user_id = ? OR fp.user_id = ?
        ORDER BY m.resolved ASC, m.date_matched DESC -- Show UNRESOLVED (0) first, then date.
    """, (user_id, user_id))
    matches = [dict(row) for row in cur.fetchall()]
    conn.close()
    return matches

# What I need: The claim transaction.
def claim_item(lost_id: str, found_id: str, claimant_user_id: str) -> tuple[bool, str]:
    """
    Create a match when an owner claims a found item.
    Use a single connection for the entire transaction to avoid database locking due to nested connections.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM LostPosts WHERE lost_id = ?", (lost_id,))
        lost_post = cur.fetchone()
        cur.execute("SELECT * FROM FoundPosts WHERE found_id = ?", (found_id,))
        found_post = cur.fetchone()

        # Check item status.
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

        # Update both post statuses to 'matched'.
        cur.execute("UPDATE LostPosts SET status = 'matched' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'matched' WHERE found_id = ?", (found_id,))

        conn.commit() # FINAL STEP: Commit the whole transaction.
        return True, "Match created successfully. Awaiting admin resolution."
    except Exception as e:
        #roll back function if it fails
        try:
            conn.rollback()
        except Exception:
            pass
        return False, f"Error creating match: {e}"
    finally:
        conn.close()

# What I need: The final resolution transaction.
def admin_resolve_match(match_id: int) -> tuple[bool, str]:
    """
    Resolve a match and update related post statuses. Use single connection for transaction.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check the match exists and is unresolved.
        cur.execute("SELECT lost_id, found_id, resolved FROM Matches WHERE match_id = ?", (match_id,))
        match = cur.fetchone()
        if not match:
            return False, "Match not found."
        if match['resolved'] == 1:
            return False, "Match is already resolved."
        lost_id, found_id = match['lost_id'], match['found_id']

        # Update all 3 tables: Matches, LostPosts, FoundPosts once we know its valid
        cur.execute("UPDATE Matches SET resolved = 1, notes = ? WHERE match_id = ?",
                    ("Match successfully resolved by admin. Item returned.", match_id))
        cur.execute("UPDATE LostPosts SET status = 'closed' WHERE lost_id = ?", (lost_id,))
        cur.execute("UPDATE FoundPosts SET status = 'returned' WHERE found_id = ?", (found_id,))
        conn.commit()
        return True, f"Match {match_id} resolved successfully."
    except Exception as e:
        # rollback if needed
        try:
            conn.rollback()
        except Exception:
            pass
        return False, f"Error resolving match: {e}"
    finally:
        conn.close()



if __name__ == "__main__":
    print("DB module loaded")
    print("the db file is working this is db.py") # this is for the main file so I know when it actually os called during it so it worked