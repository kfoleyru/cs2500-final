# python
import sqlite3
from database.db import hash_password #this is for the passcode

# Connect to database
conn = sqlite3.connect("lost_and_found.db")
cur = conn.cursor()

# Enable foreign keys
cur.execute("PRAGMA foreign_keys = ON;")

# CLEAR EXISTING DATA
cur.execute("DELETE FROM Matches")
cur.execute("DELETE FROM FoundPosts")
cur.execute("DELETE FROM LostPosts")
cur.execute("DELETE FROM Users")
conn.commit()
print("Existing data cleared.\n")

# insert 20 users
users_raw = [
    ("950000001", "Alice Johnson", "alice@college.edu", "555-1234", "password123", "student"),
    ("950000002", "Ben Carter", "ben@college.edu", "555-2345", "password123", "student"),
    ("950000003", "Sam Lopez", "sam@college.edu", "555-3456", "password123", "staff"),
    ("950000004", "Kim Nguyen", "kim@college.edu", "555-4567", "password123", "admin"),
    ("950000005", "Jordan Smith", "jordan@college.edu", "555-5678", "password123", "student"),
    ("950000006", "Taylor Brown", "taylor@college.edu", "555-6789", "password123", "student"),
    ("950000007", "Morgan Davis", "morgan@college.edu", "555-7890", "password123", "staff"),
    ("950000008", "Casey Wilson", "casey@college.edu", "555-8901", "password123", "student"),
    ("950000009", "Riley Martinez", "riley@college.edu", "555-9012", "password123", "student"),
    ("950000010", "Avery Garcia", "avery@college.edu", "555-0123", "password123", "student"),
    ("950000011", "Quinn Rodriguez", "quinn@college.edu", "555-1122", "password123", "staff"),
    ("950000012", "Parker Lee", "parker@college.edu", "555-2233", "password123", "student"),
    ("950000013", "Skylar White", "skylar@college.edu", "555-3344", "password123", "student"),
    ("950000014", "Reese Harris", "reese@college.edu", "555-4455", "password123", "student"),
    ("950000015", "Cameron Clark", "cameron@college.edu", "555-5566", "password123", "admin"),
    ("950000016", "Dakota Lewis", "dakota@college.edu", "555-6677", "password123", "student"),
    ("950000017", "Sage Walker", "sage@college.edu", "555-7788", "password123", "student"),
    ("950000018", "River Hall", "river@college.edu", "555-8899", "password123", "staff"),
    ("950000019", "Phoenix Allen", "phoenix@college.edu", "555-9900", "password123", "student"),
    ("950000020", "Rowan Young", "rowan@college.edu", "555-0011", "password123", "student"),
]

# Hash passwords and prepare rows to match table columns including password_hash
users = [
    (user_id, name, email, phone, hash_password(plain_pw), role)
    for (user_id, name, email, phone, plain_pw, role) in users_raw
]

# Insert users adding the password
for u in users:
    try:
        cur.execute(
            "INSERT INTO Users (user_id, name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
            u
        )
    except sqlite3.IntegrityError as e:
        print(f"Skipping user {u[0]}: {e}")


