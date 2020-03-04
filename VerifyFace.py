import boto3
from botocore.exceptions import ClientError
import easygui as EG  # to open file dialog
import cv2
import json


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

        # resize the image
        Img = cv2.imread(Image)

        # resize the image
        Img = cv2.resize(Img, (500, 500))

        cv2.imwrite(Image, Img)

        with open(Image, 'rb') as uploadimage:
            print(BucketName, 'BucketName')
            print(S3ObjectName, 'S3ObjectName')

            response = s3_client.upload_fileobj(uploadimage, BucketName, S3ObjectName)

        ReturnCode = 0
    except ClientError as e:
        print(ClientError)

        ReturnCode = e

    return ReturnCode


def VerifyFace(ImageName, CollectionName, BucketName, DebugFlag):
    ReturnCode = ''
    Response = ''
    # if no collection is specified then error out.
    if CollectionName == None:
        ReturnCode = 'No collection name specified'
    else:
        Client = boto3.client('rekognition')
        try:

            Response = Client.search_faces_by_image(
                CollectionId=CollectionName,
                Image={'S3Object': {'Bucket': BucketName, 'Name': ImageName}},
                MaxFaces=1,
                QualityFilter='AUTO'
            )
            ReturnCode = 'Successfully verified image.'
        except ClientError as err:
            print(err)
            ReturnCode = err

        return Response, ReturnCode


def AnnotateImage(PhotoPath, Response, Text):
    '''X--Left
        Y--Top
        W--Width
        H--Height'''

    # convert the json to dict
    ResponseDict = Response

    Height = ResponseDict['SearchedFaceBoundingBox']['Height']
    Width = ResponseDict['SearchedFaceBoundingBox']['Width']
    Top = ResponseDict['SearchedFaceBoundingBox']['Top']
    Left = ResponseDict['SearchedFaceBoundingBox']['Left']

    if len(ResponseDict['FaceMatches']) != 0:
        Text = ResponseDict['FaceMatches'][0]['Similarity']
    else:
        Text = 'No Match Found'

    # open the image
    Img = cv2.imread(PhotoPath)

    # resize the image
    Img = cv2.resize(Img, (500, 500))

    x = (int(Left), int(Top))
    y = (int(Width), int(Height))
    color = (255, 199, 0)
    # create a bounding box
    Img = cv2.rectangle(Img, x, y, color, 2)

    # write the name on the image
    # Img = cv2.putText(Img, Text, (int(Left), int(Top)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
    Img = cv2.putText(Img, str(Text), (1, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    cv2.imshow('rec', Img)
    cv2.waitKey(0)

    cv2.imwrite(PhotoPath, Img)

    return


def main():
    # get the video file path
    PhotoPath = EG.fileopenbox(msg='Select the Phot file path', title='Photo',
                               default='C:/Work Files/Tech Forum/Facial Recognition/Training Pics/*')
    # take the metadata and debugflag
    fieldNames = ["PersonName"]
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

    # Set Collection Name
    CollectionName = Metadata + '-Collection'

    # set the bucket name
    BucketName = 'verificationbucket'

    # upload the file to S3Bucket
    Upload = UploadImages(BucketName=BucketName, Image=PhotoPath, S3ObjectName=Metadata, DebugFlag=DebugFlag)

    # verify the image
    Response, ReturnCode = VerifyFace(ImageName=Metadata
                                      , CollectionName=CollectionName
                                      , BucketName=BucketName
                                      , DebugFlag=DebugFlag)

    print(Response)

    # annotate the image
    AnnotateImage(PhotoPath=PhotoPath, Response=Response, Text=Metadata)

    # show the image
    Img = cv2.imread(PhotoPath)
    cv2.imshow('Verified Image', Img)

    # closes the window when you press any key
    cv2.waitKey(0)


if __name__ == '__main__':
    main()




