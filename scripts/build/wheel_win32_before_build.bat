@echo on
setlocal enabledelayedexpansion

echo "=== Debug: Current directory ==="
cd
echo "=== Debug: VCPKG_INSTALLATION_ROOT = %VCPKG_INSTALLATION_ROOT% ==="

echo "=== Installing build tools ==="
pip install "delvewheel>=1.0.0" wheel
if %ERRORLEVEL% NEQ 0 (
    echo "Warning: delvewheel install failed, continuing anyway"
)

echo "=== Installing vcpkg packages ==="
REM libpq in vcpkg automatically links with openssl, no need for feature flags
echo "Running: vcpkg install libpq:x64-windows-release openssl:x64-windows-release"
vcpkg install libpq:x64-windows-release openssl:x64-windows-release
set VCPKG_RESULT=!ERRORLEVEL!
echo "vcpkg install returned: %VCPKG_RESULT%"
if !VCPKG_RESULT! NEQ 0 (
    echo "ERROR: vcpkg install failed with code %VCPKG_RESULT%"
    exit /b 1
)

echo "=== Checking vcpkg installed files ==="
dir "%VCPKG_INSTALLATION_ROOT%\installed\x64-windows-release\lib\*pq*" 2>nul || echo "No libpq lib files found"
dir "%VCPKG_INSTALLATION_ROOT%\installed\x64-windows-release\include\libpq*" 2>nul || echo "No libpq include dir found"

echo "=== Installing pg_config stub ==="
echo "Current directory for pip install:"
cd
dir scripts\build\pg_config_vcpkg_stub\ 2>nul || echo "pg_config_vcpkg_stub directory not found"

REM Use pip instead of pipx (pipx may not be available in cibuildwheel environment)
pip install scripts\build\pg_config_vcpkg_stub\
if %ERRORLEVEL% NEQ 0 (
    echo "ERROR: pg_config stub install failed"
    echo "=== Trying with full path ==="
    pip install %CD%\scripts\build\pg_config_vcpkg_stub\
    if %ERRORLEVEL% NEQ 0 (
        echo "ERROR: pg_config stub install still failed"
        exit /b 1
    )
)

echo "=== Testing pg_config stub ==="
pg_config --libdir
if %ERRORLEVEL% NEQ 0 (
    echo "Warning: pg_config --libdir failed"
)

echo "=== Installed DLLs in vcpkg bin ==="
dir "%VCPKG_INSTALLATION_ROOT%\installed\x64-windows-release\bin\*.dll" 2>nul || echo "No DLLs found in vcpkg bin"

echo "=== before_build completed successfully ==="
exit /b 0
