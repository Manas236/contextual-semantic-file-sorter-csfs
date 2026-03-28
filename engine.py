import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("CSFS.Engine")

class SemanticFileEngine:
    def __init__(self, collection_name: str = "csfs_index", persist_dir: str = "./.csfs_data"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_connection(
            name=collection_name,
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        
    def _read_file_content(self, file_path: Path, max_chars: int = 5000) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_chars)
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return ""

    def index_files(self, source_dir: str):
        source = Path(source_dir)
        files = [f for f in source.rglob('*') if f.is_file()]
        
        for file in files:
            content = self._read_file_content(file)
            if content:
                self.collection.add(
                    documents=[content],
                    metadatas=[{"path": str(file), "name": file.name}],
                    ids=[str(file.absolute())]
                )
        logger.info(f"Indexed {len(files)} files.")

    def suggest_path(self, file_path: Path, llm_client) -> str:
        """
        Uses an external LLM interface to determine the semantic destination.
        """
        content = self._read_file_content(file_path)
        prompt = f"Analyze the following content and suggest a directory name for organization: {content[:1000]}"
        
        # Interface with local LLM (e.g., Ollama)
        response = llm_client.generate(prompt)
        return response.strip().replace(" ", "_")

    def move_file(self, source: Path, destination_root: Path, dry_run: bool = True):
        dest_dir = destination_root / self.suggest_path(source, None)
        dest_path = dest_dir / source.name

        if dry_run:
            logger.info(f"[DRY RUN] Would move {source} -> {dest_path}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest_path))
            logger.info(f"Moved {source.name} to {dest_dir}")

    def query_semantic_context(self, query: str, n_results: int = 5) -> List[Dict]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return [
            {"path": m["path"], "name": m["name"]} 
            for m in results["metadatas"][0]
        ]

    def verify_integrity(self, file_list: List[Path]) -> bool:
        """Ensures that no files are lost during batch operations."""
        return all(f.exists() for f in file_list)

    def batch_process(self, source_dir: str, target_dir: str, dry_run: bool = True):
        source = Path(source_dir)
        target = Path(target_dir)
        
        for file in source.rglob('*'):
            if file.is_file():
                self.move_file(file, target, dry_run=dry_run)