import os
import tempfile
from pathlib import Path


TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="ghostgraph_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DATA_DIR / 'test.db').as_posix()}"
os.environ["GHOSTGRAPH_VECTOR_DB_PATH"] = str(TEST_DATA_DIR / "vectordb")
