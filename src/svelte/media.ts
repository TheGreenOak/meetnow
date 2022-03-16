export default class Media {
    private videoStream?: MediaStream;
    private screenStream?: MediaStream;
    private audioStream?: MediaStream;

      /////////////////////////////////////////
     ///           MEDIA DEVICES           ///
    /////////////////////////////////////////

    public async getVideoDevices(): Promise<object> {
        return new Promise<object>((resolve, reject) => {
            const videoDevices = {};
            
            navigator.mediaDevices.enumerateDevices().then(devices => {
                devices.forEach(device => {
                    if (device.kind == "videoinput") {
                        videoDevices[device.deviceId] = device.label;
                    }
                });

                resolve(videoDevices);
            })
    
            .catch(err => reject(err));
        });
    }

    public async getAudioDevices(): Promise<object> {
        return new Promise<object>((resolve, reject) => {
            const audioDevices = {};

            navigator.mediaDevices.enumerateDevices().then(devices => {
                devices.forEach(device => {
                    if (device.kind == "audioinput") {
                        audioDevices[device.deviceId] = device.label;
                    }
                });

                resolve(audioDevices);
            })

            .catch(err => reject(err));
        });
    }

      /////////////////////////////////////////
     ///           MEDIA ENABLERS          ///
    /////////////////////////////////////////

    /**
     * This method turns on the user's webcam.
     * 
     * @param width The ideal width of the video
     * @param height The ideal height of the video
     * @returns A promise. Once resolved, the webcam is on. Rejection upon any error
     */
    public async enableVideo(width: number, height: number, id?: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            if (this.videoStream) resolve();

            navigator.mediaDevices.getUserMedia({
                video: {
                    deviceId: id,
                    width: { ideal: width },
                    height: { ideal: height }
                }
            })
            
            .then(stream => {
                this.videoStream = stream;
                resolve();
            })
    
            .catch(err => reject(err));
        });
    }

    /**
     * This method turns on the user's microphone.
     * 
     * @param noiseSuppresion Whether or not to enable default noise suppression
     * @returns A promise. Once resolved, the microphone is on. Rejection upon any error
     */
    public async enableAudio(noiseSuppression: boolean, id?: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            if (this.audioStream) resolve();

            navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: id,
                    noiseSuppression: noiseSuppression
                }
            })

            .then(stream => {
                this.audioStream = stream;
                resolve();
            })

            .catch(err => reject(err));
        });
    }

    /**
     * This method turns on the user's screenshare.
     * 
     * @param width The ideal width of the video
     * @param height The ideal height of the video
     * @returns A promise. Once resolved, the webcam is on. Rejection upon any error
     */
    public async enableScreenshare(width: number, height: number): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            if (this.screenStream) resolve();

            navigator.mediaDevices.getDisplayMedia({
                video: {
                    width: { ideal: width },
                    height: { ideal: height }
                }
            })

            .then(stream => {
                this.screenStream = stream;
                resolve();
            })

            .catch(err => reject(err));
        });
    }

      /////////////////////////////////////////
     ///           MEDIA DISABLERS         ///
    /////////////////////////////////////////

    public disableVideo(): void {
        this.videoStream?.getVideoTracks()[0].stop();
        this.videoStream = undefined;
    }

    public disableAudio(): void {
        this.audioStream?.getAudioTracks()[0].stop();
        this.audioStream = undefined;
    }

    public disableScreenshare(): void {
        this.screenStream?.getVideoTracks()[0].stop();
        this.screenStream = undefined;
    }

      /////////////////////////////////////////
     ///           MEDIA GETTERS           ///
    /////////////////////////////////////////

    public getVideoStream(): MediaStream | undefined {
        return this.videoStream;
    }

    public getAudioStream(): MediaStream | undefined {
        return this.audioStream;
    }

    public getScreenStream(): MediaStream | undefined {
        return this.screenStream;
    }

    public async getVideoFrame(): Promise<string> {
        return new Promise<string>((resolve, reject) => {
            if (this.videoStream) {
                new ImageCapture(this.videoStream.getVideoTracks()[0]).grabFrame().then(bitmap =>  {
                    resolve(this.bitmapToString(bitmap));
                })

                .catch(err => { reject(err) });
            } else {
                reject("Video is not on!");
            }
        });
    }

    private bitmapToString(bitmap: ImageBitmap): string {
        let tempCanvas: HTMLCanvasElement = document.createElement("canvas");
        let canvasCtx: CanvasRenderingContext2D = tempCanvas.getContext("2d");

        let rawData: Uint8ClampedArray;
		let converted = "";

        tempCanvas.width = bitmap.width;
        tempCanvas.height = bitmap.height;

        canvasCtx.drawImage(bitmap, 0, 0);
        rawData = canvasCtx.getImageData(0, 0, bitmap.width, bitmap.height).data;

		for (let i = 0; i < rawData.length; i += 4) {
			for (let j = 0; j < 3; j++) {
				converted += String.fromCharCode(rawData[i + j]);
			}
		}

		return converted;
	}
    
    private stringToBitmap(str: string, width: number, height: number): Promise<ImageBitmap> {
        return new Promise<ImageBitmap>((resolve, reject) => {
            let converted: Uint8ClampedArray = new Uint8ClampedArray(width * height * 4);

            let currAlpha = 0;
            let j = 0;
    
            for (let i = 0; i < (width * height * 3); i += 3) {
                for (j = 0; j < 3; j++) {
                    converted[i + j + currAlpha] = str[i + j].charCodeAt(0);
                }
    
                converted[i + j + currAlpha] = 255;
                currAlpha++;
            }
    
            createImageBitmap(new ImageData(converted, width, height)).then(bitmap => {
                resolve(bitmap);
            })
    
            .catch(err => reject(err));
        });
	}
};