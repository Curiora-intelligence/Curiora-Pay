from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from services.bank_engine import Openaccount
import psycopg as sql,os,string,secrets

def cap(): #this function is for captcha generation
    return "".join(secrets.SystemRandom().choices(string.digits + string.ascii_letters,k=6))

auth_router= APIRouter()
templates=Jinja2Templates(directory="templates")

@auth_router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request,"home.html")

# Create account routes
@auth_router.get("/create-account-form", response_class=HTMLResponse)
def create_account_form(request: Request):
    return templates.TemplateResponse(request,"create-ac-form.html")

@auth_router.post("/create-account", response_class=HTMLResponse)
def create_account(request:Request,full_name:str=Form(...),user_id:str=Form(...),password:str=Form(...),confirm_password:str=Form(...)):
    if password != confirm_password:
        return templates.TemplateResponse(request,"create-ac-form.html", {"error": "Passwords did not match."})
    
    new_user = Openaccount(full_name, user_id, password)
    new_user = new_user.open_account()

    if isinstance(new_user, sql.IntegrityError):
        return templates.TemplateResponse(request,"create-ac-form.html", {"error": "User ID already exists."})
    elif isinstance(new_user, Exception):
        return templates.TemplateResponse(request,"create-ac-form.html", {"error": f"Error: {str(new_user)}"})
    else:   
        return templates.TemplateResponse(request,"account-success.html", {'full_name': full_name, 'user_id': user_id, 'account_number': new_user[0], 'creation_date': new_user[1]})
    
    # Login form route
@auth_router.get("/login-form", response_class=HTMLResponse)
def login_form(request: Request ): 
    return templates.TemplateResponse(request,"login-form.html", {"captcha": cap()})

# Login POST route (Strictly Authentication -> Redirect)
@auth_router.post("/login", response_class=HTMLResponse)
def login(request: Request, userid: str = Form(...), password: str = Form(...), real_captcha: str = Form(None), user_captcha: str = Form(...)):
    try:
        if real_captcha != user_captcha:
            new_captcha = cap()
            return templates.TemplateResponse(request,'login-form.html', {
                                        "captcha": new_captcha, 
                                        "error": "Security Verification Failed Due To Incorrect Captcha." })
        
        with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:#database connection
            with con.cursor() as cursor:
                cursor.execute("SELECT userid FROM users WHERE userid = %s AND password = %s", (userid, password))
                user_data = cursor.fetchone()
                if not user_data:
                    new_captcha = cap() 
                    return templates.TemplateResponse(request,'login-form.html', {
                                            "captcha": new_captcha, 
                                            "error": "Invalid User ID or Password."})
        
                # Give the VIP wristband and redirect to Dashboard!
                request.session["user_id"] = userid 
                return RedirectResponse(url='/dashboard/', status_code=303)

    except Exception as e:
        return f"An internal server error occurred while logging in: {str(e)}"
# Logout route
@auth_router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# CONTACT US ROUTE
@auth_router.get("/contact-form")
def contact_form(request:Request):
    return templates.TemplateResponse(request,"contact-form.html")

@auth_router.post("/contact",response_class=HTMLResponse)
def contact(request:Request,name:str=Form(...), age:int=Form(None), email:str=Form(None), num:str=Form(None), info:str=Form(None)):
    ip=request.headers.get("User-Agent")
    return templates.TemplateResponse(request,"contact.html",{"name":name,"age":age, "email-id":email, "mobile-num":num, "issue":info,"ip":ip})