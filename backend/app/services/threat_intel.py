import chromadb
from chromadb.config import Settings
import json
import os

class ThreatIntelService:
    def __init__(self):
        # Initialize ChromaDB client pointing to local persistence directory
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "vectordb")
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get the collection for Threat Intelligence
        self.collection = self.client.get_or_create_collection(name="threat_intelligence")
        
        # Mock ingestion of NVD / MITRE STIX JSON feeds if empty
        if self.collection.count() == 0:
            self._ingest_initial_feeds()

    def _ingest_initial_feeds(self):
        """Fetches and ingests the live CISA KEV catalog."""
        print("Ingesting CISA Known Exploited Vulnerabilities into ChromaDB...")
        try:
            import requests
            response = requests.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", timeout=15)
            response.raise_for_status()
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            
            # For performance, ingest the latest 500
            vulnerabilities = sorted(vulnerabilities, key=lambda x: x.get("dateAdded", ""), reverse=True)[:500]
            
            documents = []
            ids = []
            metadatas = []
            
            for v in vulnerabilities:
                doc = f"CVE: {v.get('cveID')} | Vendor: {v.get('vendorProject')} | Product: {v.get('product')} | Vulnerability: {v.get('vulnerabilityName')} | Description: {v.get('shortDescription')} | Action: {v.get('requiredAction')}"
                documents.append(doc)
                ids.append(v.get('cveID'))
                metadatas.append({
                    "id": v.get('cveID'),
                    "source": "CISA KEV",
                    "type": "Vulnerability"
                })
                
            if documents:
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    self.collection.add(
                        documents=documents[i:i+batch_size],
                        ids=ids[i:i+batch_size],
                        metadatas=metadatas[i:i+batch_size]
                    )
                print(f"Ingested {len(documents)} live threat intel records from CISA.")
        except Exception as e:
            print(f"Failed to ingest CISA KEV: {e}")
            self._ingest_mock_data()

    def _ingest_mock_data(self):
        """Simulates downloading and ingesting massive JSON feeds into the Vector DB."""
        print("Ingesting initial threat intelligence feeds into ChromaDB...")
        documents = [
            "CISA KEV notes that lack of Strict-Transport-Security (HSTS) allows SSL stripping attacks which are actively used to capture credentials on insecure network boundaries.",
            "CISA Alert: Session hijacking via insecure cookies is a common initial access vector for ransomware operators. Always set Secure and HttpOnly flags.",
            "GitHub Advisory: Hardcoded secrets in client-side code are the #1 cause of major data breaches. Rotate exposed AWS/GCP keys immediately.",
            "OWASP Top 10: UI Redressing (Clickjacking) via missing X-Frame-Options is frequently chained with CSRF to force state-changing actions.",
            "MITRE ATT&CK T1552: Attackers search local file systems and JS bundles for unsecured credentials and API keys.",
            "NVD CVE-2023-XXXX: Missing authentication on GraphQL endpoints allows unauthorized data exfiltration.",
        ]
        
        # Add to vector DB (Chroma handles embedding automatically via sentence-transformers default)
        ids = [f"intel_{i}" for i in range(len(documents))]
        self.collection.add(
            documents=documents,
            ids=ids
        )
        print(f"Ingested {len(documents)} threat intel records.")

    def retrieve_context(self, finding_title: str, description: str = "") -> str:
        """
        Queries the ChromaDB vector store for semantically similar threat intelligence.
        """
        query_text = f"{finding_title} {description}"
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=2
            )
            if results['documents'] and len(results['documents'][0]) > 0:
                context = " | ".join(results['documents'][0])
                return context
        except Exception as e:
            print(f"Vector DB query failed: {e}")
            
        return "No specific threat intel context retrieved."

threat_intel_db = ThreatIntelService()
