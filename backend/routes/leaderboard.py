from fastapi import APIRouter
from data import leaderboard_data

router = APIRouter(prefix='/api',tags=['leaderboard'])

@router.get('/leaderboard')
def get_leaderboard():
    return leaderboard_data