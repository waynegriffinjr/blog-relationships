from sqlalchemy import create_engine, String, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, 
    relationship, Session
)
from typing import Optional

engine = create_engine("sqlite:///blog_relations.db", echo=False) # Creates a SQLite database file named blog_relations.db and turns off SQL echo logging.

class Base(DeclarativeBase):
    pass

# --- Association table for many-to-many (Post <-> Tag) ---
post_tags = Table(  # Defines a plain table that connects posts and tags via foreign keys—this is the join table for the many‑to‑many relationship.
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

# --- Models ---

class Author(Base):
    __tablename__ = "authors"
    
    id: Mapped[int]   = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # One-to-many: one author -> many posts
    posts: Mapped[list["Post"]] = relationship(back_populates="author") # Provides a readable string representation for debugging and printing.
    
    def __repr__(self):
        return f"Author(name='{self.name}')"
    

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    
    # Foreign key to authors (the "many" side stores the FK)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    
    # Relationship back to author
    author: Mapped["Author"] = relationship(back_populates="posts")
    
    # Many-to-many: posts <-> tags
    tags: Mapped[list["Tag"]] = relationship(
        secondary=post_tags, back_populates="posts"
    )
    
    def __repr__(self):
        return f"Post(title='{self.title}')"

    
class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Many-to-many: tags <-> posts
    posts: Mapped[list["Post"]] = relationship(
        secondary=post_tags, back_populates="tags"
    )
    
    def __repr__(self):
        return f"Tag(name='{self.name}')"

# Create all tables
Base.metadata.create_all(engine)
print("Tables created!\n")


# Creates related data.
with Session(engine) as session:
    # Create authors
    alice = Author(name="Alice Park")
    bob = Author(name="Bob Martinez")
    
    # Create tags
    python_tag = Tag(name="python")
    sql_tag = Tag(name="sql")
    tutorial_tag = Tag(name="tutorial")
    beginner_tag = Tag(name="beginner")
    
    # Create posts and assign relationships
    post1 = Post(
        title="Getting Started with Python",
        content="Python is a versatile language...",
        author=alice,  # Set the relationship directly
        tags=[python_tag, tutorial_tag, beginner_tag]  # Many-to-many as a list. 
    )
    
    post2 = Post(
        title="SQL Joins Explained",
        content="Joins combine data from multiple tables...",
        author=alice,
        tags=[sql_tag, tutorial_tag]
    )
    
    post3 = Post(
        title="Python for Data Science",
        content="Data science with Python starts with...",
        author=bob,
        tags=[python_tag]
    )
    
    # Add everything — SQLAlchemy handles the relationships
    session.add_all([alice, bob])
    session.commit()
    
    print("Data created!")
    
    
# Navigate one-to-many relationships. 
with Session(engine) as session:
    # Get all authors and their posts
    print("\n=== Authors and Their Posts ===")
    authors = session.query(Author).all()
    for author in authors:
        print(f"\n  {author.name} ({len(author.posts)} posts):")
        for post in author.posts:
            print(f"    - {post.title}")
    
    # Navigate the other direction: from post to author
    print("\n=== Post Authors ===")
    posts = session.query(Post).all()
    for post in posts:
        print(f"  '{post.title}' by {post.author.name}")
        
# Navigate many-to-many relationships. 
with Session(engine) as session:
    # Posts with their tags
    print("\n=== Posts and Tags ===")
    posts = session.query(Post).all()
    for post in posts:
        tag_names = [tag.name for tag in post.tags]
        print(f"  '{post.title}': {', '.join(tag_names)}")
    
    # Tags and which posts use them
    print("\n=== Tags and Their Posts ===")
    tags = session.query(Tag).all()
    for tag in tags:
        post_titles = [post.title for post in tag.posts]
        print(f"  #{tag.name}: {', '.join(post_titles)}")


# Adding to existing relationships.
with Session(engine) as session:
    # Add a new tag to an existing post
    python_for_ds = session.query(Post).filter_by(
        title="Python for Data Science"
    ).first()
    
    beginner = session.query(Tag).filter_by(name="beginner").first()
    
    python_for_ds.tags.append(beginner)  # Just append to the list!
    session.commit()
    
    print("\n=== Updated Tags for 'Python for Data Science' ===")
    tag_names = [tag.name for tag in python_for_ds.tags]
    print(f"  Tags: {', '.join(tag_names)}")