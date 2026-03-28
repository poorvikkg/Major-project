from fastapi import APIRouter

router = APIRouter()

@router.post("/add-person")
def add_person():
    return {"message": "Person added"}