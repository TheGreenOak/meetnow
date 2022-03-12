.DEFAULT_GOAL := build

# Variables
COMPILER    = g++
CPP_FLAGS   = -Wall -g --debug
SOURCE_DIR  = src/**.cpp
INCLUDES    = -I/usr/include/opencv4 -Iinclude
OPENCV_FIX  = $$(pkg-config opencv4 --libs --cflags)
OUT_DIR     = bin
OUT_FILE    = build

# JS Variables
JS_COMPILER = emcc
JS_FLAGS    = -s EXPORTED_FUNCTIONS=_encode,_decode -s EXPORTED_RUNTIME_METHODS=cwrap -O3
JS_INCLUDES = -Iinclude
JS_SOURCE   = src/codec.cpp
JS_OUT_FILE = codec.js

build:
	mkdir -p bin
	${COMPILER} ${CPP_FLAGS} -o ${OUT_DIR}/${OUT_FILE} ${INCLUDES} ${OPENCV_FIX} ${SOURCE_DIR}

js:
	mkdir -p bin
	${JS_COMPILER} ${JS_SOURCE} -o ${OUT_DIR}/${JS_OUT_FILE} ${JS_INCLUDES} ${JS_FLAGS}

run:
	./${OUT_DIR}/${OUT_FILE}
