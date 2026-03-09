from pydantic_model import *
from dbConnection import collection_config, collection_user, collection_files, collection_QuBound_file, collection_QuCAD_file
from fastapi import FastAPI, HTTPException, Response
from fastapi import UploadFile, File, Form
from bson import ObjectId
import base64
from bson.binary import Binary
from datetime import datetime
import torch
import io
import json

app = FastAPI()

# creating the post end point to enable fastapi to save the endpoint

# @app.post("/students", status_code=201)
# async def create_student(student: Student):
#     result = collection.insert_one(student.model_dump())
#     return {"id": str(result.inserted_id)}


# @app.get("/students", response_model=list[Student])
# async def get_all_students():
#     # .find() with an empty dict {} fetches all records
#     # {"_id": 0} hides the MongoDB ID to match your Pydantic model
#     students = list(collection.find({}, {"_id": 0}))
#     return students


# @app.get("/students/{id}", response_model=Student)
# async def get_student(id: str):
#     student = collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
#     if student:
#         return student
#     else:
#         raise HTTPException(status_code=404, detail="Student not found")
    
@app.post("/CircuitConfig", status_code=201)
async def create_IBMConfig(config: IBMConfig):
    result = collection_config.insert_one(config.model_dump())
    return {
        "message": "Student created successfully", 
        "id": str(result.inserted_id)
    }


@app.get("/CircuitConfig", response_model=list[IBMConfig])
async def get_all_configs():
    # .find() with an empty dict {} fetches all records
    # {"_id": 0} hides the MongoDB ID to match your Pydantic model
    circuitConfigs = list(collection_config.find({}, {"_id": 0}))
    return circuitConfigs

@app.post("/login")
async def login(data: LoginRequest):
    user = collection_user.find_one({"username": data.username, "password": data.password})
    if user:
        return {"status": "success", "username": data.username}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
@app.post("/signup")
async def signup(data: LoginRequest):
    user = collection_user.find_one({"username": data.username})

    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    result = collection_user.insert_one(data.model_dump())
    return {
        "status": "success",
        "message": "Login Information added successfully", 
        "id": str(result.inserted_id),
        "username": data.username
    }




@app.get("/load_QuCAD")
async def load_QuCAD_Qbank(model_name: str):

    doc = collection_QuCAD_file.find_one({"model_name": model_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    
    qucad_bank_data = json.loads(doc["qucad_bank"])
    
    return qucad_bank_data

@app.post("/save_QuCAD")
async def save_QuBound_data(
    username: str = Form(...),
    model_name: str = Form(...),
    qucad_bank: str = Form(...)
    ):
    try:
        model_document = {
            "username": username,
            "model_name": model_name,
            "qucad_bank": qucad_bank,
        }

        # 4. Insert into your results_files or a new 'models' collection
        result = collection_QuCAD_file.insert_one(model_document)

        return {
            "status": "success",
            "message": f"QuCAD model saved to MongoDB",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.get("/load_QUbound")
async def load_QuBound_data(model_name:str):
    doc = collection_QuBound_file.find_one({"model_name": model_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_bytes = doc["model_data"]
    
    # Load into Torch
    buffer = io.BytesIO(model_bytes)
    model = torch.jit.load(buffer)
    
    return Response(
        content=model_bytes, 
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={model_name}.pt"}
    )

@app.post("/save_QUbound")
async def save_QuBound_data(
    username: str = Form(...),
    model_name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # 1. Read the binary content from the upload
        model_bytes = await file.read()

        # 2. (Optional but recommended) Verify it's a valid JIT model
        # This ensures you don't save corrupted data to your DB
        try:
            buffer = io.BytesIO(model_bytes)
            torch.jit.load(buffer)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid TorchScript model: {str(e)}")

        # 3. Prepare the document for MongoDB
        # We use Binary() to tell MongoDB to store this as raw bytes
        model_document = {
            "username": username,
            "model_name": model_name,
            "model_data": Binary(model_bytes),
            "uploaded_at": datetime.utcnow()
        }

        # 4. Insert into your results_files or a new 'models' collection
        result = collection_QuBound_file.insert_one(model_document)

        return {
            "status": "success",
            "message": f"JIT model '{model_name}' saved to MongoDB",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/expdata_save")
async def save_experiment_data(exp_data: expDataRequest):
    # result = collection_files.insert_one(exp_data.model_dump())

    data = exp_data.model_dump()
    data['experiment_data'] = Binary(base64.b64decode(data['experiment_data']))
    data['experiment_circuit'] = Binary(base64.b64decode(data['experiment_circuit']))

    result = collection_files.insert_one(data)

    return {
        "message": "Experiment data saved successfully", 
        "id": str(result.inserted_id)
    }

@app.get("/expdata_retrieve", response_model = list[expDataRequest])
async def get_all_exp_data_list(username: str):
    # exp_data_list = list(collection_files.find({}, {"_id": 0}))
    # return exp_data_list
    raw_data_list = list(collection_files.find({"username": username}, {"_id": 0}))
    
    formatted_list = []
    
    for data in raw_data_list:
        # 2. Convert bytes/Binary back to Base64 strings
        if isinstance(data.get('experiment_data'), bytes):
            data['experiment_data'] = base64.b64encode(data['experiment_data']).decode('utf-8')
            
        if isinstance(data.get('experiment_circuit'), bytes):
            data['experiment_circuit'] = base64.b64encode(data['experiment_circuit']).decode('utf-8')
            
        formatted_list.append(data)
        
    return formatted_list


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "127.0.0.1",port = 8000)