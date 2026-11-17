from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, Session
# pydantic은 리액트에서 데이터를 요청을 받을때 웹브라우저에서 적어서 클릭을 하게 되면 그 데이터가 우리한테 오겠죠 그 
# 데이터 타입이 맞는지 검사하는 라이브러리
from pydantic import BaseModel
from supabase import create_client, ClientOptions

DATABASE_URL = "postgresql://postgres.sjcqhzgjpoplxtqoqeyv:kWJUbef9Q0p74Aox@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# 객체로 만든거
engine = create_engine(DATABASE_URL)

# 객체로 만든거
Base = declarative_base()

SUPABASE_URL = "https://sjcqhzgjpoplxtqoqeyv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNqY3FoemdqcG9wbHh0cW9xZXl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ3NzM3OTcsImV4cCI6MjExMDM0OTc5N30.96gDfKJCWtbUFmOf0y2VDbLbr5nYsP2HYinlJGt_Xes"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(flow_type="pkce"))

# 테이블 모델(테이블 이름을 users)
class Profile(Base):
    # users가 테이블 이름이다 
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(120))
    provider = Column(String(50))

# 회원가입할때 받을것
class EmailForm(BaseModel):
    username: str
    email: str
    password: str

# 테이블이 없으면 생성
Base.metadata.create_all(bind=engine)

# 요청마다 세션을 열고, 끝나면 닫는 함수 finally는 성공해도 닫고 실패해도 닫는다?
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/")
def read_home():
    return {
        "hello": "world"
    }

def save_profile(db: Session, user, username, provider):
    # get은 하나만 가져온다 
    profile = db.get(Profile, user.id)
    if profile is None:
        Profile(id=user.id, email=user.email, username=username, provider=provider)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

# 회원가입을 고객한테 받아서 date로 옮겨야 하니까 post
@app.post("/signup")
def signup(form: EmailForm, db: Session=Depends(get_db)):
    # auth 안에 sign_up이라는 메서드가 있다 이걸 이용하면 내가 너한테 어떠한 값을 주겠다 
    res = supabase.auth.sign_up({
        "email": form.email,
        "password": form.password
    })
    # user는 res에 이메일이랑 패스워드다 
    profile = save_profile(db, res.user, form.username, "email")
    return {
        "id": profile.id,
        "email": profile.email,
        "username": profile.username
    }