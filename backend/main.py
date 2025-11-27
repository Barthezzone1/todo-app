from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import SQLModel, Field, Session, create_engine, select

from uuid import uuid4
import pandas as pd


DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    api_key: str = Field(index=True, unique=True)


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = Field(default=False)
    user_id: int = Field(index=True)


class RegisterRequest(SQLModel):
    username: str


class UserPublic(SQLModel):
    username: str
    api_key: str


class TodoCreate(SQLModel):
    title: str


class TodoUpdate(SQLModel):
    title: Optional[str] = None
    done: Optional[bool] = None


app = FastAPI()

# pozwolenie frontendowi łączyć się z API (http://localhost:5173)
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# autentykacja z api key


def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> User:
    # brak nagłówka -> 401
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    user = session.exec(
        select(User).where(User.api_key == x_api_key)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return user

#endpointy
#request post - create, rejestracja nowego użytkownika - zwraca username oraz wygenerowane api key

@app.post("/register", response_model=UserPublic)
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):

    # sprawdzamy, czy username jest wolny
    existing = session.exec(
        select(User).where(User.username == payload.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already taken",
        )

    api_key = uuid4().hex  # prosty losowy klucz
    user = User(username=payload.username, api_key=api_key)
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserPublic(username=user.username, api_key=user.api_key)


@app.get("/todos", response_model=List[Todo])
def list_todos(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Zwraca listę zadań zalogowanego użytkownika.
    """
    todos = session.exec(
        select(Todo).where(Todo.user_id == current_user.id)
    ).all()
    return todos

#request post inaczej mówiąc create

@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(
    payload: TodoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):

    todo = Todo(
        title=payload.title,
        user_id=current_user.id,
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

#request put aka update

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):

    todo = session.get(Todo, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(404, "Todo not found")

    if payload.title is not None:
        todo.title = payload.title
    if payload.done is not None:
        todo.done = payload.done

    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

#request delete

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):

    todo = session.get(Todo, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(404, "Todo not found")

    session.delete(todo)
    session.commit()
    return

#pandas endpoint z statystykami

@app.get("/stats")
def stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):

    todos = session.exec(
        select(Todo).where(Todo.user_id == current_user.id)
    ).all()

    if not todos:
        return {"total": 0, "done": 0, "not_done": 0}

    df = pd.DataFrame(
        [{"id": t.id, "done": t.done} for t in todos]
    )

    total = len(df)
    done = int(df["done"].sum())
    not_done = total - done

    return {"total": total, "done": done, "not_done": not_done}
