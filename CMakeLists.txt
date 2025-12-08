cmake_minimum_required(VERSION 3.12)

# initialize pico_sdk from GIT
# (note this can come from environment, CMake cache etc)
# set(PICO_SDK_FETCH_FROM_GIT on)

# pico_sdk_import.cmake is a single file copied from this SDK
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(pico_voice_rover)

# initialize the Pico SDK
pico_sdk_init()

# Define ARM_CPU, CMSIS ROOT and DSP to use CMSIS-DSP
set(ARM_CPU "cortex-m0plus")
set(ROOT ${CMAKE_CURRENT_LIST_DIR}/lib/CMSIS_5)
set(DSP ${ROOT}/CMSIS/DSP)

set(CONFIGTABLE ON)
set(RFFT_Q15_256 ON)
set(ALLFAST ON)

# Microphone capture type
set(MIC_SETUP_VALUE 2)  # 1 = PDM, 2 = ANALOG
add_definitions(-DMIC_SETUP=${MIC_SETUP_VALUE})

# include CMSIS-DSP .cmake for GCC Toolchain
include(${DSP}/Toolchain/GCC.cmake)

# add CMSIS-DSP Source directory as subdirectory
add_subdirectory(${DSP}/Source EXCLUDE_FROM_ALL)

# rest of your project
add_executable(pico_voice_rover
    ${CMAKE_CURRENT_LIST_DIR}/src/main.cpp
    ${CMAKE_CURRENT_LIST_DIR}/src/dsp_pipeline.cpp
    ${CMAKE_CURRENT_LIST_DIR}/src/ml_model.cpp
)

set(VOICE_ROVER_LINK_LIST
    pico_stdlib
    hardware_pwm
    pico-tflmicro
    CMSISDSPTransform CMSISDSPSupport CMSISDSPCommon CMSISDSPComplexMath CMSISDSPFastMath CMSISDSPBasicMath
)

if(MIC_SETUP_VALUE STREQUAL "1")     # 1 = PDM
    list(APPEND VOICE_ROVER_LINK_LIST pico_pdm_microphone)
elseif(MIC_SETUP_VALUE STREQUAL "2") # 2 = ANALOG
    list(APPEND VOICE_ROVER_LINK_LIST pico_analog_microphone)
else()
    message(FATAL_ERROR "Unknown MIC_TYPE: ${MIC_TYPE}")
endif()

target_link_libraries(pico_voice_rover
    ${VOICE_ROVER_LINK_LIST}
)

# enable usb output, disable uart output
pico_enable_stdio_usb(pico_voice_rover 1)
pico_enable_stdio_uart(pico_voice_rover 0)

# create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(pico_voice_rover)

add_subdirectory("lib/microphone-library-for-pico" EXCLUDE_FROM_ALL)
add_subdirectory("lib/pico-tflmicro" EXCLUDE_FROM_ALL)
add_subdirectory("test")

# === Auto-patch pico-tflmicro ===
execute_process(
    COMMAND patch -p1 -N -r - -i ${CMAKE_CURRENT_SOURCE_DIR}/patches/pico_tflmicro_limits_fix.patch
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/pico-tflmicro
)

# Force external CMSIS_5
target_include_directories(pico-tflmicro PUBLIC
    ${ROOT}/CMSIS/Core/Include
)