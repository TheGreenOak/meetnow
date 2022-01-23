.DEFAULT_GOAL := build

# Variables
COMPILER    = g++
CPP_FLAGS   = -Wall -g --debug
SOURCE_DIR  = src/**
INCLUDES    = -I/usr/include/opencv4 -Iinclude
OPENCV_FIX  = $$(pkg-config opencv4 --libs --cflags)
OUT_DIR     = bin
OUT_FILE    = build

build:
	mkdir -p bin
	${COMPILER} ${CPP_FLAGS} -o ${OUT_DIR}/${OUT_FILE} ${INCLUDES} ${OPENCV_FIX} ${SOURCE_DIR}

run:
	./${OUT_DIR}/${OUT_FILE}