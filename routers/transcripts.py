from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional, Dict, List
from services.transcript_manager import get_transcript_manager, TranscriptManager
from auth import verify_token
import json

router = APIRouter()


@router.post("/agent_transcript/{client_id}")
async def upload_agent_transcript(
    client_id: str,
    transcript_file: UploadFile = File(...),
    run_id: Optional[str] = None,
    metadata: Optional[str] = None,
    transcript_mgr: TranscriptManager = Depends(get_transcript_manager),
    token: str = Depends(verify_token)
):
    """
    Upload agent transcript (not tied to specific command)

    Args:
        client_id: Agent client ID
        transcript_file: PowerShell transcript file
        run_id: Optional run identifier (polling cycle number)
        metadata: Optional JSON metadata string
    """
    try:
        # Parse metadata if provided
        metadata_dict = {}
        if run_id:
            metadata_dict["run_id"] = run_id

        if metadata:
            try:
                extra_metadata = json.loads(metadata)
                metadata_dict.update(extra_metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")

        # Upload transcript
        transcript_id = await transcript_mgr.upload_transcript(
            client_id=client_id,
            transcript_file=transcript_file,
            metadata=metadata_dict
        )

        return {
            "status": "success",
            "transcript_id": transcript_id,
            "message": f"Transcript uploaded for client {client_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload transcript: {str(e)}")


@router.get("/agent_transcripts")
async def list_agent_transcripts(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of transcripts to return"),
    transcript_mgr: TranscriptManager = Depends(get_transcript_manager),
    token: str = Depends(verify_token)
):
    """
    List available agent transcripts

    Args:
        client_id: Optional filter by client ID
        limit: Maximum number of transcripts to return
    """
    try:
        transcripts = transcript_mgr.list_transcripts(client_id=client_id, limit=limit)

        return {
            "transcripts": transcripts,
            "count": len(transcripts),
            "filtered_by_client": client_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list transcripts: {str(e)}")


@router.get("/agent_transcript/{transcript_id}")
async def get_agent_transcript(
    transcript_id: str,
    format: str = Query("content", regex="^(content|metadata|both)$"),
    transcript_mgr: TranscriptManager = Depends(get_transcript_manager),
    token: str = Depends(verify_token)
):
    """
    Get agent transcript content and/or metadata

    Args:
        transcript_id: Transcript identifier
        format: Return format (content, metadata, or both)
    """
    try:
        if format == "content":
            content = transcript_mgr.get_transcript_content(transcript_id)
            if content is None:
                raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
            return PlainTextResponse(content=content, media_type="text/plain; charset=utf-8")

        elif format == "metadata":
            metadata = transcript_mgr.get_transcript_metadata(transcript_id)
            if metadata is None:
                raise HTTPException(status_code=404, detail=f"Transcript metadata {transcript_id} not found")
            return JSONResponse(content=metadata)

        else:  # format == "both"
            content = transcript_mgr.get_transcript_content(transcript_id)
            metadata = transcript_mgr.get_transcript_metadata(transcript_id)

            if content is None:
                raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")

            return {
                "transcript_id": transcript_id,
                "content": content,
                "metadata": metadata or {},
                "has_metadata": metadata is not None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")


