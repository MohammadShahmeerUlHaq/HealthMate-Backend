from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from models.users import User
from crud.sugar_logs import (
    create_sugar_log,
    get_sugar_log_by_id,
    get_sugar_logs_by_schedule,
    get_sugar_logs_by_user,
    get_sugar_logs_by_date_range,
    get_sugar_logs_by_date,
    update_sugar_log,
    delete_sugar_log
)
from schemas.sugar_logs import SugarLogCreate, SugarLogUpdate, SugarLogOut
from middlewares.auth import get_current_user

router = APIRouter()

@router.post("/{schedule_id}", response_model=SugarLogOut, status_code=201)
def create_log(schedule_id: int, data: SugarLogCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return create_sugar_log(db, user.id, schedule_id, data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/log/{log_id}", response_model=SugarLogOut)
def get_log_by_id(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    log = get_sugar_log_by_id(db, log_id, user.id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@router.get("/schedule/{schedule_id}", response_model=List[SugarLogOut])
def get_logs_by_schedule(schedule_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_sugar_logs_by_schedule(db, schedule_id, user.id)

@router.get("/user", response_model=List[SugarLogOut])
def get_logs_by_user(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_sugar_logs_by_user(db, user.id)


@router.get("/date", response_model=List[SugarLogOut])
def get_logs_by_date_or_range(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if date_from and date_to:
        logs = get_sugar_logs_by_date_range(db, current_user.id, date_from, date_to)
    elif date_from:
        logs = get_sugar_logs_by_date(db, current_user.id, date_from)
    else:
        raise HTTPException(status_code=400, detail="Please provide at least date_from or both date_from and date_to")

    return logs

# @router.get("/date-range", response_model=List[SugarLogOut])
# def get_logs_by_date_range(
#     start: date = Query(...),
#     end: date = Query(...),
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     return get_sugar_logs_by_date_range(db, user.id, start, end)

# @router.get("/date", response_model=List[SugarLogOut])
# def get_logs_by_date(
#     date_val: date = Query(..., alias="date"),
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     return get_sugar_logs_by_date(db, user.id, date_val)

@router.put("/{log_id}", response_model=SugarLogOut)
def update_log(log_id: int, data: SugarLogUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        log = update_sugar_log(db, log_id, user.id, data)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        return log
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not delete_sugar_log(db, log_id, user.id):
        raise HTTPException(status_code=404, detail="Log not found")
    return
