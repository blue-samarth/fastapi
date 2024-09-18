from fastapi import FastAPI, HTTPException, UploadFile, File, Form , Response
from typing import List
from uuid import uuid4, UUID
from gridfs import GridFS
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import uvicorn
from pymongo import MongoClient
from bson import ObjectId , Binary

# Synchronous MongoDB client for GridFS
try:
    sync_client = MongoClient("mongodb://mongo:27017")
    pymongo_db = sync_client["client_list"]  # Replace with your preferred DB name
    fs = GridFS(pymongo_db)
    print("Connected to MongoDB and GridFS")
except Exception as e:
    print("Failed to connect to MongoDB/GridFS:", e)

# Asynchronous MongoDB client
client = AsyncIOMotorClient("mongodb://mongo:27017", uuidRepresentation="standard")
db: AsyncIOMotorDatabase = client["client_list"]  # Same DB name as above, will be created automatically

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class JOB(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    # id: str = Field(default_factory=str, alias="_id")
    name: str
    phone: int
    rdate: str
    inventory: int
    document: Optional[str] 
    issue: str
    notes: str
    technician: str
    deadline: str
    amount: int
    status: str

@app.post("/createjob", response_model=JOB)
async def create_job(
    name: str = Form(...),
    phone: int = Form(...),
    rdate: str = Form(...),
    inventory: int = Form(...),
    issue: str = Form(...),
    notes: str = Form(...),
    technician: str = Form(...),
    deadline: str = Form(...),
    amount: int = Form(...),
    status: str = Form(...),
    document: Optional[UploadFile] = File(None)
):
    try:
        job_data = {
            "name": name,
            "phone": phone,
            "rdate": rdate,
            "inventory": inventory,
            "issue": issue,
            "notes": notes,
            "technician": technician,
            "deadline": deadline,
            "amount": amount,
            "status": status,
        }

        if document:
            file_data = await document.read()
            grid_out = fs.put(file_data, filename=document.filename, content_type=document.content_type)
            job_data["document"] = str(grid_out)  # Save the file ID from GridFS

        job_id = uuid4()
        job_data["_id"] = job_id

        # Insert into MongoDB
        await db["jobs"].insert_one(job_data)

        return {**job_data, "id": job_id}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to create job")




@app.get("/jobs", response_model=List[JOB])
async def get_jobs():
    try:
        jobs = await db["jobs"].find().to_list(length=100)
        return jobs
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to fetch jobs")



@app.get("/jobs/{job_id}", response_model=JOB)
async def get_job(job_id: UUID):
    try:
        job = await db["jobs"].find_one({"_id": job_id})
        if job:
            return job
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to fetch job")


@app.get("/files/{file_id}")
async def get_file(file_id: str):
    try:
        file_id = ObjectId(file_id)
        grid_out = fs.get(file_id)
        content_type = grid_out.content_type
        return Response(content=grid_out.read(), media_type=content_type)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="File not found")
    
@app.put("/job_Edit/{job_id}", response_model=JOB)
async def update_job(
    job_id: UUID,  # This is a UUID object
    name: str = Form(...),
    phone: int = Form(...),
    rdate: str = Form(...),
    inventory: int = Form(...),
    issue: str = Form(...),
    notes: str = Form(...),
    technician: str = Form(...),
    deadline: str = Form(...),
    amount: int = Form(...),
    status: str = Form(...),
    document: Optional[UploadFile] = File(None)
):
    try:
        job_data = {
            "name": name,
            "phone": phone,
            "rdate": rdate,
            "inventory": inventory,
            "issue": issue,
            "notes": notes,
            "technician": technician,
            "deadline": deadline,
            "amount": amount,
            "status": status,
        }

        if document:
            file_data = await document.read()  
            grid_out = fs.put(file_data, filename=document.filename, content_type=document.content_type)  # Store file in GridFS
            job_data["document"] = str(grid_out)  

        # Perform the update operation using the UUID
        update_result = await db["jobs"].update_one(
            {"_id": Binary.from_uuid(job_id)},  # Use Binary.from_uuid to convert UUID to Binary type for MongoDB
            {"$set": job_data}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Job not found or not updated")

        updated_job = await db["jobs"].find_one({"_id": Binary.from_uuid(job_id)})  

        # Convert to Pydantic model for the response
        return JOB(**updated_job)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"Failed to update job: {str(e)}") 

@app.delete("/delete_job/{job_id}")
async def delete_job(job_id: UUID):
    try:
        delete_result = await db["jobs"].delete_one({"_id": job_id})
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job not found or not deleted")
        return {"message": "Job deleted"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to delete job")   
    
# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
