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
JS_FLAGS_OBJ = -c
JS_FLAGS_LIB = -shared
JS_INCLUDES  = -Iinclude
JS_SOURCE    = src/codec.cpp
OBJ_FILE     = codec.o
LIB_FILE     = codec.so

build:
	mkdir -p bin
	${COMPILER} ${CPP_FLAGS} -o ${OUT_DIR}/${OUT_FILE} ${INCLUDES} ${OPENCV_FIX} ${SOURCE_DIR}

js:
	mkdir -p bin
	${COMPILER} ${JS_SOURCE} -o ${OUT_DIR}/${OBJ_FILE} ${JS_INCLUDES} ${JS_FLAGS_OBJ} && ${COMPILER} ${JS_FLAGS_LIB} -o ${OUT_DIR}/${LIB_FILE} ${JS_INCLUDES} ${OUT_DIR}/${OBJ_FILE}

run:
	./${OUT_DIR}/${OUT_FILE}
