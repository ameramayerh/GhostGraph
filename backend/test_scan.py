import asyncio
from sqlmodel import Session, SQLModel
from app.models import Engagement, Finding
from app.database import engine
from app.api import trigger_scan

# Ensure DB tables exist
SQLModel.metadata.create_all(engine)

async def run_test():
    with Session(engine) as session:
        # Create a test engagement
        eng = Engagement(
            name="Automated Test Engagement",
            scope="http://example.com",
            authorized_by="Admin"
        )
        session.add(eng)
        session.commit()
        session.refresh(eng)
        
        print(f"Created Engagement ID: {eng.id} for target {eng.scope}")
        print("Triggering dual engine scan (Playwright + Nuclei)...")
        
        # Trigger scan
        result = await trigger_scan(eng.id, session=session)
        print("Scan result:", result)
        
        # Fetch findings
        from sqlmodel import select
        findings = session.exec(select(Finding).where(Finding.engagement_id == eng.id)).all()
        print(f"\nTotal findings saved in DB: {len(findings)}")
        print("---- Findings Summary ----")
        for f in findings:
            print(f"[{f.severity}] {f.title} (Source: {f.category})")

if __name__ == "__main__":
    asyncio.run(run_test())
