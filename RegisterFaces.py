import os
import shutil
# import AWSRekognition as AR#custom module to upload images to AWS and index them
import VideoProcessor as VP  # custom module to take a video file and split it to images
import easygui as EG  # to open file dialog
import boto3  # AWS library
from botocore.exceptions import ClientError


def CreateProcessedFolder(ProcessedFolderPath, DebugFlag):
    if os.path.exists(ProcessedFolderPath) == True:
        if DebugFlag != 0:
            print('Processed folder checked and it exists')
        ReturnCode = 0
    else:
        os.makedirs(ProcessedFolderPath)
        if DebugFlag != 0:
            print('Processed folder created')
        ReturnCode = 0

    return ReturnCode


def CreateCollection(CollectionName, DebugFlag=0):
    '''This function will create a new collection by the name provided if does not exist already
    Inputs:
    CollectionName: Collection ID to be stored in AWS Rekognition.
    DebugFlga: Pass 0 for quiet mode, 1 to print messages out at logical points.'''
    client = boto3.client('rekognition')
    ReturnCode = 0

    # get all the collections in the rekognition memory
    Response = client.list_collections(MaxResults=2)

    # retrieve collections
    Collections = Response['CollectionIds']

    # check if the collection exists
    if CollectionName in Collections:
        if DebugFlag != 0:
            print(f'Collection {CollectionName} found.')
        ReturnCode = 1
    else:
        try:

            # create the collection if it does not exist.
            Response = client.create_collection(CollectionId=CollectionName)

            # if the debug flag is on print the message
            if DebugFlag != 0:
                print(f'Collection {CollectionName} created.')
            ReturnCode = 2
        except ClientError as Err:
            print('Error creating Collection')
            ReturnCode = -1

    return ReturnCode


def UploadImages(BucketName, Image, S3ObjectName=None, DebugFlag=0):
    """This function will upload the provided image to the specified S3 bucket
    Inputs:
    BucketName: Which S3 bucket is the image uploaded to.
    Image: Image location on the local drive
    S3ObjectName: What would you like the image name to be on the bucket. If no name is specified, file name will be used.
    """
    ReturnCode = 0

    # If S3 object_name was not specified, use file_name
    if S3ObjectName is None:
        S3ObjectName = os.path.basename(Image)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        if DebugFlag != 0:
            print('Starting Uploding!!!')
            print(Image)
        with open(Image, 'rb') as uploadimage:
            print(BucketName, 'BucketName')
            print(S3ObjectName, 'S3ObjectName')
            response = s3_client.upload_fileobj(uploadimage, BucketName, S3ObjectName)

        ReturnCode = 0
    except ClientError as e:
        print(ClientError)

        ReturnCode = e

    return ReturnCode


def IndexFaces(CollectionName, BucketName, PhotoLocation, PhotoMetaData, DebugFlag=0):
    '''This function will upload an image to S3bucket and then index it to the provided collection
    Inputs:
    CollectionName: Rekognition Collection name to which the faces have to be added
    BucketName: S3BucketName to which the photos have to be added
    Photolocation: Physical location of the photo in your local drive
    PhotoMetadata: Identifiying info about the person being indexed
    DebugFlag: To print out messages'''

    client = boto3.client('rekognition')
    ReturnCode = 0

    # upload image to S3Bucket
    Upload = UploadImages(BucketName=BucketName, Image=PhotoLocation, S3ObjectName=None, DebugFlag=DebugFlag)
    print(Upload)

    # if there was an error, exit
    if Upload != 0:
        return Upload

    S3ObjectName = os.path.basename(PhotoLocation)

    # Index faces to the collection
    try:
        if DebugFlag != 0:
            print('Starting indexing!!!!')
        IndexFacesResponse = client.index_faces(CollectionId=CollectionName
                                                , Image={'S3Object': {'Bucket': BucketName, 'Name': S3ObjectName}}
                                                , ExternalImageId=PhotoMetaData
                                                , MaxFaces=1
                                                , QualityFilter="AUTO"
                                                , DetectionAttributes=['ALL'])
        print(IndexFacesResponse)
    except ClientError as err:
        print('There was an error indexing the faces')
        print(err)
        ReturnCode = 'There was an error indexing the faces'

    return ReturnCode


def ProcessImages(VideoLocation, VideoMetaData, DestinationFolder, DebugFlag):
    '''This function will take a video file, extract frames from it, upload it to S3 bucket and index it to a new collection.
    Inputs:
    VideoLocation: Path to the video file
    VideoMetadata: Identifiying information about the person.
    Destination Folder: Where do you want the extracted pictures to be saved on the local drive
    DebugFlag: Prints out messages when its 1'''

    # check if the destination folder exists.
    FolderCheck = VP.FolderCheck(DestinationFolder=DestinationFolder)

    if FolderCheck == 'Error creating the destination folder.':
        return
    else:
        VP.ProcessVideo(VideoFile=VideoLocation, DestinationFolder=DestinationFolder, DebugFlag=DebugFlag)

    # get the list of files from the destination folder.
    Pictures = os.listdir(DestinationFolder)

    # set the collection name
    CollectionName = VideoMetaData + '-Collection'

    # set the S3BucketName
    BucketName = 'facialrecognitionbucket'

    # check the processed folder:
    FolderPath = f'C:/Work Files/Tech Forum/Facial Recognition/Processed Pictures/{VideoMetaData}'
    FolderCheck = CreateProcessedFolder(ProcessedFolderPath=FolderPath, DebugFlag=DebugFlag)

    print(FolderCheck, 'Folder check')

    IndexMessage = 'Sucess'
    try:
        # index each image
        for Picture in Pictures:
            IndexMessage = IndexFaces(CollectionName=CollectionName
                                      , BucketName=BucketName
                                      , PhotoLocation=os.path.join(DestinationFolder, Picture)
                                      , PhotoMetaData=VideoMetaData
                                      , DebugFlag=DebugFlag)

            # once the picture is processed move it to the processed folder
            shutil.move(os.path.join(DestinationFolder, Picture), os.path.join(FolderPath, Picture))
            print('moving images')
            ReturnCode = 0
    except:
        print('error indexing the picture', IndexMessage)
        ReturnCode = 1

    return ReturnCode


def main():
    # get the video file path
    VideoPath = EG.fileopenbox(msg='Select the video file path', title='Video File',
                               default='C:/Work Files/Tech Forum/Facial Recognition/Train Videos/*')
    # take the metadata and debugflag
    fieldNames = ["Metadata"]
    choices = ["Yes", "No"]
    # Inputs = list(multenterbox(msg='Fill in values for the fields.', title='Information', fields=(fieldNames)))
    Metadata = EG.multenterbox(msg='Enter Metadata to be stored in AWS.', title='Information', fields=(fieldNames))[0]
    DebugFlag = EG.choicebox(msg='Do you want me to print messages?', title='DebugMode', choices=choices)

    # change the debug flag to 1 or 0
    if DebugFlag == 'Yes':
        DebugFlag = 1
    else:
        DebugFlag = 0
    # set the destination folder
    Folder = 'C:\Work Files\Tech Forum\Facial Recognition\Training Pics'

    # create collection
    Collection = CreateCollection(CollectionName=Metadata + '-Collection', DebugFlag=DebugFlag)

    # if there was an error, exit
    if Collection == -1:
        return Collection

    # print(Folder)
    ProcessImages(VideoLocation=VideoPath
                  , VideoMetaData=Metadata
                  , DestinationFolder=Folder
                  , DebugFlag=DebugFlag)


if __name__ == '__main__':
    main()