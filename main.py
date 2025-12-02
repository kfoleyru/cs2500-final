from fastapi import FastAPI, Request, Form, Response, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette import status
import uuid
from typing import Optional

# Database functions
from database.db import (
    get_lost_posts,
    get_found_posts,
    get_lost_post,
    get_found_post,
    add_lost_post,
    delete_lost_post,
    add_found_post,
    delete_found_post,
    add_user,
    verify_login,
    get_user_by_id,
    claim_item,
    get_all_unresolved_matches,
    get_matches_by_user,
    admin_resolve_match,
    get_lost_posts_by_user
)

# --- FastAPI Setup ---
app = FastAPI()
# NOTE: You must create a 'static' directory if you have CSS/JS/images
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Application Constants ---
VALID_CATEGORIES = [
    'Electronics', 'Clothing', 'Accessories',
    'Documents', 'Keys', 'Books', 'Other'
]


# --- Simple Session Helper (using cookies) ---
def get_current_user(user_id: Optional[str] = None):
    """Get current logged in user from cookie or passed ID"""
    if not user_id:
        return None
    return get_user_by_id(user_id)


# --- Authentication Routes ---

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    """Display registration form"""
    # Return context for re-rendering on error
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None, "name": None, "email": None, "phone": None}
    )


@app.post("/register", response_class=HTMLResponse)
async def register_user(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        phone: str = Form(None),
        role: str = Form("student")
):
    """Handle user registration"""
    user_id = name[0].lower() + uuid.uuid4().hex[:7]

    success, message = add_user(user_id, name, email, password, phone, role)

    if success:
        # Automatically log the user in upon successful registration
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="user_id", value=user_id, httponly=True)
        return response
    else:
        # Re-render form with error and submitted data
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": message,
                "name": name,
                "email": email,
                "phone": phone
            }
        )


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Display login form"""
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_user(
        request: Request,
        user_id_or_email: str = Form(...),
        password: str = Form(...)
):
    """Handle user login and set cookie"""
    user = verify_login(user_id_or_email, password)

    if user:
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="user_id", value=user['user_id'], httponly=True)
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid User ID/Email or Password"}
        )


@app.get("/logout", response_class=RedirectResponse)
async def logout_user():
    """Clear session cookie and redirect to login"""
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="user_id")
    return response


# --- Core Application Routes (Requires Login) ---

@app.get("/", response_class=HTMLResponse)
async def home_dashboard(request: Request, user_id: Optional[str] = Cookie(None)):
    """Display the main dashboard with lost and found items"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    lost_posts = get_lost_posts(status='open')
    found_posts = get_found_posts(status='available')

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lost_posts": lost_posts,
            "found_posts": found_posts,
            **current_user
        }
    )


# --- Lost Post Detail/Management ---

@app.get("/lost/{lost_id}", response_class=HTMLResponse)
async def lost_detail(request: Request, lost_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = get_lost_post(lost_id)
    if not post:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Lost item not found.", **current_user},
            status_code=status.HTTP_404_NOT_FOUND
        )

    return templates.TemplateResponse(
        "lost_detail.html",
        {
            "request": request,
            "post": post,
            **current_user
        }
    )


