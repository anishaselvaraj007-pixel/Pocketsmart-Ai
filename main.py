from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from dotenv import load_dotenv
from google import genai

import os
from datetime import datetime
import hashlib
import secrets

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    inspect,
    text
)

from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")


# ============================================================
# GEMINI SETUP
# ============================================================

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# DATABASE SETUP
# ============================================================

DATABASE_URL = "sqlite:///./pocketsmart.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ============================================================
# RECOMMENDATION HISTORY MODEL
# ============================================================

class RecommendationHistory(Base):

    __tablename__ = "recommendation_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    recommendation_type = Column(
        String(50),
        nullable=False
    )

    details = Column(
        Text,
        nullable=False
    )

    ai_message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        String(50),
        nullable=True
    )


# ============================================================
# USER MODEL
# ============================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(
    password: str,
    stored_password: str
) -> bool:

    try:

        salt, saved_hash = stored_password.split("$")

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

        return secrets.compare_digest(
            password_hash,
            saved_hash
        )

    except ValueError:

        return False


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_database():

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if "recommendation_history" not in tables:
        return

    columns = [
        column["name"]
        for column in inspector.get_columns(
            "recommendation_history"
        )
    ]

    if "created_at" not in columns:

        with engine.begin() as connection:

            connection.execute(
                text(
                    "ALTER TABLE recommendation_history "
                    "ADD COLUMN created_at VARCHAR(50)"
                )
            )


migrate_database()


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="PocketSmart AI"
)


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

if not SESSION_SECRET_KEY:

    SESSION_SECRET_KEY = secrets.token_hex(32)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY
)


# ============================================================
# TEMPLATES
# ============================================================

templates = Jinja2Templates(
    directory="templates"
)


# ============================================================
# LOGIN CHECK
# ============================================================

def require_login(request: Request):

    if "user_id" not in request.session:

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return None


# ============================================================
# HOME / LANDING PAGE
# ============================================================

@app.get("/")
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ============================================================
# HOME INTERIOR PAGE
# ============================================================

@app.get("/home")
async def home_planner(request: Request):

    login_check = require_login(request)

    if login_check:
        return login_check

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={}
    )


# ============================================================
# GENERATE HOME RECOMMENDATION
# ============================================================

@app.post("/generate-home")
async def generate_home(
    request: Request,
    budget: int = Form(...),
    room: str = Form(...),
    item: str = Form(...),
    quantity: int = Form(...)
):

    login_check = require_login(request)

    if login_check:
        return login_check

    recommendations = f"""
🏠 PocketSmart AI Home Recommendation

💰 Budget: ₹{budget:,}
🛋️ Room: {room}
💡 Required Item: {item}
🔢 Quantity: {quantity}

Here are some practical and budget-friendly recommendations:

• LED Lights
• Ceiling Fan
• Bedroom Furniture
• Decorative Items

💡 Tip:
Choose energy-efficient products and compare prices before purchasing.
"""

    ai_message = recommendations

    if client:

        try:

            prompt = f"""
You are PocketSmart AI, a smart home interior assistant.

Give practical and affordable home interior recommendations.

Budget: ₹{budget}
Room: {room}
Required Item: {item}
Quantity: {quantity}

Include:

1. Product recommendation
2. Estimated price
3. Why it is suitable
4. Placement suggestion
5. Remaining budget

Make sure recommendations stay within the user's budget.

Keep the answer short, clear and useful.
Use Indian Rupees.
"""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if response.text:

                ai_message = response.text

        except Exception:

            pass


    # SAVE HISTORY

    db = SessionLocal()

    try:

        history = RecommendationHistory(

            recommendation_type="Home Interior",

            details=f"""
Budget: ₹{budget:,}
Room: {room}
Item: {item}
Quantity: {quantity}
""",

            ai_message=ai_message,

            created_at=datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            )
        )

        db.add(history)

        db.commit()

    finally:

        db.close()


    return templates.TemplateResponse(

        request=request,

        name="recommendations.html",

        context={

            "budget": budget,
            "room": room,
            "item": item,
            "quantity": quantity,
            "recommendations": recommendations,
            "ai_message": ai_message

        }
    )


# ============================================================
# PARTY PAGE
# ============================================================

@app.get("/party")
async def party_planner(request: Request):

    login_check = require_login(request)

    if login_check:
        return login_check

    return templates.TemplateResponse(
        request=request,
        name="party.html",
        context={}
    )


