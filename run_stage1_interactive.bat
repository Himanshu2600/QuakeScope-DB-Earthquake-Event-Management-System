@echo off
TITLE QuakeScope DB - Stage 1 Interactive Runner
COLOR 0A

echo ===============================================================================
echo       QUAKESCOPE DB - STAGE 1: DEMO ^& SCREENSHOT CAPTURE RUNNER
echo       Course: CSE494 Intelligent NoSQL Databases
echo ===============================================================================
echo.
echo This runner will execute each Stage 1 milestone step-by-step.
echo At each pause, you can press Win + Shift + S to take your screenshot
echo and save it into screenshots\stage1\
echo.
pause

echo.
echo -------------------------------------------------------------------------------
echo STEP 1: DATASET INSPECTION
echo Target Screenshot: screenshots\stage1\01_dataset_inspection.png
echo Command: python scripts\inspect_dataset.py
echo -------------------------------------------------------------------------------
python scripts\inspect_dataset.py
echo.
echo [TAKE SCREENSHOT 01 NOW] - Press any key to continue to Step 2...
pause > nul

echo.
echo -------------------------------------------------------------------------------
echo STEP 2 ^& 3: MONGODB DATABASE SETUP ^& SCHEMA VALIDATION
echo Target Screenshot: screenshots\stage1\03_database_creation.png
echo Command: mongosh database\setup_database.js
echo -------------------------------------------------------------------------------
mongosh database\setup_database.js
echo.
echo [TAKE SCREENSHOT 03 NOW] - Press any key to continue to Step 4...
pause > nul

echo.
echo -------------------------------------------------------------------------------
echo STEP 4: DATASET IMPORT WITH DEDUPLICATION ^& BSON TYPE CONVERSION
echo Target Screenshot: screenshots\stage1\05_data_import.png
echo Command: python scripts\import_data.py
echo -------------------------------------------------------------------------------
python scripts\import_data.py
echo.
echo [TAKE SCREENSHOT 05 NOW] - Press any key to continue to Step 5...
pause > nul

echo.
echo -------------------------------------------------------------------------------
echo STEP 5: MONGOSH QUERY VERIFICATION ^& VALIDATION TEST
echo Target Screenshots: 
echo   - 06_document_structure.png
echo   - 07_record_count.png
echo   - 08_basic_queries.png
echo   - 09_validation_test.png
echo Command: mongosh database\verify_queries.js
echo -------------------------------------------------------------------------------
mongosh database\verify_queries.js
echo.
echo [TAKE SCREENSHOTS 06-09 NOW] - Press any key to finish...
pause > nul

echo.
echo ===============================================================================
echo STAGE 1 EXECUTION COMPLETE!
echo All outputs have been verified and logged in docs\stage1_notes.md.
echo ===============================================================================
pause
