@echo off

rem -----------------------------------------------------------------------
rem Check command line parameters
rem -----------------------------------------------------------------------
if "%1"==""   goto usage
if "%1"=="?"  goto usage
if "%1"=="-?" goto usage
if "%1"=="-h" goto usage
if "%1"=="--help" goto usage
goto %1
goto _eof

:usage
echo -----------------------------------------------------------------
echo bt_test makefile
echo -----------------------------------------------------------------
echo make clean          clean up temporary files
echo make help           make helpfiles (HTML, CHM and PDF)
echo make installer      make full installation (py2exe and nsis installer)
echo make doxygen        make doxygen documentation
echo make pip            Update Python libraries (using requirements.txt)

goto _eof

:pip
rem --- Update Python libraries (using requirements.txt)
	python.exe -m pip install --upgrade pip
	pip install -r requirements.txt --upgrade
	goto _eof

:doxygen
rem --- Generate DOXYGEN documentation
    call doxygen 
    goto _eof

:sphinx
rem --- Generate Spinx documentation
    pushd doc & call make html & popd
    goto _eof

:clean
rem --- Remove unneccessary files
	del /S *.bak
	rmdir /S /Q __pycache__
	pushd docs\doxygen & rmdir /S /Q html & popd

:_eof