# ============================================================
# GENERATE PARTY RECOMMENDATION
# ============================================================

@app.post("/generate-party")
async def generate_party(
    request: Request,
    budget: int = Form(...),
    guests: int = Form(...),
    event_type: str = Form(...),
    venue: str = Form(...)
):

    login_check = require_login(request)

    if login_check:
        return login_check


    catering = int(budget * 0.50)

    decoration = int(budget * 0.15)

    entertainment = int(budget * 0.15)

    cake_extras = int(budget * 0.10)


    total_spending = (
        catering
        + decoration
        + entertainment
        + cake_extras
    )

    remaining = budget - total_spending


    if guests > 0:

        cost_per_guest = catering // guests

    else:

        cost_per_guest = 0


    ai_message = f"""
🎉 PocketSmart AI Party Plan

💰 Total Budget: ₹{budget:,}
👥 Guests: {guests}
🎊 Event: {event_type}
🏨 Venue: {venue}

🍽️ Catering
₹{catering:,}

🎈 Decoration
₹{decoration:,}

🎵 Entertainment
₹{entertainment:,}

🎂 Cake & Extras
₹{cake_extras:,}

💵 Total Planned Spending
₹{total_spending:,}

💰 Remaining Budget
₹{remaining:,}

👤 Approximate Catering Cost Per Guest
₹{cost_per_guest:,}

💡 PocketSmart Tip:
Keep some money reserved for unexpected expenses.
"""


    if client:

        try:

            prompt = f"""
You are PocketSmart AI, a smart party budget assistant.

Create a practical party budget plan.

Total Budget: ₹{budget}
Number of Guests: {guests}
Event Type: {event_type}
Venue: {venue}

Calculate realistic amounts for:

1. Catering
2. Decoration
3. Entertainment
4. Cake and Extras

IMPORTANT:

- Total spending must NOT exceed ₹{budget}.
- Consider the number of guests.
- Calculate approximate catering cost per guest.
- Mention remaining budget.
- Give practical suggestions.
- Use Indian Rupees.
- Keep the answer simple and easy to understand.

Format the answer clearly with headings and amounts.
"""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if response.text:

                ai_message = response.text

        except Exception:

            pass


    db = SessionLocal()

    try:

        history = RecommendationHistory(

            recommendation_type="Party Planner",

            details=f"""
Budget: ₹{budget:,}
Guests: {guests}
Event: {event_type}
Venue: {venue}
""",

            ai_message=ai_message,

            created_at=datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            )
        )

        db.add(history)

        db.commit()

    finally:

        db.close()


    return templates.TemplateResponse(

        request=request,

        name="party_recommendations.html",

        context={

            "budget": budget,
            "guests": guests,
            "event_type": event_type,
            "venue": venue,
            "ai_message": ai_message

        }
    )


# ============================================================
# JEWELRY PAGE
# ============================================================

@app.get("/jewelry")
async def jewelry_planner(request: Request):

    login_check = require_login(request)

    if login_check:
        return login_check

    return templates.TemplateResponse(
        request=request,
        name="jewelry.html",
        context={}
    )


# ============================================================
# GENERATE JEWELRY RECOMMENDATION
# ============================================================

@app.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: int = Form(...),
    occasion: str = Form(...),
    style: str = Form(...),
    outfit: str = Form(...)
):

    login_check = require_login(request)

    if login_check:
        return login_check


    necklace = int(budget * 0.40)

    earrings = int(budget * 0.25)

    bracelet = int(budget * 0.15)

    ring = int(budget * 0.10)


    total = (
        necklace
        + earrings
        + bracelet
        + ring
    )

    remaining = budget - total


    ai_message = f"""
💎 PocketSmart AI Jewelry Recommendation

💰 Budget: ₹{budget:,}
🎉 Occasion: {occasion}
✨ Style: {style}
👗 Outfit: {outfit}

💍 Recommended Jewelry

📿 Necklace
₹{necklace:,}

✨ Earrings
₹{earrings:,}

💫 Bracelet
₹{bracelet:,}

💍 Ring
₹{ring:,}

💵 Estimated Total
₹{total:,}

💰 Remaining Budget
₹{remaining:,}

💡 PocketSmart Tip:
Choose jewelry that complements both your outfit and occasion.
"""


    if client:

        try:

            prompt = f"""
You are PocketSmart AI, a smart jewelry recommendation assistant.

Recommend jewelry based on these details.

Budget: ₹{budget}
Occasion: {occasion}
Style: {style}
Outfit: {outfit}

Suggest:

1. Necklace
2. Earrings
3. Bracelet
4. Ring

For each recommendation include:

- Estimated price
- Why it matches
- Style suggestion

IMPORTANT:

- Total estimated cost must stay within ₹{budget}.
- Use Indian Rupees.
- Keep recommendations practical.
- Match the jewelry with the occasion, style and outfit.
- Keep the answer clear and easy to understand.
"""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if response.text:

                ai_message = response.text

        except Exception:

            pass


    db = SessionLocal()

    try:

        history = RecommendationHistory(

            recommendation_type="Jewelry",

            details=f"""
Budget: ₹{budget:,}
Occasion: {occasion}
Style: {style}
Outfit: {outfit}
""",

            ai_message=ai_message,

            created_at=datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            )
        )

        db.add(history)

        db.commit()

    finally:

        db.close()


    return templates.TemplateResponse(

        request=request,

        name="jewelry_recommendations.html",

        context={

            "budget": budget,
            "occasion": occasion,
            "style": style,
            "outfit": outfit,
            "ai_message": ai_message

        }
    )


