from app.models.tables import Expenses, sesssionLocal
from flask import g
from sqlalchemy import func,and_

def get_db():
       if "db" not in g:
          g.db=sesssionLocal()
       return g.db

class Expense_tracker:
    def __init__(self) -> None:
        pass
    def add_expense(self,title,amount,category,date,user_id):
        try:
         db=get_db()
         new_expense = Expenses(title=title,amount=amount,category=category,date=date,user_id=user_id)
         db.add(new_expense)
         db.commit()
         return {"message" : "Expense Successfully added"}, 201
        except Exception as e:
            db.rollback()
            return {"message" : f"Error : {str(e)}"},500

    def view_expense(self,page,page_size,user_id):
       try:
        db=get_db()
        skip=(page-1)*page_size
        data= db.query(Expenses).filter(Expenses.user_id==user_id).offset(skip).limit(page_size).all()
        return [i.to_dict() for i in data],200
       except Exception as e:
            return {"message" : f"Error : {str(e)}"},500

    
    def view_total(self,user_id):
        try:
         db=get_db()
         s=db.query(func.sum(Expenses.amount)).filter(Expenses.user_id==user_id).scalar()
         db.commit()
         return {"total" : s or 0},200
        except Exception as e:
            return {"message" : f"Error : {str(e)}"},500

        
    def search_by_cat(self, category,user_id):
     try :
      db=get_db()
      data= db.query(Expenses).filter(Expenses.user_id==user_id).filter(Expenses.category==category).all()
      return [i.to_dict() for i in data], 200
     except Exception as e:
            db.rollback()
            return {"message" : f"Error : {str(e)}"},500
      
     
    def delete_titl(self,title,user_id):
        try:
         db=get_db()
         dell=db.query(Expenses).filter(Expenses.user_id==user_id).filter(Expenses.title==title).first()
         if dell:
          db.delete(dell)
          db.commit()
          return {"message" : "Deleted Successfully"},201
         else :
             return {"message" : "No such title to delete"},404
        except Exception as e:
            db.rollback()
            return {"message" : f"Error : {str(e)}"},500
        
    def filter_Expenses_bydate(self,start_date,end_date,user_id):
     try :
        db=get_db()
        data=db.query(Expenses).filter(Expenses.user_id==user_id).filter(and_(Expenses.date>=start_date,
       Expenses.date<=end_date)).all()
        return [i.to_dict() for i in data],200
     except Exception as e:
        return {"message" : f"Error{str(e)}"},500

