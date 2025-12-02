from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette import status
import uuid  # Used for generating unique IDs for lost/found posts
from database.db import (
    get_lost_posts,
    get_found_posts,
    add_lost_post,
    delete_lost_post,
    add_found_post,
    delete_found_post,
    add_user,
)

# --- FastAPI Setup ---
app = FastAPI()

# Mount a directory for static files (e.g., CSS, images)
# For simplicity, I'm assuming a 'static' folder exists in the same directory as main.py
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
# For simplicity, I'm assuming a 'templates' folder exists in the same directory as main.py
templates = Jinja2Templates(directory="templates")

# --- Helper Functions (Mocking User and Data for Demo) ---
"""
# Mock a user ID since posts require one.
# You would replace this with actual authentication logic.
MOCK_USER_ID = "u001"

# Ensure the mock user exists for Foreign Key constraints
# In a real app, this would happen during user registration/login.
success, message = add_user(MOCK_USER_ID, "Test User", "test@college.edu")
if not success and "already exists" not in message:
    print(f"Failed to ensure mock user exists: {message}")

# Valid categories for form validation
VALID_CATEGORIES = [
    'Electronics', 'Clothing', 'Accessories',
    'Documents', 'Keys', 'Books', 'Other'
]
"""

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Displays the homepage with lists of all Lost and Found posts.
    """
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
            "user_id": MOCK_USER_ID
        }
    )


## Lost Post Routes

@app.get("/add-lost", response_class=HTMLResponse)
async def add_lost_post_form(request: Request):
    """
    Displays the form to add a new Lost Post.
    """
    return templates.TemplateResponse(
        "add_lost.html",
        {"request": request, "categories": VALID_CATEGORIES}
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
    """
    Handles the form submission to create a new Lost Post.
    """
    new_id = "lost" + str(uuid.uuid4().hex[:8])  # Generate a simple unique ID

    # Simple validation for category
    if category not in VALID_CATEGORIES:
        return templates.TemplateResponse(
            "add_lost.html",
            {"request": request, "error": "Invalid category selected.", "categories": VALID_CATEGORIES}
        )

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
        # Redirect back to the homepage after successful submission
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # Pass an error message to the template
        return templates.TemplateResponse(
            "add_lost.html",
            {"request": request, "error": f"Database error: {e}", "categories": VALID_CATEGORIES}
        )


@app.post("/delete-lost/{lost_id}", response_class=HTMLResponse)
async def remove_lost_post(request: Request, lost_id: str):
    """
    Deletes a specific Lost Post.
    """
    delete_lost_post(lost_id)
    # Redirect back to the homepage
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


## Found Post Routes

@app.get("/add-found", response_class=HTMLResponse)
async def add_found_post_form(request: Request):
    """
    Displays the form to add a new Found Post.
    """
    return templates.TemplateResponse(
        "add_found.html",
        {"request": request, "categories": VALID_CATEGORIES}
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
    """
    Handles the form submission to create a new Found Post.
    """
    new_id = "found" + str(uuid.uuid4().hex[:8])  # Generate a simple unique ID

    if category not in VALID_CATEGORIES:
        return templates.TemplateResponse(
            "add_found.html",
            {"request": request, "error": "Invalid category selected.", "categories": VALID_CATEGORIES}
        )

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
    """
    Deletes a specific Found Post.
    """
    delete_found_post(found_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)