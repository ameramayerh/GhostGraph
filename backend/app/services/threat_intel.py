import chromadb
import hashlib
import logging
import os
import re
from typing import List

logger = logging.getLogger(__name__)

class ThreatIntelService:
    def __init__(self):
        # Keep generated vector data outside tracked source files. Docker supplies
        # /app/data as a persistent volume; local runs use backend/data.
        default_data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectordb")
        db_path = os.getenv("GHOSTGRAPH_VECTOR_DB_PATH", default_data_dir)
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # GhostGraph supplies deterministic local vectors to avoid a model download.
        self.collection = self.client.get_or_create_collection(
            name="threat_intelligence", embedding_function=None
        )
        
        if self.collection.count() == 0:
            self._ingest_initial_feeds()

    def _ingest_initial_feeds(self):
        """Optionally fetches CISA KEV, otherwise seeds a useful offline catalog."""
        if os.getenv("GHOSTGRAPH_FETCH_THREAT_INTEL", "false").lower() not in {"1", "true", "yes"}:
            self._ingest_builtin_data()
            return

        logger.info("Loading the CISA Known Exploited Vulnerabilities catalog")
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
                logger.info("Loaded %s CISA KEV records", len(documents))
        except Exception as e:
            logger.warning("CISA KEV download failed; using built-in guidance: %s", e)
            self._ingest_builtin_data()

    def _ingest_builtin_data(self):
        """Seed a small offline collection of defensive security guidance."""
        documents = [
            "Use HTTP Strict Transport Security after validating HTTPS deployment to reduce protocol downgrade risk.",
            "Set Secure, HttpOnly, and an appropriate SameSite policy on session cookies.",
            "Do not store credentials in source code. Use protected configuration and rotate exposed secrets.",
            "Use Content-Security-Policy frame-ancestors or X-Frame-Options to reduce clickjacking risk.",
            "MITRE ATT&CK T1552 describes adversary attempts to locate unsecured credentials in files and other storage locations.",
            "Apply authentication and object-level authorization consistently to API and GraphQL operations.",
        ]
        
        ids = [f"intel_{i}" for i in range(len(documents))]
        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=[{"source": "Built-in GhostGraph guidance", "type": "Security Guidance"} for _ in documents],
            embeddings=[self._embed(document) for document in documents],
        )
        logger.info("Loaded %s built-in security guidance records", len(documents))

    @staticmethod
    def _embed(text: str, dimensions: int = 64) -> List[float]:
        """Create a deterministic token-hashing vector without a model download."""
        vector = [0.0] * dimensions
        for token in re.findall(r"[a-z0-9_]+", text.lower()):
            index = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big") % dimensions
            vector[index] += 1.0
        length = sum(value * value for value in vector) ** 0.5
        return [value / length for value in vector] if length else vector

    def retrieve_context(self, finding_title: str, description: str = "") -> str:
        """
        Query the local ChromaDB collection for related defensive guidance.
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
            logger.warning("Threat-intelligence query failed: %s", e)
            
        return "No specific threat intel context retrieved."

threat_intel_db = ThreatIntelService()
