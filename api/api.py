import asyncio
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.workflow import workflow
from src.schemas import BriefRequest, BriefResponse, FinalBrief
from src.config import config

# Initialize FastAPI app
app = FastAPI(
    title="Research Brief Generator API",
    description="AI-powered research brief generation using LangGraph and Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for async job tracking
job_store: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Research Brief Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_brief": "POST /brief",
            "get_job_status": "GET /job/{job_id}",
            "health_check": "GET /health"
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Validate configuration
        is_configured = config.validate_config()
        
        return {
            "status": "healthy" if is_configured else "configuration_error",
            "timestamp": time.time(),
            "configuration": {
                "gemini_api_configured": bool(config.GEMINI_API_KEY or config.GOOGLE_API_KEY),
                "model": config.GEMINI_MODEL
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@app.post("/brief", response_model=BriefResponse)
async def generate_brief(request: BriefRequest, background_tasks: BackgroundTasks):
    """
    Generate a research brief.
    
    This endpoint accepts a research request and returns the generated brief.
    For long-running requests, consider using the async job endpoints.
    """
    try:
        # Validate request
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        if not (1 <= request.depth <= 5):
            raise HTTPException(status_code=400, detail="Depth must be between 1 and 5")
        
        # Generate thread ID for checkpointing
        thread_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        # Execute workflow
        result = workflow.run(
            topic=request.topic,
            depth=request.depth,
            follow_up=request.follow_up,
            user_id=request.user_id,
            thread_id=thread_id
        )
        
        processing_time = time.time() - start_time
        
        # Check if workflow completed successfully
        if not result.get("success", False):
            error_message = result.get("error", "Unknown workflow error")
            return BriefResponse(
                success=False,
                brief=None,
                error_message=error_message,
                processing_time=processing_time
            )
        
        # Extract the final brief
        final_brief = result.get("final_brief")
        if not final_brief:
            return BriefResponse(
                success=False,
                brief=None, 
                error_message="No brief generated",
                processing_time=processing_time
            )
        
        return BriefResponse(
            success=True,
            brief=final_brief,
            error_message=None,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time if 'start_time' in locals() else 0
        return BriefResponse(
            success=False,
            brief=None,
            error_message=f"Internal server error: {str(e)}",
            processing_time=processing_time
        )

@app.post("/brief/async")
async def generate_brief_async(request: BriefRequest):
    """
    Start an asynchronous brief generation job.
    
    Returns a job ID that can be used to check status and retrieve results.
    """
    try:
        # Validate request
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        
        # Store job info
        job_store[job_id] = {
            "status": "pending",
            "created_at": time.time(),
            "request": request.dict(),
            "thread_id": thread_id,
            "result": None,
            "error": None
        }
        
        # Start background task
        asyncio.create_task(process_brief_job(job_id, request, thread_id))
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Brief generation started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and result of an async brief generation job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = job_store[job_id]
    
    response = {
        "job_id": job_id,
        "status": job_info["status"],
        "created_at": job_info["created_at"]
    }
    
    if job_info["status"] == "completed":
        response["result"] = job_info["result"]
    elif job_info["status"] == "failed":
        response["error"] = job_info["error"]
    elif job_info["status"] == "processing":
        response["message"] = "Brief generation in progress"
    
    return response

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job from the job store."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del job_store[job_id]
    return {"message": "Job deleted successfully"}

@app.get("/jobs")
async def list_jobs(user_id: Optional[str] = None):
    """List all jobs, optionally filtered by user_id."""
    jobs = []
    for job_id, job_info in job_store.items():
        if user_id and job_info["request"]["user_id"] != user_id:
            continue
            
        jobs.append({
            "job_id": job_id,
            "status": job_info["status"],
            "topic": job_info["request"]["topic"],
            "user_id": job_info["request"]["user_id"],
            "created_at": job_info["created_at"]
        })
    
    return {"jobs": jobs}

async def process_brief_job(job_id: str, request: BriefRequest, thread_id: str):
    """Background task to process a brief generation job."""
    try:
        # Update status
        job_store[job_id]["status"] = "processing"
        job_store[job_id]["started_at"] = time.time()
        
        # Execute workflow
        result = workflow.run(
            topic=request.topic,
            depth=request.depth,
            follow_up=request.follow_up,
            user_id=request.user_id,
            thread_id=thread_id
        )
        
        # Update job with result
        if result.get("success", False):
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["result"] = {
                "success": True,
                "brief": result.get("final_brief"),
                "processing_time": result.get("total_execution_time", 0)
            }
        else:
            job_store[job_id]["status"] = "failed" 
            job_store[job_id]["error"] = result.get("error", "Unknown error")
        
        job_store[job_id]["completed_at"] = time.time()
        
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
        job_store[job_id]["completed_at"] = time.time()

@app.get("/stats")
async def get_stats():
    """Get API usage statistics."""
    total_jobs = len(job_store)
    completed = sum(1 for job in job_store.values() if job["status"] == "completed")
    failed = sum(1 for job in job_store.values() if job["status"] == "failed")
    pending = sum(1 for job in job_store.values() if job["status"] in ["pending", "processing"])
    
    return {
        "total_jobs": total_jobs,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "success_rate": completed / total_jobs if total_jobs > 0 else 0
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=config.FASTAPI_HOST,
        port=config.FASTAPI_PORT,
        reload=True
    )