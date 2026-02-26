from fastapi import APIRouter
from data import feed_data

router = APIRouter(prefix='/api',tags=['feed'])

@router.get('/feed')
def get_feed():
    return feed_data