@app.post("/delete-lost/{lost_id}", response_class=RedirectResponse)
async def delete_lost_item(lost_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    post = get_lost_post(lost_id)
    if not post or (post['user_id'] != current_user['user_id'] and current_user['role'] != 'admin'):
        return RedirectResponse("/error?msg=Unauthorized to delete this post.", status_code=status.HTTP_303_SEE_OTHER)

    delete_lost_post(lost_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- Found Post Detail/Management (with Claiming support) ---

@app.get("/found/{found_id}", response_class=HTMLResponse)
async def found_detail(request: Request, found_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = get_found_post(found_id)
    if not post:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Found item not found.", **current_user},
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Fetch the user's open lost posts for claiming the found item
    lost_posts_open = get_lost_posts_by_user(current_user['user_id'], status='open')

    return templates.TemplateResponse(
        "found_detail.html",
        {
            "request": request,
            "post": post,
            "lost_posts_open": lost_posts_open,
            **current_user
        }
    )


@app.post("/delete-found/{found_id}", response_class=RedirectResponse)
async def delete_found_item(found_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    post = get_found_post(found_id)
    if not post or (post['user_id'] != current_user['user_id'] and current_user['role'] != 'admin'):
        return RedirectResponse("/error?msg=Unauthorized to delete this post.", status_code=status.HTTP_303_SEE_OTHER)

    delete_found_post(found_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- Lost Post Routes (Create) ---

@app.get("/add-lost", response_class=HTMLResponse)
async def add_lost_post_form(request: Request, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "add_lost.html",
        {
            "request": request,
            "categories": VALID_CATEGORIES,
            **current_user,
            "error": None
        }
    )


@app.post("/add-lost", response_class=RedirectResponse)
async def create_lost_post(
        request: Request,
        item_name: str = Form(...),
        category: str = Form(...),
        description: str = Form(...),
        date_lost: str = Form(...),
        last_seen_location: str = Form(...),
        user_id: Optional[str] = Cookie(None)
):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    new_id = "lost" + str(uuid.uuid4().hex[:8])

    try:
        add_lost_post(
            lost_id=new_id,
            user_id=current_user['user_id'],
            item_name=item_name,
            category=category,
            description=description,
            date_lost=date_lost,
            last_seen_location=last_seen_location,
        )
        return RedirectResponse(f"/lost/{new_id}", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        return templates.TemplateResponse(
            "add_lost.html",
            {
                "request": request,
                "error": f"Database error: {e}",
                "categories": VALID_CATEGORIES,
                **current_user
            }
        )


# --- Found Post Routes (Create) ---
@app.get("/add-found", response_class=HTMLResponse)
async def add_found_post_form(request: Request, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "add_found.html",
        {
            "request": request,
            "categories": VALID_CATEGORIES,
            **current_user,
            "error": None
        }
    )


@app.post("/add-found", response_class=RedirectResponse)
async def create_found_post(
        request: Request,
        item_name: str = Form(...),
        category: str = Form(...),
        description: str = Form(...),
        date_found: str = Form(...),
        found_location: str = Form(...),
        storage_location: str = Form("Campus Security Office"),
        user_id: Optional[str] = Cookie(None)
):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    new_id = "found" + str(uuid.uuid4().hex[:8])

    try:
        add_found_post(
            found_id=new_id,
            user_id=current_user['user_id'],
            item_name=item_name,
            category=category,
            description=description,
            date_found=date_found,
            found_location=found_location,
            storage_location=storage_location,
        )
        return RedirectResponse(f"/found/{new_id}", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        return templates.TemplateResponse(
            "add_found.html",
            {
                "request": request,
                "error": f"Database error: {e}",
                "categories": VALID_CATEGORIES,
                **current_user
            }
        )


# --- Matching System Routes ---

@app.post("/claim/{found_id}", response_class=RedirectResponse)
async def claim_found_item(
        found_id: str,
        lost_id: str = Form(...),
        user_id: Optional[str] = Cookie(None)
):
    """Route for a user to claim a found item (create a match)"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    success, message = claim_item(lost_id, found_id, current_user['user_id'])

    if success:
        return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Redirect to generic error page
        return RedirectResponse(f"/error?msg={message}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/matches", response_class=HTMLResponse)
async def view_matches(request: Request, user_id: Optional[str] = Cookie(None)):
    """Display matches relevant to the current user (or all for admin)"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user['role'] == 'admin':
        matches = get_all_unresolved_matches()  # Admin sees only unresolved
    else:
        matches = get_matches_by_user(current_user['user_id'])  # User sees all of their matches

    return templates.TemplateResponse(
        "matches.html",
        {
            "request": request,
            "matches": matches,
            **current_user
        }
    )


@app.post("/admin/resolve/{match_id}", response_class=RedirectResponse)
async def resolve_match(request: Request, match_id: int, user_id: Optional[str] = Cookie(None)):
    """Admin route to resolve a match"""
    current_user = get_current_user(user_id)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if current_user['role'] != 'admin':
        return RedirectResponse("/error?msg=Unauthorized: Admin access required", status_code=status.HTTP_303_SEE_OTHER)

    success, message = admin_resolve_match(match_id)

    if success:
        return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(f"/error?msg={message}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/error", response_class=HTMLResponse)
async def error_page(request: Request, msg: Optional[str] = None, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    error_message = msg if msg else "An unexpected error occurred."

    # Context for layout.html even if user isn't fully logged in (but may have a stale cookie)
    user_context = current_user if current_user else {"user_id": None, "user_name": "Guest", "user_role": "guest"}

    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": error_message,
            **user_context
        }
    )