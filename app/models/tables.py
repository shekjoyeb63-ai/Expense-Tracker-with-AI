from sqlalchemy import Integer,String,Column,create_engine,Float,ForeignKey
from sqlalchemy.orm import DeclarativeBase,sessionmaker,relationship
import os

DATABASE=os.getenv("DATABASE_URL" , "sqlite:///Expense.db")

engine=create_engine(DATABASE,echo=False)

sesssionLocal=sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="userdetails"
    id=Column(Integer,primary_key=True)
    email=Column(String(100),unique=True,nullable=False)
    password=Column(String(100))
    is_verified=Column(Integer,default=0)
    phone_number=Column(String(15),nullable=True)
    exp=relationship("Expenses",back_populates="us")
    def to_dict(self):
        return{
            "id" : self.id,
            "email" : self.email,
            "is_verified" : self.is_verified
        }

class Expenses(Base):
    __tablename__="Expenses_Table"
    id=Column(Integer,primary_key=True)
    title=Column(String)
    amount=Column(Float)
    category=Column(String)
    date=Column(String)
    user_id=Column(Integer,ForeignKey("userdetails.id"),nullable=True)
    us=relationship("User",back_populates="exp")
    def to_dict(self):
        return {
            "id" : self.id,
            "title" : self.title,
            "amount" : self.amount,
            "category" : self.category,
            "date" : self.date
        }
Base.metadata.create_all(engine)    