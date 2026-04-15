import cv2

class StereoCamera:
    def __init__(self, left_id=0, right_id=1):
        self.capL = cv2.VideoCapture(left_id)
        self.capR = cv2.VideoCapture(right_id)

        # Set resolution (important for consistency)
        self.capL.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capL.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.capR.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capR.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def grab(self):
        self.capL.grab()
        self.capR.grab()

    def retrieve(self):
        retL, frameL = self.capL.retrieve()
        retR, frameR = self.capR.retrieve()
        return frameL, frameR

    def read(self):
        self.grab()
        return self.retrieve()

    def release(self):
        self.capL.release()
        self.capR.release()