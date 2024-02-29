from fastapi import (
    FastAPI,
    Request,
    Form,
    Depends,
    HTTPException,
    status,
    Cookie,
)
from fastapi.routing import APIRouter
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from chat1 import collect_messages_text1,payment
from chat2 import get_completion_from_messages2,collect_messages_text2
from chat3 import get_completion_from_messages3,collect_messages_text3
from chat4 import get_completion_from_messages4,collect_messages_text4
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from fastapi.responses import JSONResponse,HTMLResponse
import random
import os,uuid
import json
import logging
from google.cloud import bigquery



# Set your Google Cloud project ID
project_id = 'ck-eams'

# Initialize a BigQuery client
client = bigquery.Client(project=project_id)




# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (use logging.DEBUG for more detailed logs)
    filename="app.log",  # Specify a file to write logs (optional)
    format="%(asctime)s [%(levelname)s]: %(message)s",  # Define log format
)

# Initialize FastAPI app
app = FastAPI()
router = APIRouter()

# Create an instance of HTTPBasic for security
security = HTTPBasic()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2Templates
templates = Jinja2Templates(directory="templates")

# User Database (for demonstration purposes)
users = {}

# In-memory session storage (for demonstration purposes)
sessions = {}


class SessionData(BaseModel):
    username: str


class Message(BaseModel):
    content: str


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users.get(credentials.username)
    if user is None or users["password"] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def create_session(username: str):
    session_id = str(uuid.uuid4())
    # print(session_id)
    sessions[session_id] = username
    # print(sessions[session_id])
    return session_id

def get_user_from_session(session_id: str):
    username = sessions.get(session_id)
    if username:
        user = users.get(username)
        # print(f"Session ID passed in: {session_id}")
        # print(f"User retrieved from session: {user}")
        return user
    return None


def get_authenticated_user_from_session_id(
    session_id: str = Cookie(None, alias="session_id")
):
    if session_id is None or str(session_id) not in sessions:
        raise HTTPException(
            status_code=401,
            detail="Invalid session ID",
        )
    user = get_user_from_session(session_id)
    return user

def authenticated_user_required():
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # print("Wrapper function is being called")
            session_id = request.cookies.get("session_id")
            # print(f"Session ID from cookies: {session_id}")
            user = get_user_from_session(session_id)
            print(f"User retrieved from session: {user}")
            if user:
                return await func(request, user, *args, **kwargs)
            else:
                return RedirectResponse(url="/login")
        return wrapper
    return decorator

@app.post("/signup", response_class=RedirectResponse)
async def signup(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    
    sql_query = """
        SELECT * from ck-eams.dosabot.users
        where username=@username
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
        ]
    )

    # Run the query job
    query_job = client.query(sql_query, job_config=job_config)

    # Wait for the job to complete (optional)
    print(query_job.result())
    results=query_job.result()
    uname=""
    for row in results:
        print(row)
        print(row[0])
        print(row[1])
        uname=row[0]

    print("Username:",username)
    print("password:",password)
    if uname==username :
        print("You have already signed in !!!")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


        # Define your SQL query
    sql_query = """
        INSERT INTO ck-eams.dosabot.users (username, password)
        VALUES (@username,@password)
    """

    # Set up the query job and pass parameters
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
            bigquery.ScalarQueryParameter("password", "STRING", password)
        ]
    )

    # Run the query job
    query_job = client.query(sql_query, job_config=job_config)

    # Wait for the job to complete (optional)
    query_job.result()

    # Optionally check for errors or retrieve job results
    if query_job.errors:
        for error in query_job.errors:
            print(f"Error: {error}")

    # Print the number of rows affected
    print(f"Inserted {query_job.num_dml_affected_rows} row(s) into BigQuery.")


    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)



@app.get("/login", response_class=HTMLResponse)

def login(request: Request, error: str = None):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )

@app.post("/login", response_class=RedirectResponse)
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    
    sql_query = """
      SELECT * FROM ck-eams.dosabot.users
       WHERE Username=@username
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
           
        ]
    )

    # Run the query job
    query_job = client.query(sql_query, job_config=job_config)

    # Wait for the job to complete (optional)
    query_job.result()
    for row in query_job.result():
        print(row)

    if row[1] == password:  
        session_id = create_session(username)
        logging.info(f"Session created for user {username} with session ID {session_id}")

        response = RedirectResponse(
            url="/templates/index1.html",
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Set-Cookie": f"session_id={session_id}"},
        )
    else:
        response = RedirectResponse(
            url="/login?error=Invalid%20credentials",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return response



@app.get("/getusers/me", response_class=HTMLResponse)
def read_current_user(
    request: Request, user: dict = Depends(get_authenticated_user_from_session_id)
):
    return HTMLResponse(content="You are logged in as: " + user["username"])

@app.post("/logout", response_class=RedirectResponse)
def logout(session_id: str = Cookie(None, alias="session_id")):
    if session_id is not None and session_id in sessions:
        sessions.pop(session_id)
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER,
        headers={"Set-Cookie": "session_id=; expires=Thu, 01 Jan 1970 00:00:00 GMT"},
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request, error: str = None):
    return templates.TemplateResponse(
        "signup.html", {"request": request, "error": error}
    )


