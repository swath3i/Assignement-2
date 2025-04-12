from fastapi import FastAPI, Request , Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel,Field
from google.cloud import firestore
from uuid import uuid4
from typing import List, Optional
from fastapi import HTTPException , status ,APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.transport import requests
import google.oauth2.id_token




app = FastAPI()

# Serve static files like CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set template directory
templates = Jinja2Templates(directory="htmlpages")

firebase_db = firestore.Client()
firebase_request_adapter = requests.Request()

class nameRequest(BaseModel):
    name: str

class Task(BaseModel):
    task_mame: str
    task_users: List[str] 
    task_status: str  
    task_pendingDate: str
    task_finishedDate:str

class Taskboard(BaseModel):
    taskboardboard_Id:str
    taskboard_name:str
    taskboard_admin:str
    taskboard_tasks:Optional[List[Task]] = []
    taskboard_collaborators:List[str]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("main-page.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def fetch_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/boards", response_class=HTMLResponse)
async def fetch_login(request: Request):
    return templates.TemplateResponse("board.html", {"request": request})


@app.get("/displaytaskboard", response_class=HTMLResponse)
async def fetch_login(request: Request):
    return templates.TemplateResponse("displaytaskboard.html", {"request": request})

@app.get("/test", response_class=HTMLResponse)
async def fetch_login(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/test2", response_class=HTMLResponse)
async def fetch_login(request: Request):
    return templates.TemplateResponse("test2.html", {"request": request})


@app.post('/CheckTaskBoardName')
def checkTaskboardName(request:Request,name:nameRequest):
    print("inside request ",name)
    do_name_exist = firebase_db.collection('taskboards').where('name', '==', name.name).limit(1).get()
    if do_name_exist:
        return True
    return False


def get_user(request:Request):
        token = request.cookies.get("token")
        if not token:
            return None
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(token, firebase_request_adapter)
            if not user_token:
                return None

            email = user_token.get("email")
            if not email:
                return None
            user = {
                "email": email,
                "name": email.split("@")[0]
            }
            return user
        except Exception:
           return None
        
@app.post("/createboard", response_class=HTMLResponse)
def taskboard_creation(request: Request, taskboard: Taskboard):
    try:
        print("Creating taskboard:", taskboard)
        
      
        taskboard_data = taskboard.dict()

        firebase_db.collection('taskboards').add(taskboard_data)
        print("done")
        return True
    except Exception as e:
        print("Error while creating taskboard:", e)
        return HTMLResponse(content="Failed to create taskboard", status_code=500)
    

@app.get("/gettaskboards/{useremail}")
async def get_taskboards(useremail):
    print("email of user ",useremail)
    user_tasks = []
    taskboards_ref = firebase_db.collection("taskboards")
    taskboards = taskboards_ref.stream()
    print("user email is ",useremail, taskboards)
    for taskboard in taskboards:
        taskboard_data = taskboard.to_dict()
        if useremail == taskboard_data.get("taskboard_admin") or useremail in taskboard_data.get("taskboard_collaborators", []):
            user_tasks.append(taskboard_data)
    print("user tasks ",user_tasks)
    return {"user_tasks":user_tasks}


@app.get("/createuser")
def register_user_in_firestore(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None

    try:
        decoded_token = google.oauth2.id_token.verify_firebase_token(token, firebase_request_adapter)
        if not decoded_token:
            return None

        user_email = decoded_token.get("email")
        if not user_email:
            return None
       
        users_collection = firebase_db.collection("users")
        
        matching_users = users_collection.where("email", "==", user_email).limit(1).stream()
        if not any(matching_users):
            users_collection.add({
                "email": user_email,
            })

        return {"email": user_email}
    
    except Exception:
        return None