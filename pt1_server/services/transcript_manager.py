"""
Agent Transcript Management Module
Handles transcript upload, storage, and retrieval for agent sessions
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import UploadFile
import json


class TranscriptManager:
    def __init__(self, transcript_dir: str = "uploads/transcripts"):
        self.transcript_dir = Path(transcript_dir)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)

    def _generate_transcript_id(self, client_id: str) -> str:
        """Generate transcript ID with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # microseconds to milliseconds
        return f"{client_id}_{timestamp}"

    async def upload_transcript(
        self,
        client_id: str,
        transcript_file: UploadFile,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Upload and store agent transcript

        Args:
            client_id: Agent client ID
            transcript_file: Uploaded transcript file
            metadata: Optional metadata (run_id, etc.)

        Returns:
            transcript_id: Generated transcript identifier
        """
        transcript_id = self._generate_transcript_id(client_id)

        # Save transcript content
        transcript_path = self.transcript_dir / f"{transcript_id}.txt"
        content = await transcript_file.read()

        with open(transcript_path, "wb") as f:
            f.write(content)

        # Save metadata if provided
        if metadata:
            metadata_path = self.transcript_dir / f"{transcript_id}_metadata.json"
            metadata_info = {
                "client_id": client_id,
                "transcript_id": transcript_id,
                "filename": transcript_file.filename,
                "upload_time": datetime.now().isoformat(),
                "file_size": len(content),
                **metadata
            }

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata_info, f, indent=2, ensure_ascii=False)

        return transcript_id

    def list_transcripts(
        self,
        client_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List available transcripts

        Args:
            client_id: Filter by specific client ID
            limit: Maximum number of transcripts to return

        Returns:
            List of transcript information
        """
        transcripts = []

        # Get all transcript files
        pattern = f"{client_id}_*.txt" if client_id else "*.txt"
        transcript_files = list(self.transcript_dir.glob(pattern))

        # Sort by modification time (newest first)
        transcript_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for transcript_file in transcript_files[:limit]:
            if transcript_file.name.endswith('.txt'):
                transcript_id = transcript_file.stem

                # Try to load metadata
                metadata_path = self.transcript_dir / f"{transcript_id}_metadata.json"
                metadata = {}

                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                    except (json.JSONDecodeError, Exception):
                        pass

                # Basic file info
                stat_info = transcript_file.stat()
                transcript_info = {
                    "transcript_id": transcript_id,
                    "client_id": transcript_id.split('_')[0] if '_' in transcript_id else "unknown",
                    "file_size": stat_info.st_size,
                    "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    **metadata
                }

                transcripts.append(transcript_info)

        return transcripts

    def get_transcript_content(self, transcript_id: str) -> Optional[str]:
        """
        Get transcript content by ID

        Args:
            transcript_id: Transcript identifier

        Returns:
            Transcript content or None if not found
        """
        transcript_path = self.transcript_dir / f"{transcript_id}.txt"

        if not transcript_path.exists():
            return None

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(transcript_path, "r", encoding="cp1252") as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None

    def get_transcript_metadata(self, transcript_id: str) -> Optional[Dict]:
        """
        Get transcript metadata by ID

        Args:
            transcript_id: Transcript identifier

        Returns:
            Metadata dict or None if not found
        """
        metadata_path = self.transcript_dir / f"{transcript_id}_metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def delete_transcript(self, transcript_id: str) -> bool:
        """
        Delete transcript and its metadata

        Args:
            transcript_id: Transcript identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        transcript_path = self.transcript_dir / f"{transcript_id}.txt"
        metadata_path = self.transcript_dir / f"{transcript_id}_metadata.json"

        deleted = False

        if transcript_path.exists():
            try:
                transcript_path.unlink()
                deleted = True
            except Exception:
                pass

        if metadata_path.exists():
            try:
                metadata_path.unlink()
            except Exception:
                pass

        return deleted

    def cleanup_old_transcripts(self, days: int = 30) -> int:
        """
        Clean up transcripts older than specified days

        Args:
            days: Age threshold in days

        Returns:
            Number of files deleted
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_time.timestamp()

        deleted_count = 0

        for file_path in self.transcript_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_timestamp:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    pass

        return deleted_count


# Global instance
_transcript_manager = None


def get_transcript_manager() -> TranscriptManager:
    """Dependency injection for FastAPI"""
    global _transcript_manager
    if _transcript_manager is None:
        _transcript_manager = TranscriptManager()
    return _transcript_manager