@app.post("/chat1", response_model=dict)
async def chat1(
    request: Request, 
    message: Message,
    user: dict = Depends(get_authenticated_user_from_session_id)
):
    user_message = message.content
    
    # Debugging: Print the received message and headers
    # print(f"Received message in chat1: {user_message}")
    # print(f"Headers: {dict(request.headers)}")
    
    if not user_message:
        return {"message": "Received an empty message."}

    try:
        session_id = request.cookies.get("session_id")
        response = collect_messages_text1(user_message, session_id)  # Pass session_id as a parameter
        print(session_id)
        return {"message": response}
    except Exception as e:
        print(f"Error in chat1: {e}")
        return {"message": "An error occurred."}


@app.post("/chat2", response_model=dict)
async def chat2(message: Message):
    user_message = message.content
    response = collect_messages_text2(user_message)
    return {"message": response}


@app.post("/chat3", response_model=dict)
async def chat3(message: Message):
    user_message = message.content
    response = collect_messages_text3(user_message)
    return {"message": response}


@app.post("/chat4", response_model=dict)
async def chat4(message: Message):
    user_message = message.content
    response = collect_messages_text4(user_message)
    return {"message": response}


@app.post("/process_voice", response_model=dict)
async def process_voice(request: Request,voice_input: dict):
    text = voice_input.get("input")
    session_id = request.cookies.get("session_id")
    response = collect_messages_text1(text,session_id)
    return {"message": response}
@app.post("/process_voice", response_model=dict)
async def process_voice(voice_input: dict):
    text = voice_input.get("input")
    response = collect_messages_text2(text)
    return {"message": response}
@app.post("/process_voice", response_model=dict)
async def process_voice(voice_input: dict):
    text = voice_input.get("input")
    response = collect_messages_text3(text)
    return {"message": response}
@app.post("/process_voice", response_model=dict)
async def process_voice(voice_input: dict):
    text = voice_input.get("input")
    response = collect_messages_text4(text)
    return {"message": response}

# @app.get("/index.html"
# def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


@app.get("/templates/index1.html")
def index1(request: Request):
    return templates.TemplateResponse("index1.html", {"request": request})


@app.get("/templates/index2.html")
def index2(request: Request):
    return templates.TemplateResponse("index2.html", {"request": request})


@app.get("/templates/hotel1.html")
def hotel1(request: Request):
    return templates.TemplateResponse("hotel1.html", {"request": request})

@app.get("/templates/hotel2.html")
def hotel2(request: Request):
    return templates.TemplateResponse("hotel2.html", {"request": request})

@app.get("/templates/hotel3.html")
def hotel3(request: Request):
    return templates.TemplateResponse("hotel3.html", {"request": request})

@app.get("/templates/hotel4.html")
def hotel4(request: Request):
    return templates.TemplateResponse("hotel4.html", {"request": request})



@app.get("/get_order_summary", response_model=list[dict])
def get_order_summary_from_db(session_id: str):
    id=session_id
    try:
        sql_query="""
            SELECT item_name, quantity, price 
            FROM ck-eams.dosabot.order_items 
            WHERE id = @id
        """
        job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING",id),
           
        ])

        # Run the query job
        query_job = client.query(sql_query, job_config=job_config)

        # Wait for the job to complete (optional)
        order_summary=query_job.result()
        # total_price = calculate_total_price(session_id)

        # Convert the data into a list of dictionaries
        order_summary_list = [{'item_name': row[0], 'quantity': row[1], 'price': row[2]} for row in order_summary]
        print(order_summary_list)
        insert_order(session_id)
        return order_summary_list
    except Exception as e:
        print(f"Error: {e}")
        return [{"error": "Order summary not found"}]


# # Function to create the "orders" table and insert session_id and totalprice

def insert_order(session_id):

        total_price=calculate_total_price(session_id)
        id=session_id
        # Execute the SQL statement to insert data
        sql_query="""
            INSERT INTO ck-eams.dosabot.orders (id, total_price)
            VALUES (@id, @total_price)
            """
        job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING",id),
            bigquery.ScalarQueryParameter("total_price", "STRING",total_price),
           
        ])

        # Run the query job
        query_job = client.query(sql_query, job_config=job_config)

        # Wait for the job to complete (optional)
        query_job.result()
        print("Inserted into orders successfully")
        
        payment(session_id)
        
        
        

def calculate_total_price(session_id):
    id=session_id
    sql_query="""SELECT SUM(CAST(quantity AS INT64) * CAST(price AS INT64))
                  FROM ck-eams.dosabot.order_items
                  WHERE id = @id"""


    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING",id),
           
        ])

    # Run the query job
    query_job = client.query(sql_query, job_config=job_config)

    # Wait for the job to complete (optional)
    results=query_job.result()
    total_price =[ row[0] for row in results]
    print(total_price)
    print(total_price[0])
    return total_price[0]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)