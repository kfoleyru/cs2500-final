from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette import status
import uuid  # Used for generating unique IDs for posts
from database.db import (
    get_lost_posts,
    get_found_posts,
    add_lost_post,
    delete_lost_post,
    add_found_post,
    delete_found_post,
    add_user,
    get_all_users,  # Added to check if any user exists
)

# --- FastAPI Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Application Constants ---
# In a real application, you'd use a session/cookie to manage the logged-in user.
# For this demo, we'll simulate a logged-in user (u900) for posting/deleting,
# but the registration route is fully functional.
MOCK_USER_ID = "u900"
MOCK_USER_NAME = "Demo User"

# Valid categories from your CreateLAF.py
VALID_CATEGORIES = [
    'Electronics', 'Clothing', 'Accessories',
    'Documents', 'Keys', 'Books', 'Other'
]


# --- Initial Setup (Ensuring Mock User and Data) ---
def ensure_mock_user():
    """Checks if the mock user exists and adds them if not."""
    if not get_all_users():  # If no users exist, ensure the mock user is available
        success, message = add_user(MOCK_USER_ID, MOCK_USER_NAME, "demo@uvm.edu", "555-1234", "student")
        if not success and "already exists" not in message:
            print(f"Failed to ensure mock user exists: {message}")


ensure_mock_user()


# --- Routes ---

## 🌎 Homepage Route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Displays the homepage with lists of all Lost and Found posts."""
    lost_posts = get_lost_posts()
    found_posts = get_found_posts()

    # Sort posts by date posted (newest first)
    lost_posts.sort(key=lambda x: x['date_posted'], reverse=True)
    found_posts.sort(key=lambda x: x['date_posted'], reverse=True)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "lost_posts": lost_posts,
            "found_posts": found_posts,
            "user_id": MOCK_USER_ID,  # Pass the current user ID for delete permissions
            "user_name": MOCK_USER_NAME
        }
    )


# --- 👤 Registration Routes ---

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    """Displays the form to create a new user account."""
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register", response_class=HTMLResponse)
async def create_account(
        request: Request,
        user_id: str = Form(...),
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(None),
        role: str = Form("student")  # Default role
):
    """Handles the form submission to create a new user account."""
    success, message = add_user(user_id, name, email, phone, role)

    if success:
        # Success message, then redirect to home
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "message": f"Account created successfully for {name}! You can now post.",
                "user_id": user_id,
                "user_name": name,
                "lost_posts": get_lost_posts(),
                "found_posts": get_found_posts(),
            }
        )
    else:
        # Display the error message back on the registration form
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Registration Failed: {message}"}
        )


# --- 🔎 Lost Post Routes ---

@app.get("/add-lost", response_class=HTMLResponse)
async def add_lost_post_form(request: Request):
    return templates.TemplateResponse(
        "add_lost.html",
        {"request": request, "categories": VALID_CATEGORIES, "user_id": MOCK_USER_ID}
    )


@app.post("/add-lost", response_class=HTMLResponse)
async def create_lost_post(
        request: Request,
        item_name: str = Form(...),
        category: str = Form(...),
        description: str = Form(...),
        date_lost: str = Form(...),
        last_seen_location: str = Form(...)
):
    new_id = "lost" + str(uuid.uuid4().hex[:8])

    try:
        add_lost_post(
            lost_id=new_id,
            user_id=MOCK_USER_ID,
            item_name=item_name,
            category=category,
            description=description,
            date_lost=date_lost,
            last_seen_location=last_seen_location,
        )
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "add_lost.html",
            {"request": request, "error": f"Database error: {e}", "categories": VALID_CATEGORIES}
        )


@app.post("/delete-lost/{lost_id}", response_class=HTMLResponse)
async def remove_lost_post(request: Request, lost_id: str):
    delete_lost_post(lost_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- 🤝 Found Post Routes ---

@app.get("/add-found", response_class=HTMLResponse)
async def add_found_post_form(request: Request):
    return templates.TemplateResponse(
        "add_found.html",
        {"request": request, "categories": VALID_CATEGORIES, "user_id": MOCK_USER_ID}
    )


@app.post("/add-found", response_class=HTMLResponse)
async def create_found_post(
        request: Request,
        item_name: str = Form(...),
        category: str = Form(...),
        description: str = Form(...),
        date_found: str = Form(...),
        found_location: str = Form(...),
        storage_location: str = Form("Campus Security Office")
):
    new_id = "found" + str(uuid.uuid4().hex[:8])

    try:
        add_found_post(
            found_id=new_id,
            user_id=MOCK_USER_ID,
            item_name=item_name,
            category=category,
            description=description,
            date_found=date_found,
            found_location=found_location,
            storage_location=storage_location
        )
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "add_found.html",
            {"request": request, "error": f"Database error: {e}", "categories": VALID_CATEGORIES}
        )


@app.post("/delete-found/{found_id}", response_class=HTMLResponse)
async def remove_found_post(request: Request, found_id: str):
    delete_found_post(found_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)