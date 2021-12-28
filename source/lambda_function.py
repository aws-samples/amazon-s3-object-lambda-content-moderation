import json
import boto3

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

from io import BytesIO
from PIL import Image
from PIL import ImageFilter

import urllib3
http = urllib3.PoolManager()

from exceptions import CustomException, S3GetException, ExceedingFileSizeException, UnsupportedFormatException
from s3_helper import translate_response_headers_to_writegetobjectresponse, parse_s3_error_response


def blur_image(image_data, file_format):
    img = Image.open(BytesIO(image_data))
    blurred = img.filter(ImageFilter.GaussianBlur(32))
    
    blurred_byte_arr = BytesIO()
    blurred.save(blurred_byte_arr, format=file_format)
    return blurred_byte_arr.getvalue()

def extract_object_context(event):

    object_get_context = event["getObjectContext"]
    request_route = object_get_context["outputRoute"]
    request_token = object_get_context["outputToken"]
    s3_url = object_get_context["inputS3Url"]

    return request_route, request_token, s3_url

def download_image_from_s3(presigned_s3_url):

    REKOGNITION_MAX_FILE_SIZE = 5242880
    response = http.request('GET', presigned_s3_url)

    if response is None:
       raise ValueError('response is empty')
    if response.headers is None:
       raise ValueError('response has no headers')

    if response.status >= 300:

        s3_error_code, s3_error_message = parse_s3_error_response(response.data.decode('utf-8'))

        raise S3GetException( 
            s3_http_code = response.status, 
            s3_error_code = s3_error_code, 
            s3_error_message = "S3 Error: " + s3_error_message
            )
    
    extensions = ['/jpg', '/jpeg', '/png']
    if not any(response.headers['Content-Type'].lower().endswith(ext) for ext in extensions):
        raise UnsupportedFormatException()
    file_format = response.headers['Content-Type'].split('/')[-1]
    
    if int(response.headers['Content-Length']) > REKOGNITION_MAX_FILE_SIZE:
        raise ExceedingFileSizeException()

    # Translate the headers returned from the presigned s3 url request to a format used by 
    # S3 WriteGetObjectResponse.
    headers = translate_response_headers_to_writegetobjectresponse(response.headers)

    return response.data, headers, file_format

def write_s3_get_object_response(status_code,request_route, request_token, image_bytes, headers):

    # Write image object back to S3 get object response
    s3.write_get_object_response(
        StatusCode=status_code,
        Body=image_bytes,
        RequestRoute=request_route,
        RequestToken=request_token,
        **headers
        )

def write_s3_get_object_error(status_code, s3_error_code, error_message, request_route, request_token):

    # Write image object back to S3 get object response
    s3.write_get_object_response(
        StatusCode=status_code,
        ErrorCode=s3_error_code,
        ErrorMessage=error_message,
        RequestRoute=request_route,
        RequestToken=request_token
        )

def lambda_handler(event, context):
                                                                                                                                                                                                                                                                
    try:
        [request_route, request_token, presigned_s3_url] = extract_object_context(event)
        
        # Download the image object from S3 via the presigned url. 
        # This way the object lambda does not need S3 read permissions.
        # (Generally, Rekognition would also accept passing an S3 URL instead of the image bytes)
        [image_bytes, headers, file_format] = download_image_from_s3(presigned_s3_url)
        
        # Detect moderation content in the image with Rekognition
        response = rekognition.detect_moderation_labels(
            Image={
                'Bytes': image_bytes
            },
                MinConfidence=50
            )    

        #Blur the imaege if moderation labels are present
        labels = response['ModerationLabels']    
        if len(labels):
            image_bytes = blur_image(image_bytes, file_format)

            # Update the headers to the new size in bytes of the blurred image (in case it changed)
            headers['ContentLength']=len(image_bytes)

    except Exception as e:
        handle_exception(e, request_route, request_token)    
    else:
        write_s3_get_object_response(200, request_route, request_token, image_bytes, headers)

    # Return lambda gracefully
    return {'statusCode': 200 }


def handle_exception(exception, request_route, request_token):
    try:
        raise exception

    except CustomException as e:
        write_s3_get_object_error(e.status_code, e.s3_error_code, e.error_message, request_route, request_token)

    except Exception as e:
        write_s3_get_object_error(500, 'InternalError', 'An unexpected internal error occured', request_route, request_token)

    
    
    
