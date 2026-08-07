from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import websocket, game

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket.router)
app.include_router(game.router)

@app.on_event("startup") # type: ignore
async def startup():
    # Inicialmente no hay partida, pero si ya hay usuarios conectados, 
    # el gestor se encargará cuando se registren.
    pass