cmake_minimum_required(VERSION 3.16)
project(qit-cpp-proton-shim VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(ProtonCpp REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(JSONCPP REQUIRED jsoncpp)

# Shim executable
add_executable(qit-shim-cpp
    src/main.cpp
    src/sender.cpp
    src/receiver.cpp
    src/type_codec.cpp
)

target_include_directories(qit-shim-cpp PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${JSONCPP_INCLUDE_DIRS}
)

target_link_libraries(qit-shim-cpp
    Proton::cpp
    ${JSONCPP_LIBRARIES}
)

# Installation
install(TARGETS qit-shim-cpp
    RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin
)
