import cv2
import os

# initiate the video source
video = 'C:/Work Files/Tech Forum/Facial Recognition/Train Videos/Vamsi.MOV'
DestinationFolder = 'C:\Work Files\Tech Forum\Facial Recognition\Training Pics'


# Function to check if the destination folder exists else creates it.
def FolderCheck(DestinationFolder):
    ReturnMessage = ''

    try:
        if not os.path.exists(DestinationFolder):
            os.makedirs(DestinationFolder)
            ReturnMessage = 'Folder Created'
        else:
            ReturnMessage = 'Folder Exists'

    # exit if there is an error creating the folder
    except:
        ReturnMessage = 'Error creating the destination folder.'

    return (ReturnMessage)


def ProcessVideo(VideoFile, DestinationFolder, DebugFlag):
    # Open the video and capture 30 frames at equal intervals.
    # initiate the frame counter
    ImageCounter = 0
    FrameCounter = 0
    Video = cv2.VideoCapture(VideoFile)

    while Video.isOpened():
        ret, frame = Video.read()
        print(ret)
        if ret:
            # print(ret)
            # if DebugFlag != 0:
            print(os.path.join(DestinationFolder, f'frame{ImageCounter}.jpg Created'))
            cv2.imwrite(os.path.join(DestinationFolder, f'frame{ImageCounter}.jpg'), frame)
            FrameCounter += 10  # this will help the processor jump a few frames before capturing the next image.
            Video.set(1, FrameCounter)
            ImageCounter += 1
        else:
            print(ret)
            Video.release()
            break
        return


FolderMessage = FolderCheck(DestinationFolder)

ProcessVideo(video, DestinationFolder, 1)

