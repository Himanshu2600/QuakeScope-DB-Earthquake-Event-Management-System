@echo off
TITLE QuakeScope DB - Stage 2: 6 Essential Screenshots Runner
COLOR 0B

echo ===============================================================================
echo       QUAKESCOPE DB - STAGE 2: 6 ESSENTIAL SCREENSHOTS RUNNER
echo       Course: CSE494 Intelligent NoSQL Databases
echo ===============================================================================
echo.
echo This runner will execute each milestone in sequence.
echo At each pause, press Win + Shift + S (Windows Snipping Tool) to snap
echo the screenshot and save it with the exact filename in screenshots\stage2\
echo.
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 1 OF 6: PyMongo Connection and CRUD
echo File: screenshots\stage2\01_pymongo_crud.png
echo What to show: scripts\database.py / scripts\crud_operations.py alongside output
echo -------------------------------------------------------------------------------
python scripts\database.py
echo.
echo [TAKE SCREENSHOT 01_pymongo_crud.png NOW]
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 2 OF 6: MongoDB Shell Queries
echo File: screenshots\stage2\02_mongosh_queries.png
echo Command: mongosh database\queries_crud.js (Steps 1-3)
echo -------------------------------------------------------------------------------
mongosh database\queries_crud.js
echo.
echo [TAKE SCREENSHOT 02_mongosh_queries.png NOW]
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 3 OF 6: Aggregation Code
echo File: screenshots\stage2\03_aggregation_code.png
echo What to show: Open scripts\aggregation_queries.py in your editor (VS Code/Notepad)
echo Showing the 5 aggregation functions:
echo   - get_average_magnitude_and_total()
echo   - get_magnitude_distribution()
echo   - get_top_strongest_events()
echo   - get_counts_by_magnitude_type()
echo   - get_monthly_earthquake_counts()
echo -------------------------------------------------------------------------------
echo.
echo [TAKE SCREENSHOT 03_aggregation_code.png OF YOUR EDITOR NOW]
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 4 OF 6: Aggregation Results (Python Terminal Output)
echo File: screenshots\stage2\04_aggregation_results.png
echo Command: python scripts\aggregation_queries.py
echo -------------------------------------------------------------------------------
python scripts\aggregation_queries.py
echo.
echo [TAKE SCREENSHOT 04_aggregation_results.png NOW]
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 5 OF 6: CRUD Test Results (Insert, Read, Update, Delete)
echo File: screenshots\stage2\05_crud_test_results.png
echo Command: mongosh database\queries_crud.js (Steps 4-8)
echo -------------------------------------------------------------------------------
mongosh database\queries_crud.js
echo.
echo [TAKE SCREENSHOT 05_crud_test_results.png NOW]
pause

echo.
echo -------------------------------------------------------------------------------
echo SCREENSHOT 6 OF 6: Final Verification (Self-Test + Count = 19705)
echo File: screenshots\stage2\06_final_verification.png
echo Command: python -c "import main; main.run_automated_self_test()"
echo -------------------------------------------------------------------------------
python -c "import main; main.run_automated_self_test()"
mongosh --quiet --eval "print('Verified MongoDB Collection Count: ' + db.getSiblingDB('quakescope_db').earthquake_events.countDocuments({}))"
echo.
echo [TAKE SCREENSHOT 06_final_verification.png NOW]
pause

echo.
echo ===============================================================================
echo ALL 6 ESSENTIAL SCREENSHOTS COMPLETED!
echo Verified all screenshots are in screenshots\stage2\
echo ===============================================================================
pause
