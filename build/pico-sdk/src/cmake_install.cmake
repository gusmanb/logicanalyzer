# Install script for directory: C:/Users/backu/.pico-sdk/sdk/2.2.0/src

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "C:/Program Files (x86)/LogicAnalyzer")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Debug")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "TRUE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "C:/Users/backu/.pico-sdk/toolchain/14_2_Rel1/bin/arm-none-eabi-objdump.exe")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/boot_picobin_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/boot_picoboot_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/boot_uf2_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_base_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_usb_reset_interface_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_bit_ops_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_binary_info/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_divider_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_sync/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_time/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_util/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/pico_stdlib_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/common/hardware_claim/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2350/pico_platform/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2350/hardware_regs/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2350/hardware_structs/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2350/boot_stage2/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_base/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_adc/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_boot_lock/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_clocks/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_divider/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_dma/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_exception/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_flash/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_gpio/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_i2c/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_interp/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_irq/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_pio/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_pll/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_pwm/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_resets/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_spi/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_sync/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_sync_spin_lock/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_ticks/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_timer/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_uart/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_vreg/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_watchdog/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_xip_cache/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_xosc/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_powman/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_riscv_platform_timer/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_sha256/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_dcp/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/hardware_rcp/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/boot_bootrom_headers/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_platform_common/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_platform_compiler/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_platform_sections/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_platform_panic/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_aon_timer/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_bootrom/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_bootsel_via_double_reset/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_multicore/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_unique_id/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_atomic/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_bit_ops/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_divider/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_double/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_int64_ops/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_flash/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_float/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_mem_ops/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_malloc/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_printf/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_rand/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_sha256/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdio_semihosting/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdio_uart/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdio_rtt/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/cmsis/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/tinyusb/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdio_usb/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_i2c_slave/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_async_context/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_btstack/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_cyw43_driver/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_mbedtls/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_lwip/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_cyw43_arch/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_time_adapter/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_crt0/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_clib_interface/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_cxx_options/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_standard_binary_info/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_standard_link/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_fix/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_status_led/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_runtime_init/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_runtime/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdio/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/rp2_common/pico_stdlib/cmake_install.cmake")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "C:/Users/backu/Documents/GitHub/logicanalyzer/Firmware/LogicAnalyzer_V2/build/pico-sdk/src/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
