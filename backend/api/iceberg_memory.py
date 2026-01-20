from fastapi import APIRouter
from memory.iceberg_memory import IcebergMemory

router = APIRouter()
memory = IcebergMemory()

@router.get("/iceberg/memory")
def iceberg_memory():
    return memory.recent(days=3)
