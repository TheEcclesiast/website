import requests
from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from starlette.staticfiles import StaticFiles
import os
load_dotenv()
API_KEY = os.getenv("API_KEY")
HOUSECALL_PRO_CUSTOMER_URL = "https://api.housecallpro.com/customers"
HOUSECALL_PRO_JOB_URL = "https://api.housecallpro.com/jobs"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Маршруты для шаблонов
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/reviews", response_class=HTMLResponse)
async def read_reviews(request: Request):
    return templates.TemplateResponse("reviews.html", {"request": request})

@app.get("/order", response_class=HTMLResponse)
async def order_form(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.post("/submit_order", response_class=HTMLResponse)
async def submit_order(request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    job_description: str = Form(...)
):
    # Подготовка данных для создания клиента
    customer_data = {
        "first_name": name.split()[0],
        "last_name": " ".join(name.split()[1:]),
        "notifications_enabled": True,
        "mobile_number": phone,
        "addresses": [
            {
                "street": address,
                "street_line_2": "",
                "city": city,
                "state": state,
                "zip": zip,
            }
        ],
        "notes": "Заявка с сайта"
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Отправка данных на создание клиента
    customer_response = requests.post(HOUSECALL_PRO_CUSTOMER_URL, json=customer_data, headers=headers)

    if customer_response.status_code == 201:
        customer_id = customer_response.json()["id"]  # Получение ID клиента
        address_id = customer_response.json()["addresses"][0]["id"]  # Получение ID адреса

        # Создание работы
        job_data = {
            "customer_id": customer_id,
            "address_id": address_id,
            "line_items": [
                {
                    "name": "Заявка",
                    "description": job_description,
                    "unit_price": 0,
                    "quantity": 1,
                    "unit_cost": 0
                }
            ],
            "notes": "Заявка с сайта"
        }

        # Отправка данных на создание работы
        job_response = requests.post(HOUSECALL_PRO_JOB_URL, json=job_data, headers=headers)

        if job_response.status_code == 201:
            job_id = job_response.json()["id"]
            return templates.TemplateResponse("upload_file.html", {"request": request, "job_id": job_id})
        else:
            return HTMLResponse(f"<p>Ошибка при создании работы: {job_response.status_code} - {job_response.text}</p>")
    else:
        return HTMLResponse(f"<p>Ошибка при создании клиента: {customer_response.status_code} - {customer_response.text}</p>")





# Маршрут для загрузки файла с job_id в URL
@app.get("/upload_file/{job_id}", response_class=HTMLResponse)
async def upload_file_form(request: Request, job_id: str):
    return templates.TemplateResponse("upload_file.html", {"request": request, "job_id": job_id})

# Обработка загрузки файла
@app.post("/upload_attachment/{job_id}")
async def upload_attachment(request: Request, job_id: str, file: UploadFile = File(...)):
    # Получаем файл
    file_contents = await file.read()

    # Отправляем файл в Housecall Pro
    url = f"{HOUSECALL_PRO_JOB_URL}/{job_id}/attachments"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }
    files = {'file': (file.filename, file_contents, file.content_type)}

    # Отправляем запрос
    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 202 or response.status_code == 201:
        return templates.TemplateResponse("confirmation.html", {"request": request})
    else:
        return HTMLResponse(f"<h1>Error: {response.status_code} - {response.text}</h1>")

@app.get("/confirmation", response_class=HTMLResponse)
async def confirmation_page(request: Request):
    return templates.TemplateResponse("confirmation.html", {"request": request})