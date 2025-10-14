from fastapi import APIRouter, UploadFile, File, HTTPException
from logic.salary_calculator import SalaryCalculator

router = APIRouter()

@router.post("/calculate-salary")
async def calculate_salary(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        contents = await file.read()
        calculator = SalaryCalculator()
        results = calculator.calculate(contents)
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")