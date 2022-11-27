# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "F:/PicoSDK/Pico/pico-sdk/tools/pioasm"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/tmp"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/src/PioasmBuild-stamp"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/src"
  "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/src/PioasmBuild-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/src/PioasmBuild-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "F:/PicoSDK/Projects/LogicAnalyzer/build/pioasm/src/PioasmBuild-stamp${cfgdir}") # cfgdir has leading slash
endif()