# ============================================================
# REGISTER PAGE
# ============================================================

@app.get("/register")
async def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )


# ============================================================
# REGISTER USER
# ============================================================

@app.post("/register")
async def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:

            return templates.TemplateResponse(

                request=request,

                name="register.html",

                context={
                    "error": "Email already registered!"
                }
            )


        password_hash = hash_password(
            password
        )


        new_user = User(

            name=name,

            email=email,

            password_hash=password_hash

        )


        db.add(new_user)

        db.commit()


        return RedirectResponse(
            url="/login",
            status_code=303
        )

    finally:

        db.close()


# ============================================================
# LOGIN PAGE
# ============================================================

@app.get("/login")
async def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


# ============================================================
# LOGIN USER
# ============================================================

@app.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )


        if not user or not verify_password(
            password,
            user.password_hash
        ):

            return templates.TemplateResponse(

                request=request,

                name="login.html",

                context={
                    "error": "Invalid email or password!"
                }
            )


        request.session["user_id"] = user.id

        request.session["user_name"] = user.name

        request.session["user_email"] = user.email


        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    finally:

        db.close()


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
async def dashboard(request: Request):

    login_check = require_login(request)

    if login_check:
        return login_check


    db = SessionLocal()

    try:

        total = db.query(
            RecommendationHistory
        ).count()


        home_count = db.query(
            RecommendationHistory
        ).filter(
            RecommendationHistory.recommendation_type
            == "Home Interior"
        ).count()


        party_count = db.query(
            RecommendationHistory
        ).filter(
            RecommendationHistory.recommendation_type
            == "Party Planner"
        ).count()


        jewelry_count = db.query(
            RecommendationHistory
        ).filter(
            RecommendationHistory.recommendation_type
            == "Jewelry"
        ).count()

    finally:

        db.close()


    return templates.TemplateResponse(

        request=request,

        name="dashboard.html",

        context={

            "total": total,

            "home_count": home_count,

            "party_count": party_count,

            "jewelry_count": jewelry_count

        }
    )


# ============================================================
# LOGOUT
# ============================================================

@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303
    )


# ============================================================
# RECOMMENDATION HISTORY
# ============================================================

@app.get("/history")
async def history(request: Request):

    login_check = require_login(request)

    if login_check:
        return login_check


    db = SessionLocal()

    try:

        history_items = (

            db.query(
                RecommendationHistory
            )

            .order_by(
                RecommendationHistory.id.desc()
            )

            .all()

        )

    finally:

        db.close()


    return templates.TemplateResponse(

        request=request,

        name="history.html",

        context={
            "history_items": history_items
        }

    )


# ============================================================
# DELETE HISTORY
# ============================================================

@app.post("/delete-history/{history_id}")
async def delete_history(
    request: Request,
    history_id: int
):

    login_check = require_login(request)

    if login_check:
        return login_check


    db = SessionLocal()

    try:

        history_item = (

            db.query(
                RecommendationHistory
            )

            .filter(
                RecommendationHistory.id
                == history_id
            )

            .first()

        )


        if history_item:

            db.delete(history_item)

            db.commit()

    finally:

        db.close()


    return RedirectResponse(
        url="/history",
        status_code=303
    )