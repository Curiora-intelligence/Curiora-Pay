from fastapi import APIRouter, Request, Form, Depends,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services import bank_engine
import psycopg as sql,os

# 1. THE BOUNCER: Checks the VIP wristband (cookie) authorization
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        # Kicks them to login if they aren't authenticated
        raise HTTPException(status_code=303, headers={"Location": "/login-form"})
    return user_id

# 2. THE SUB-PANEL: Create the secure zone
dashboard_router = APIRouter(
    prefix="/dashboard",
    dependencies=[Depends(get_current_user)]
)
templates=Jinja2Templates(directory="templates")

#DASHBOARD ROUTE
@dashboard_router.get("/", response_class=HTMLResponse)
def dashboard(request: Request,user_id:str=Depends(get_current_user)):
    try:
        with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
            with con.cursor() as cursor:
                cursor.execute("SELECT username, balance, account_number FROM users WHERE userid = %s", (user_id,))
                user_data = cursor.fetchone()
                username, balance, account_number = user_data
                
                cursor.execute("SELECT * FROM transactions WHERE sender_acc= %s OR receiver_acc= %s ORDER BY date DESC LIMIT 5" ,(account_number,account_number))
                raw_transactions = cursor.fetchall()

                formatted_transactions = []
                for row in raw_transactions:
                    if row[3] == account_number:
                        tx_type = "Sent" 
                        counterparty = f"To: {row[5]}"
                        sign = "-"
                    else:
                        tx_type = "Received"
                        counterparty = f"From: {row[2]}"
                        sign = "+"
                    formatted_transactions.append({
                        "transactionid": row[1],
                        "type": tx_type,
                        "counterparty": counterparty,
                        "amount": f"{sign}₹{row[6]}",
                        "note": bank_engine.Bank.decrypt_str(row[9]),
                        "status": row[7],
                        "date": str(row[8])[:16],
                        "method": row[10]
                    })

                return templates.TemplateResponse(request,'homepage.html', {
                "user_name": username,
                "total_balance": balance,
                "account_number": account_number,
                "transactions": formatted_transactions
                })
    except Exception as a:
        return f"Error occured while loading dashboard {str(a)}"



# SECURED TRANSACTION ROUTES 

#Transfer money route
@dashboard_router.get("/transfer-money-form", response_class=HTMLResponse)
def transfer_money_form(request: Request):
    return templates.TemplateResponse(request,"transfer-money-form.html",)

@dashboard_router.post("/transfer-money", response_class=HTMLResponse)
def transfer_money(request: Request,user_id: str = Depends(get_current_user), receiver_acc: str = Form(...),amount: float = Form(...),note: str = Form(None), method: bank_engine.TransactionMethod = Form(...)):
    
    user_bank = bank_engine.Bank(user_id)
    success, message = user_bank.transfer(receiver_acc, amount, note, method)
    if not success:
        return templates.TemplateResponse(request,"transfer-money-form.html", {"error": message})
    return templates.TemplateResponse(request,"transfer-result.html", {"success": success, "message": message})

#Deposit money route
@dashboard_router.get("/deposit", response_class=HTMLResponse)
def deposit(request: Request):
    return templates.TemplateResponse(request,"deposite-money-form.html")

@dashboard_router.post("/deposite-money", response_class=HTMLResponse)
def deposite_money(request: Request, amount: float = Form(...),user_id: str = Depends(get_current_user)):
    user_bank = bank_engine.Bank(user_id)
    success, message = user_bank.deposit_amount(amount)
    if not success:
        return templates.TemplateResponse(request,"deposite-money-form.html", {"error": message})
    return templates.TemplateResponse(request,"deposite-result.html", {"success": success, "message": message})

#Withdraw money route
@dashboard_router.get("/withdraw-money-form", response_class=HTMLResponse)
def withdraw_money_form(request: Request):
    return templates.TemplateResponse(request,"withdraw-money-form.html")

@dashboard_router.post("/withdraw-money", response_class=HTMLResponse)
def withdraw_money(request: Request, user_id: str = Depends(get_current_user), amount: float = Form(...)):
    user_bank = bank_engine.Bank(user_id)
    success, message = user_bank.withdraw_amount(amount)
    if not success:
        return templates.TemplateResponse(request,"withdraw-money-form.html", {"error": message})
    return templates.TemplateResponse(request,"withdraw-result.html", {"success": success, "message": message})

#AI loan approval route
@dashboard_router.get("/apply-loan", response_class=HTMLResponse)
def apply_loan(request: Request,user_id:str=Depends(get_current_user)):
    user_bank = bank_engine.Bank(user_id)
    status,message,user_data=user_bank.apply_for_loan()
    return templates.TemplateResponse(request,"loan-form.html", {"status":status,"message":message,"user_data":user_data})

@dashboard_router.get("/download-satatement-form")
def statement(request:Request,date_filter:str=None,userid=Depends(get_current_user)):
    return bank_engine.Bank.download_statement(userid)

@dashboard_router.get("/transaction-history", response_class=HTMLResponse)
def transaction_history(request:Request):
    pass
