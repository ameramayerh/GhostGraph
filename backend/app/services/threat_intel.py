import chromadb
import hashlib
import os
import re
from typing import List

class ThreatIntelService:
    def __init__(self):
        # Keep generated vector data outside tracked source files. Docker supplies
        # /app/data as a persistent volume; local runs use backend/data.
        default_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectordb")
        db_path = os.getenv("GHOSTGRAPH_VECTOR_DB_PATH", default_data_dir)
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get the collection for Threat Intelligence
        # Embeddings are supplied by GhostGraph itself. This avoids Chroma downloading a
        # sentence-transformer model the first time the app starts.
        self.collection = self.client.get_or_create_collection(
            name="threat_intelligence", embedding_function=None
        )
        
        # Mock ingestion of NVD / MITRE STIX JSON feeds if empty
        if self.collection.count() == 0:
            self._ingest_initial_feeds()

    def _ingest_initial_feeds(self):
        """Optionally fetches CISA KEV, otherwise seeds a useful offline catalog."""
        if os.getenv("GHOSTGRAPH_FETCH_THREAT_INTEL", "false").lower() not in {"1", "true", "yes"}:
            self._ingest_mock_data()
            return

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
                        metadatas=metadatas[i:i+batch_size],
                        embeddings=[self._embed(document) for document in documents[i:i+batch_size]],
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
        
        ids = [f"intel_{i}" for i in range(len(documents))]
        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=[{"source": "Built-in GhostGraph guidance", "type": "Security Guidance"} for _ in documents],
            embeddings=[self._embed(document) for document in documents],
        )
        print(f"Ingested {len(documents)} threat intel records.")

    @staticmethod
    def _embed(text: str, dimensions: int = 64) -> List[float]:
        """Create a small deterministic local vector; it needs no model download."""
        vector = [0.0] * dimensions
        for token in re.findall(r"[a-z0-9_]+", text.lower()):
            index = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big") % dimensions
            vector[index] += 1.0
        length = sum(value * value for value in vector) ** 0.5
        return [value / length for value in vector] if length else vector

    def retrieve_context(self, finding_title: str, description: str = "") -> str:
        """
        Queries the ChromaDB vector store for semantically similar threat intelligence.
        """
        query_text = f"{finding_title} {description}"
        try:
            results = self.collection.query(
                query_embeddings=[self._embed(query_text)],
                n_results=2
            )
            if results['documents'] and len(results['documents'][0]) > 0:
                context = " | ".join(results['documents'][0])
                return context
        except Exception as e:
            print(f"Vector DB query failed: {e}")
            
        return "No specific threat intel context retrieved."

threat_intel_db = ThreatIntelService()
