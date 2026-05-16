from datetime import date
from fastapi import HTTPException, status

def date_validation(log_date: date):
    if log_date > date.today() :
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Can't add a log in future date."
        )