# adding 30 lost posts from chatgpt
lost_posts = [
    ("lost_001", "950000001", "MacBook Air", "Electronics", "Silver laptop in a black case", "2025-02-01", "Library 3rd floor", "open"),
    ("lost_002", "950000002", "Hoodie", "Clothing", "Gray Nike hoodie", "2025-01-28", "Gym locker room", "open"),
    ("lost_003", "950000001", "Student ID Card", "Documents", "Blue ID with lanyard", "2025-02-03", "Cafeteria", "matched"),
    ("lost_004", "950000003", "Car Keys", "Keys", "Black Toyota key fob", "2025-01-30", "Parking Lot B", "open"),
    ("lost_005", "950000005", "iPhone 14", "Electronics", "Black iPhone with cracked screen", "2025-02-05", "Student Union", "open"),
    ("lost_006", "950000006", "Backpack", "Accessories", "Blue Jansport backpack", "2025-02-02", "Science Building", "open"),
    ("lost_007", "950000007", "Wallet", "Accessories", "Brown leather wallet", "2025-01-29", "Parking Lot A", "matched"),
    ("lost_008", "950000008", "Textbook", "Books", "Calculus textbook, 5th edition", "2025-02-04", "Math Building Room 201", "open"),
    ("lost_009", "950000009", "Water Bottle", "Other", "Green Hydro Flask", "2025-02-01", "Gym", "open"),
    ("lost_010", "950000010", "AirPods", "Electronics", "White AirPods Pro with case", "2025-01-31", "Library 2nd floor", "open"),
    ("lost_011", "950000011", "Umbrella", "Other", "Black automatic umbrella", "2025-02-03", "Main Hall entrance", "open"),
    ("lost_012", "950000012", "Jacket", "Clothing", "Red North Face jacket", "2025-01-27", "Cafeteria", "open"),
    ("lost_013", "950000013", "Glasses", "Accessories", "Ray-Ban prescription glasses", "2025-02-02", "Library study room", "open"),
    ("lost_014", "950000014", "Bike Lock", "Keys", "U-lock with two keys", "2025-01-30", "Bike rack near dorms", "open"),
    ("lost_015", "950000015", "Lab Report", "Documents", "Chemistry lab notebook", "2025-02-04", "Science Lab 3", "open"),
    ("lost_016", "950000016", "Headphones", "Electronics", "Sony noise-canceling headphones", "2025-02-01", "Student lounge", "open"),
    ("lost_017", "950000017", "Watch", "Accessories", "Silver Casio digital watch", "2025-01-29", "Basketball court", "matched"),
    ("lost_018", "950000018", "USB Drive", "Electronics", "32GB SanDisk USB drive", "2025-02-05", "Computer lab", "open"),
    ("lost_019", "950000019", "Scarf", "Clothing", "Burgundy knit scarf", "2025-01-28", "Theatre building", "open"),
    ("lost_020", "950000020", "Calculator", "Electronics", "TI-84 graphing calculator", "2025-02-03", "Math Building", "open"),
    ("lost_021", "950000001", "Notebook", "Books", "Spiral notebook with class notes", "2025-02-02", "Lecture Hall B", "open"),
    ("lost_022", "950000002", "Sunglasses", "Accessories", "Black aviator sunglasses", "2025-01-31", "Outdoor quad", "open"),
    ("lost_023", "950000003", "Lunch Box", "Other", "Insulated lunch bag", "2025-02-04", "Cafeteria", "open"),
    ("lost_024", "950000004", "Ring", "Accessories", "Silver class ring", "2025-02-01", "Gym bathroom", "open"),
    ("lost_025", "950000005", "Charger", "Electronics", "MacBook Pro charger", "2025-01-30", "Library", "open"),
    ("lost_026", "950000006", "Hat", "Clothing", "Black baseball cap", "2025-02-03", "Athletic field", "open"),
    ("lost_027", "950000007", "Badge", "Documents", "Staff access badge", "2025-02-05", "Administration building", "matched"),
    ("lost_028", "950000008", "Earbuds", "Electronics", "Samsung Galaxy Buds", "2025-01-29", "Bus stop", "open"),
    ("lost_029", "950000009", "Gloves", "Clothing", "Black winter gloves", "2025-01-27", "Parking structure", "open"),
    ("lost_030", "950000010", "Planner", "Books", "2025 daily planner", "2025-02-02", "Bookstore", "open"),
]

