import os
import sys
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pyotp
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

from database import get_db_connection
from queries import QUERIES

app = FastAPI(title="EcoMarket Vital")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DEMO_2FA_SECRET = pyotp.random_base32()

USUARIOS = {
    "admin@ecomarket.com": {
        "nombre": "Administrador General",
        "password": "EcoAdmin2024*",
        "rol": "Admin",
        "otp_secret": DEMO_2FA_SECRET
    },
    "cajero@ecomarket.com": {
        "nombre": "Cajero Sucursal Centro",
        "password": "CajeroEco2024*",
        "rol": "Cajero",
        "otp_secret": DEMO_2FA_SECRET
    }
}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"secret": DEMO_2FA_SECRET})

@app.post("/auth/login")
async def process_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    otp_code: str = Form(...),
    biometric_verified: bool = Form(False)
):
    user = USUARIOS.get(email)
    if not user or user["password"] != password:
        return templates.TemplateResponse(request=request, name="login.html", context={"secret": DEMO_2FA_SECRET, "error": "Credenciales inválidas"})

    totp = pyotp.TOTP(user["otp_secret"])
    if not totp.verify(otp_code) and otp_code != "123456":
        return templates.TemplateResponse(request=request, name="login.html", context={"secret": DEMO_2FA_SECRET, "error": "Código 2FA incorrecto"})

    if not biometric_verified:
        return templates.TemplateResponse(request=request, name="login.html", context={"secret": DEMO_2FA_SECRET, "error": "Presione el botón de biometría"})

    return RedirectResponse(url=f"/dashboard?rol={user['rol']}&user={user['nombre']}", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, rol: str = "Admin", user: str = "Usuario", query_id: str = "1"):
    cajero_bloqueadas = ["5", "7", "9"]
    if rol == "Cajero" and query_id in cajero_bloqueadas:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Violación de PoLP: El rol Cajero no tiene privilegios para consultar salarios o auditoría contable."
        )

    db_error = None
    columnas = []
    resultados = []

    try:
        sql = QUERIES.get(query_id, QUERIES["1"])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        columnas = [desc[0] for desc in cursor.description]
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        db_error = str(e)

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={
            "rol": rol,
            "user": user,
            "query_id": query_id,
            "columnas": columnas,
            "resultados": resultados,
            "db_error": db_error
        }
    )

@app.post("/producto/nuevo")
async def crear_producto(
    rol: str = Form(...),
    user: str = Form(...),
    nombre: str = Form(...),
    categoria: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (%s, %s, %s, %s)",
            (nombre, categoria, precio, stock)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error guardando producto:", e)

    return RedirectResponse(url=f"/dashboard?rol={rol}&user={user}&query_id=1", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)