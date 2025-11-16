"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List

# ---------------------------------------------
# Player Landing Page Schemas
# ---------------------------------------------

class LinkItem(BaseModel):
    title: str = Field(..., description="Custom title for the link")
    url: str = Field(..., description="URL to external resource")
    icon: Optional[str] = Field(None, description="Lucide icon name (e.g., 'ExternalLink', 'FileText', 'Youtube')")

class SeasonStats(BaseModel):
    season: str = Field(..., description="Season label, e.g., 2023/24")
    club: Optional[str] = None
    league: Optional[str] = None
    games: Optional[int] = 0
    goals: Optional[int] = 0
    assists: Optional[int] = 0
    clean_sheets: Optional[int] = 0
    minutes: Optional[int] = 0

class Player(BaseModel):
    """
    Player landing page profile
    Collection name: "player"
    """
    slug: str = Field(..., description="Unique URL slug for the player, e.g., 'john-doe'")
    name: str
    position: str
    age: Optional[int] = None
    country: Optional[str] = None
    current_club: Optional[str] = None
    league: Optional[str] = None

    photo_url: Optional[str] = Field(None, description="URL to profile photo")
    highlight_title: Optional[str] = Field("Best Highlights", description="Title shown above main video")
    highlight_url: Optional[str] = Field(None, description="YouTube/Vimeo/file URL to main highlight video")
    highlight_description: Optional[str] = None

    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    dominant_foot: Optional[str] = None
    main_position: Optional[str] = None
    secondary_positions: Optional[List[str]] = []
    past_clubs: Optional[List[str]] = []

    bio: Optional[str] = None

    links: Optional[List[LinkItem]] = []
    stats: Optional[List[SeasonStats]] = []

    contact_email: Optional[EmailStr] = Field(None, description="Player's email to receive contact requests")

class Testimonial(BaseModel):
    """
    Testimonials associated with a player
    Collection name: "testimonial"
    """
    player_slug: str
    author: Optional[str] = None
    role: Optional[str] = None
    quote: str

class ContactSubmission(BaseModel):
    """
    Contact & Trial Requests
    Collection name: "contactsubmission"
    """
    player_slug: str
    name: str
    role: str  # coach / scout / agent / club
    club_name: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    country: Optional[str] = None
    message: Optional[str] = None

# Example schemas kept for reference (can be removed if not needed)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
