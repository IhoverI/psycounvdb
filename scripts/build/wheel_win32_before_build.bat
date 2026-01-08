@echo on

pip install "delvewheel>=1.0.0" wheel

vcpkg install libpq[core,ssl]:x64-windows-release openssl:x64-windows-release

pipx install .\scripts\build\pg_config_vcpkg_stub\

echo "Installed DLLs in vcpkg bin:"
dir "%VCPKG_INSTALLATION_ROOT%\installed\x64-windows-release\bin\*.dll"
