#include <iostream>
#include <opencv4/opencv2/opencv.hpp>

#include "codec.h"

int main() {
    cv::Mat image;
    cv::Mat oldImage;
    cv::VideoCapture cap(0);

    if (!cap.isOpened()) {
        std::cout << "Unable to open Webcam";
        return 1;
    }

    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    cap >> oldImage;
    
    std::cout << "WIDTH: " << oldImage.cols << std::endl;
    std::cout << "HEIGHT: " << oldImage.rows << std::endl;

    encode(oldImage.data, nullptr, oldImage.cols, oldImage.rows);

    cv::waitKey(1000);
    cap >> image;

    encode(image.data, oldImage.data, image.cols, image.rows);

    // unsigned char* rawPixels = image.data;
    // unsigned char* pixels = new unsigned char[image.rows * image.cols * 3];

    // for (int i = 0; i < image.rows; i++) {
    //     for (int j = 0; j < image.cols; j++) {
    //         pixels[i * image.rows + j] = (int)rawPixels[i * image.rows + j + 2];
    //         pixels[i * image.rows + j + 1] = (int)rawPixels[i * image.rows + j + 1];
    //         pixels[i * image.rows + j + 2] = (int)rawPixels[i * image.rows + j + 0];
    //     }
    // }

    return 0;
}
