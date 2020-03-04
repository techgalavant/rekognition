import boto3  # AWS library
import os
from botocore.exceptions import ClientError


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

    # create collection
    Collection = CreateCollection(CollectionName=CollectionName, DebugFlag=DebugFlag)

    # if there was an error, exit
    if Collection == -1:
        return Collection

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

