# Generated Cmake Pico project file

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Initialise pico_sdk from installed location
# (note this can come from environment, CMake cache etc)

# == DO NEVER EDIT THE NEXT LINES for Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.0.0)
set(toolchainVersion 13_2_Rel1)
set(picotoolVersion 2.0.0)
include(LogicAnalyzer_Build_Settings.cmake)
include(${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)


# ====================================================================================
if(NOT BOARD_TYPE)
    message(FATAL_ERROR "Board not set, configure the build on LogicAnalyzer_Build_Settings.cmake")
endif()

if((BOARD_TYPE STREQUAL "BOARD_PICO_W") OR (BOARD_TYPE STREQUAL "BOARD_PICO_W_WIFI"))
    message(STATUS "Setting PICO_BOARD to pico_w")
    set(PICO_BOARD pico_w CACHE STRING "Board type")
    message(STATUS "Forcing Debug for W build")
    set(CMAKE_BUILD_TYPE Debug)
    if(TURBO_MODE)
        message(FATAL_ERROR "Cannot enable turbo mode for the Pico W")
    endif()
elseif(BOARD_TYPE STREQUAL "BOARD_PICO_2")
    message(STATUS "Setting PICO_BOARD to pico2")
    set(PICO_BOARD pico2 CACHE STRING "Board type")
else()
    message(STATUS "Setting PICO_BOARD to pico")
    set(PICO_BOARD pico CACHE STRING "Board type")
endif()

if(TURBO_MODE)
    message(WARNING "WARNING!! Turbo mode enabled! Device will be extremely overclocked and overvoltaged!")
    add_compile_definitions(TURBO_MODE)
endif()

if(NOT DEBUG_BUILD)
    if((BOARD_TYPE STREQUAL "BOARD_PICO") OR (BOARD_TYPE STREQUAL "BOARD_ZERO") OR (BOARD_TYPE STREQUAL "BOARD_PICO_2"))
        message(STATUS "Forcing Release for RAM-only build")
        set(CMAKE_BUILD_TYPE Release)
    endif()
endif()


# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(LogicAnalyzer C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Add executable. Default name is the project name, version 0.1

FILE(GLOB CSources *.c)
ADD_EXECUTABLE(LogicAnalyzer ${CSources})

# Enable ram-only build for the base pico and zero, increases timming precission
if(NOT DEBUG_BUILD)
    if((BOARD_TYPE STREQUAL "BOARD_PICO") OR (BOARD_TYPE STREQUAL "BOARD_ZERO") OR (BOARD_TYPE STREQUAL "BOARD_PICO_2"))
        message(STATUS "Setting RAM-only compilation")
        pico_set_binary_type(LogicAnalyzer copy_to_ram)
    endif()
endif()

# Create C header file with the name <pio program>.pio.h
pico_generate_pio_header(${PROJECT_NAME}  
        ${CMAKE_CURRENT_LIST_DIR}/LogicAnalyzer.pio
)

pico_set_program_name(LogicAnalyzer "LogicAnalyzer")
pico_set_program_version(LogicAnalyzer "6.0")
add_compile_definitions(FIRMWARE_VERSION="V6_0")

pico_enable_stdio_uart(LogicAnalyzer 0)
pico_enable_stdio_usb(LogicAnalyzer 1)

if(BOARD_TYPE STREQUAL "BOARD_PICO")
    message(STATUS "Configuring for Pico")
    add_compile_definitions(BUILD_PICO)
endif()
if(BOARD_TYPE STREQUAL "BOARD_PICO_2")
    message(STATUS "Configuring for Pico 2")
    add_compile_definitions(BUILD_PICO_2)
endif()
if(BOARD_TYPE STREQUAL "BOARD_PICO_W")
    message(STATUS "Configuring for Pico W without WiFi support")
    set(PICO_BOARD pico_w)
    add_compile_definitions(BUILD_PICO_W)
    set (CYW_LIB pico_cyw43_arch_none)
endif()
if(BOARD_TYPE STREQUAL "BOARD_PICO_W_WIFI")
    message(STATUS "Configuring for Pico W with WiFi support")
    add_compile_definitions(BUILD_PICO_W_WIFI)
    set (CYW_LIB pico_cyw43_arch_lwip_poll)
endif()
if(BOARD_TYPE STREQUAL "BOARD_ZERO")
    message(STATUS "Configuring for Zero")
    add_compile_definitions(BUILD_ZERO)
endif()

# Add any user requested libraries
target_link_libraries(LogicAnalyzer
        pico_stdlib
        hardware_dma
        hardware_pio
        hardware_clocks
        hardware_flash
        hardware_adc
        hardware_exception
        hardware_vreg
        pico_multicore
        pico_base_headers
        pico_multicore
        cmsis_core
        ${CYW_LIB}
        )

pico_add_extra_outputs(LogicAnalyzer)

target_include_directories(LogicAnalyzer PRIVATE ${CMAKE_CURRENT_LIST_DIR} )