cur.executemany("""
INSERT INTO LostPosts (lost_id, user_id, item_name, category, description,
                       date_lost, last_seen_location, status)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", lost_posts)

# adding 22 found posts from chatgpt
found_posts = [
    ("found_001", "950000003", "Laptop", "Electronics", "Silver laptop – Apple logo", "2025-02-02", "Library study room", "Campus Security Office", "available"),
    ("found_002", "950000001", "Nike Hoodie", "Clothing", "Gray hoodie, size L", "2025-01-29", "Gym bench", "Campus Security Office", "available"),
    ("found_003", "950000003", "ID Card", "Documents", "Student ID card with lanyard", "2025-02-03", "Cafeteria", "Campus Security Office", "matched"),
    ("found_004", "950000004", "Car Keys", "Keys", "Toyota key fob found near Lot B", "2025-01-31", "Parking Lot B", "Campus Security Office", "available"),
    ("found_005", "950000011", "Black Phone", "Electronics", "iPhone with cracked screen", "2025-02-05", "Student Union floor", "Campus Security Office", "available"),
    ("found_006", "950000012", "Backpack", "Accessories", "Blue backpack with books inside", "2025-02-03", "Science Building hallway", "Campus Security Office", "available"),
    ("found_007", "950000013", "Wallet", "Accessories", "Brown leather wallet with cards", "2025-01-30", "Parking Lot A", "Campus Security Office", "matched"),
    ("found_008", "950000014", "Textbook", "Books", "Calculus book", "2025-02-05", "Math Building Room 201", "Campus Security Office", "available"),
    ("found_009", "950000015", "Green Water Bottle", "Other", "Hydro Flask", "2025-02-02", "Gym floor", "Campus Security Office", "available"),
    ("found_010", "950000016", "White Earbuds", "Electronics", "AirPods with charging case", "2025-02-01", "Library 2nd floor table", "Campus Security Office", "available"),
    ("found_011", "950000017", "Umbrella", "Other", "Black umbrella", "2025-02-04", "Main Hall", "Campus Security Office", "available"),
    ("found_012", "950000018", "Red Jacket", "Clothing", "North Face jacket, size M", "2025-01-28", "Cafeteria coat rack", "Campus Security Office", "available"),
    ("found_013", "950000019", "Prescription Glasses", "Accessories", "Ray-Ban frames", "2025-02-03", "Library", "Campus Security Office", "available"),
    ("found_014", "950000020", "U-Lock", "Keys", "Bike lock with keys", "2025-01-31", "Bike rack", "Campus Security Office", "available"),
    ("found_015", "950000002", "Silver Watch", "Accessories", "Digital watch", "2025-01-30", "Basketball court bleachers", "Campus Security Office", "matched"),
    ("found_016", "950000005", "USB Drive", "Electronics", "Small flash drive", "2025-02-05", "Computer lab desk", "Campus Security Office", "available"),
    ("found_017", "950000006", "Scarf", "Clothing", "Red knit scarf", "2025-01-29", "Theatre building", "Campus Security Office", "available"),
    ("found_018", "950000007", "Calculator", "Electronics", "Graphing calculator", "2025-02-04", "Math Building", "Campus Security Office", "available"),
    ("found_019", "950000008", "Sunglasses", "Accessories", "Aviator style sunglasses", "2025-02-01", "Quad bench", "Campus Security Office", "available"),
    ("found_020", "950000009", "Access Badge", "Documents", "Staff badge with photo", "2025-02-05", "Admin building", "Campus Security Office", "matched"),
    ("found_021", "950000010", "Black Hat", "Clothing", "Baseball cap", "2025-02-04", "Athletic field", "Campus Security Office", "available"),
    ("found_022", "950000011", "Earbuds", "Electronics", "Samsung wireless earbuds", "2025-01-30", "Bus stop bench", "Campus Security Office", "available"),
]

cur.executemany("""
INSERT INTO FoundPosts (found_id, user_id, item_name, category, description,
                        date_found, found_location, storage_location, status)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", found_posts)

# adding 4 matches
matches = [
    ("lost_003", "found_003", "950000004", "ID matched successfully"),
    ("lost_007", "found_007", "950000003", "Owner contacted and verified"),
    ("lost_017", "found_015", "950000011", "Watch returned to owner"),
    ("lost_027", "found_020", "950000015", "Badge returned to staff member"),
]

cur.executemany("""
INSERT INTO Matches (lost_id, found_id, matched_by_user_id, notes)
VALUES (?, ?, ?, ?)
""", matches)

# Save changes
conn.commit()

# Verify inserted data
print("\n=== DATA SUMMARY ===")
cur.execute("SELECT COUNT(*) FROM Users")
print(f"Users: {cur.fetchone()[0]} rows")

cur.execute("SELECT COUNT(*) FROM LostPosts")
print(f"LostPosts: {cur.fetchone()[0]} rows")

cur.execute("SELECT COUNT(*) FROM FoundPosts")
print(f"FoundPosts: {cur.fetchone()[0]} rows")

cur.execute("SELECT COUNT(*) FROM Matches")
print(f"Matches: {cur.fetchone()[0]} rows")