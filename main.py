from modal import Image, Secret, Mount, Volume, App, asgi_app
from fastapi import FastAPI, Response, Query, Request
from typing import Union
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
import time
import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]

app = App(name="jwt-token-generation")
image = (Image.micromamba()
         .micromamba_install()
         .pip_install("PyJWT==2.9.0", "requests", "fastapi==0.111.0", "python-dotenv==1.0.0"))
         #PyJWY is the library for generating the tokens

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers['X-Process-Time'] = str(process_time)
        return response


# fastAPI app
token_app = FastAPI(title='JWT Token Gen',
                        summary="JWT Token Generation API", version="1.0",
                        contact={"name": "Cristian Vergara",
                                 "email": "cvergara@geti.cl"})

# Add CORSMiddleware
token_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'])
token_app.add_middleware(MyMiddleware)


@token_app.get("/")   # dummy
async def read_root():
    return {"Hello": "World"}


@token_app.get("/generate-token")
async def generate_token(client_id: int, client_name: str, extra_dummy: str,
                         expiration: int = Query(1, enum=[1, 2, 3], description='tiempo de expiracion en horas'),
                         binary_dummy: int = Query(1, enum=[1, 0])):
    try:
        # generates an encoded token based on a client id and client name with an expiration time in [1,3] hours
        # The dummy parameters can be deleted
        payload = {
            'data': {'client_id': client_id, 'client_name': client_name, 'extra_dummy': extra_dummy,
                     'binary_dummy': binary_dummy},
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiration)  # Token expiration time
        }
        # secret key can be modified, but it is needed for decoding
        # There is a function in utils.py in the streamlit app for decoding the token
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        temp = payload['data']
        print(f'token generated for: {temp}')
        return token

    except Exception as e:
        response = {
            "error": str(e)
        }


@app.function(image=image,
              secrets=[Secret.from_name("jwt-token-secret")])
@asgi_app(label='jwt-token-generation')
def fastapi_app():

    return token_app

