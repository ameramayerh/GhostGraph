import asyncio
from app.database import engine
from sqlmodel import Session, SQLModel
from app.services.threat_intel import threat_intel_db
from app.models import Engagement, Finding

SQLModel.metadata.create_all(engine)

async def test_phase2():
    print("--- Testing Threat Intel ---")
    count = threat_intel_db.collection.count()
    print(f"Current Threat Intel Records: {count}")
    if count < 10:
        print("Emptying old mock data and forcing fresh ingestion...")
        threat_intel_db.client.delete_collection("threat_intelligence")
        threat_intel_db.collection = threat_intel_db.client.create_collection("threat_intelligence")
        threat_intel_db._ingest_initial_feeds()
        print(f"New count after live ingestion: {threat_intel_db.collection.count()}")
    else:
        print("Live CISA KEV already ingested or mock data is large.")
    
    print("\n--- Testing Attack Chain Correlation ---")
    from app.services.ai import ai_analyst
    
    with Session(engine) as session:
        # Get engagement 3 which we ran in the previous task
        eng = session.get(Engagement, 3)
        if eng and eng.findings:
            print(f"Found Engagement ID: {eng.id} with {len(eng.findings)} findings.")
            print("Triggering local Ollama LLM to generate Attack Chain (this may take a minute)...")
            
            findings_dicts = [{"title": f.title, "description": f.description, "evidence": f.evidence, "severity": f.severity} for f in eng.findings]
            try:
                scenario = ai_analyst.correlate_findings(findings_dicts)
                print("\n>>> Generated Attack Chain Scenario:")
                print(scenario)
            except Exception as e:
                print(f"Correlation failed: {e}")
        else:
            print("No suitable engagement found for correlation.")

if __name__ == "__main__":
    asyncio.run(test_phase2())
