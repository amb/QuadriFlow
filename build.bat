mkdir build
cd build
cmake .. -DPYTHON_EXECUTABLE="C:/Python3/python.exe" -DBUILD_OPENMP="1" -DCMAKE_TOOLCHAIN_FILE=E:\dev\libs\vcpkg\scripts\buildsystems\vcpkg.cmake -G"Visual Studio 15 2017 Win64"
cmake --build . --target ALL_BUILD --config Release
copy ..\build\Release\*.pyd ..\addon\win64\
cd ..
