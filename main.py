import os
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection string
DATABASE_URL = "postgresql://postgres:Qwerty%3A29%2103@localhost/ai_assistant_db"

engine = create_engine(DATABASE_URL)


# -------------------------------
# Home Route
# -------------------------------
@app.get("/")
def home():
    return {"message": "AI SQL Backend Running 🚀"}


# -------------------------------
# Get All Users
# -------------------------------
@app.get("/users")
def get_users():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users ORDER BY id"))
            users = [dict(row._mapping) for row in result]
        return users
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Pydantic Model
# -------------------------------
class User(BaseModel):
    name: str
    age: int


class QuestionRequest(BaseModel):
    question: str


# -------------------------------
# Add User
# -------------------------------
@app.post("/add_user")
def add_user(user: User):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (name, age) VALUES (:name, :age)"),
                {"name": user.name, "age": user.age}
            )
            conn.commit()
        return {"message": "User added successfully ✅"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Update User
# -------------------------------
@app.put("/update_user/{user_id}")
def update_user(user_id: int, user: User):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    UPDATE users 
                    SET name = :name, age = :age 
                    WHERE id = :id 
                    RETURNING id
                """),
                {"name": user.name, "age": user.age, "id": user_id}
            )
            updated = result.fetchone()
            conn.commit()

        if updated:
            return {"message": "User updated successfully ✅"}
        else:
            raise HTTPException(status_code=404, detail="User not found ❌")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Delete User
# -------------------------------
@app.delete("/delete_user/{user_id}")
def delete_user(user_id: int):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM users WHERE id = :id RETURNING id"),
                {"id": user_id}
            )
            deleted = result.fetchone()
            conn.commit()

        if deleted:
            return {"message": "User deleted successfully 🗑️"}
        else:
            raise HTTPException(status_code=404, detail="User not found ❌")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# AI Question Endpoint
# -------------------------------
@app.post("/ask")
def ask_ai(request: QuestionRequest):
    try:
        user_question = request.question

        prompt = f"""
        You are a PostgreSQL expert.
        Convert the user question into SQL query.
        Only return SQL.
        Table name: users
        Columns: id, name, age

        Question: {user_question}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        sql_query = response.choices[0].message.content.strip()

        if not sql_query.lower().startswith("select"):
            return {"error": "Only SELECT queries allowed"}

        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]

        return {
            "generated_sql": sql_query,
            "result": rows
        }

    except Exception as e:
        return {"error": str(e)}