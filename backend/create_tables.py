"""
Quick script to create all database tables.
Run: python create_tables.py
"""
from database import Base, engine
from models import User, Workspace, WorkspaceMember, Lead, Campaign, Automation, AutomationLog, Conversation, Message, Subscription

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    print("\nTables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
