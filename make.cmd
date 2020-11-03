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
	
:doctest
	pushd src 
	pytest --doctest-modules --doctest-continue-on-failure --disable-warnings --doctest-ignore-import-errors

	popd
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
	del /S /Q *.bak
	rmdir /S /Q __pycache__
	rmdir /S /Q .pytest_cache
	pushd src & rmdir /S /Q dbase & popd
	pushd src & rmdir /S /Q .pytest_cache & popd
	pushd src\lib & rmdir /S /Q .pytest_cache & popd
	pushd tests & rmdir /S /Q .pytest_cache & popd
	pushd tests & rmdir /S /Q dbase & popd
	rem --- Clean doxygen output
	pushd doc\doxygen & rmdir /S /Q html & popd
	rem --- Clean Sphinx output
	pushd doc & .\make clean & popd
	goto _eof

:_eof