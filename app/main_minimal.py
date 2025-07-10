from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import activities, bundles, llm

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only the routers we need
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(bundles.router, prefix="/api/bundles", tags=["bundles"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])

@app.get("/")
async def root():
    return {"message": "Activity Bundle API"}