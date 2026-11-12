#Пока не нужно потом изменить название!!
#python -m uvicorn very_first:app --reload

import shutil
import uuid
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os
import csv
import hashlib
import itsdangerous
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from PIL import Image



SESSION_LIFETIME = timedelta(minutes=3)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="session")

white_urls = ["/", "/login", "/home", "/register", "/main", "/403", "/404", "/logout", ]


@app.get("/logout", response_class=HTMLResponse) #перехват адреса 
def logout(request: Request):
    request.session['username']
    return RedirectResponse("/login", 302)

@app.get("/", response_class=HTMLResponse) #перехват адреса 
def main_page(request: Request):
    return templates.TemplateResponse(request=request, name ="based_main.html")


@app.get("/home", response_class=HTMLResponse) #перехват адреса 
def home_page(request: Request):
    try:
        print(datetime.now(), request.session.get('session_starttime'))
        if datetime.now() - datetime.fromisoformat(str(request.session.get('session_starttime'))) >= SESSION_LIFETIME:
            # грохнуть сессию
            request.session.clear()
            return templates.TemplateResponse(
                            "login.html",
                            {"request": request, "error": "Время вашей сессии завершено, войдите заново"}
                        )       
        else:
            request.session['session_starttime'] = str(datetime.now())
        username = request.session.get('username')
        password_hash= request.session.get('hash_pass')
        print(username)
            
        return templates.TemplateResponse(request=request, 
                                        name="home.html", 
                                        context={'username': username,
                                                'hash_pass': password_hash})
    except:
        return RedirectResponse("/403", 302)

@app.get("/404", response_class=HTMLResponse) #перехват адреса 
def error_page(request: Request):
    return templates.TemplateResponse( request=request, name="404.html")

@app.get("/403", response_class=HTMLResponse) #перехват адреса 
def error_page(request: Request):
    return templates.TemplateResponse( request=request, name="403.html")

@app.get("/login", response_class=HTMLResponse) #перехват адреса 
def login_page(request: Request):
    return templates.TemplateResponse( request=request, name="login.html")

@app.post("/login")
def login(request: Request, 
        username: str = Form(...), 
        password: str = Form(...)):
    
    if not username or not password: # or not admin_login or not admin_password:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Все поля, обязательны!"}
            )
    print('here')
    try:
        user_list = pd.read_csv('user.csv')
    except:
        return templates.TemplateResponse(request=request,
                                name="register.html",
                                context= { "error": "Пользователей в системе нет, Стань первым"}
                            )
    else:
        user_df = pd.DataFrame(user_list)
        print(user_df)
        print(user_df['login'].values)
        if username in user_df['login'].values:
            print(f"{user_df[user_df['login']==username]}")
            hash_pass=user_df[user_df['login']==username].values[0][1]
            if verify_password(password, hash_pass):
                print(user_df[user_df['login']==username].values[0][1])
            else:
                return templates.TemplateResponse(request=request,
                                                name="login.html",
                                                context= { "error": "Неверный пароль"}
                                            )
        else:
            return templates.TemplateResponse(request=request,
                                            name="register.html",
                                            context= { "error": "Такого Пользователя в системе нет, зарегистрируйся"}
                                        )
    request.session["username"]= username
    request.session["hash_pass"]= hash_password(password)
    request.session['session_starttime'] = str(datetime.now())
    return RedirectResponse('/home', 302)



@app.get("/main", response_class=HTMLResponse) #перехват адреса 
def main_page(request: Request):
    return templates.TemplateResponse( request=request, name="based_main.html")

@app.get("/register", response_class=HTMLResponse) #перехват адреса 
def reg_page(request: Request):
    return templates.TemplateResponse( request=request, name="register.html")

@app.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    # admin_login: str = Form(...),
    # admin_password: str = Form(...)
    ):
    # print(admin_password)
    # print(admin_login)
    if not username or not password: # or not admin_login or not admin_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Все поля, обязательны!"}
        )
    hash_passwords=hash_password(password)
    try:
            user_list = pd.read_csv('user.csv')
    except:
            user_df = pd.DataFrame({'login': [username], 'pass': [hash_passwords]})
            user_df.to_csv('user.csv', index=False)
            return RedirectResponse('/home', 302)
    else:
        user_df = pd.DataFrame(user_list)
        print(user_df)
        print(user_df['login'].values)

        if username in user_df['login'].values:
            print("zanyato")
            return templates.TemplateResponse(request=request,
                        name="register.html",
                        context= { "error": "Такое имя пользователя занято"}
                    )
        
        else:
            new_user = pd.DataFrame({'login': [username], 'pass': [hash_passwords]})
            user_df = pd.concat([user_df, new_user], ignore_index=True)
            print(user_df)
            user_df.to_csv('user.csv', index=False)
            request.session["username"]= username
            request.session["hash_pass"]= hash_password(password)
            request.session['session_starttime'] = str(datetime.now())
            return RedirectResponse('/home', 302)

    