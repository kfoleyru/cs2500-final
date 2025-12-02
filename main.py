from fastapi import FastAPI, Request, Form, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette import status
import uuid
from typing import Optional
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
)

# --- FastAPI Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Application Constants ---
VALID_CATEGORIES = [
    'Electronics', 'Clothing', 'Accessories',
    'Documents', 'Keys', 'Books', 'Other'
]


# Simple session helper (using cookies)
def get_current_user(user_id: Optional[str] = Cookie(None)):
    """Get current logged in user from cookie"""
    if not user_id:
        return None
    return get_user_by_id(user_id)


# --- Authentication Routes ---

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Display login form"""
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(
        request: Request,
        user_id: str = Form(...),
        password: str = Form(...)
):
    """Handle login submission"""
    user = verify_login(user_id, password)

    if user:
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="user_id", value=user_id, httponly=True)
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials. Please try again."}
        )


@app.get("/logout")
async def logout():
    """Log out the user"""
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="user_id")
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    """Display registration form"""
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register", response_class=HTMLResponse)
async def create_account(
        request: Request,
        user_id: str = Form(...),
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        phone: str = Form(None),
        role: str = Form("student")
):
    """Handle registration submission"""
    success, message = add_user(user_id, name, email, password, phone, role)

    if success:
        response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
        return response
    else:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Registration Failed: {message}"}
        )


# --- Homepage Route ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user_id: Optional[str] = Cookie(None)):
    """Display homepage with all posts"""
    current_user = get_current_user(user_id)

    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    lost_posts = [p for p in get_lost_posts() if p['status'] == 'open']
    found_posts = [p for p in get_found_posts() if p['status'] == 'available']

    lost_posts.sort(key=lambda x: x['date_posted'], reverse=True)
    found_posts.sort(key=lambda x: x['date_posted'], reverse=True)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lost_posts": lost_posts,
            "found_posts": found_posts,
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


# --- Lost Post Routes ---

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
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


@app.post("/add-lost", response_class=HTMLResponse)
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
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "add_lost.html",
            {
                "request": request,
                "error": f"Database error: {e}",
                "categories": VALID_CATEGORIES,
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )


@app.get("/lost/{lost_id}", response_class=HTMLResponse)
async def view_lost_post(request: Request, lost_id: str, user_id: Optional[str] = Cookie(None)):
    """Display detailed view of a lost post"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = get_lost_post(lost_id)
    if not post:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Lost post not found",
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )

    # Get available found posts for matching
    found_posts = [p for p in get_found_posts() if p['status'] == 'available']

    return templates.TemplateResponse(
        "lost_detail.html",
        {
            "request": request,
            "post": post,
            "found_posts": found_posts,
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


@app.post("/delete-lost/{lost_id}", response_class=HTMLResponse)
async def remove_lost_post(request: Request, lost_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    delete_lost_post(lost_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- Found Post Routes ---

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
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


@app.post("/add-found", response_class=HTMLResponse)
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
            storage_location=storage_location
        )
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "add_found.html",
            {
                "request": request,
                "error": f"Database error: {e}",
                "categories": VALID_CATEGORIES,
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )


@app.get("/found/{found_id}", response_class=HTMLResponse)
async def view_found_post(request: Request, found_id: str, user_id: Optional[str] = Cookie(None)):
    """Display detailed view of a found post"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = get_found_post(found_id)
    if not post:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Found post not found",
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )

    # Get available lost posts for matching
    lost_posts = [p for p in get_lost_posts() if p['status'] == 'open']

    return templates.TemplateResponse(
        "found_detail.html",
        {
            "request": request,
            "post": post,
            "lost_posts": lost_posts,
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


@app.post("/delete-found/{found_id}", response_class=HTMLResponse)
async def remove_found_post(request: Request, found_id: str, user_id: Optional[str] = Cookie(None)):
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    delete_found_post(found_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- Matching Routes ---

@app.post("/claim", response_class=HTMLResponse)
async def claim_post(
        request: Request,
        lost_id: str = Form(...),
        found_id: str = Form(...),
        notes: str = Form(""),
        user_id: Optional[str] = Cookie(None)
):
    """Handle item claim/match creation"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    success, message = claim_item(lost_id, found_id, current_user['user_id'], notes)

    if success:
        return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Return to previous page with error
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": message,
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )


@app.get("/matches", response_class=HTMLResponse)
async def view_matches(request: Request, user_id: Optional[str] = Cookie(None)):
    """Display matches relevant to the user"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user['role'] == 'admin':
        matches = get_all_unresolved_matches()
    else:
        matches = get_matches_by_user(current_user['user_id'])

    return templates.TemplateResponse(
        "matches.html",
        {
            "request": request,
            "matches": matches,
            "user_id": current_user['user_id'],
            "user_name": current_user['name'],
            "user_role": current_user['role']
        }
    )


@app.post("/admin/resolve/{match_id}", response_class=HTMLResponse)
async def resolve_match(request: Request, match_id: int, user_id: Optional[str] = Cookie(None)):
    """Admin route to resolve a match"""
    current_user = get_current_user(user_id)
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if current_user['role'] != 'admin':
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unauthorized: Admin access required",
                "user_id": current_user['user_id'],
                "user_name": current_user['name'],
                "user_role": current_user['role']
            }
        )

    success, message = admin_resolve_match(match_id)
    return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)