class CustomException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.status_code = 500
        self.s3_error_code = 'InternalError'
        self.error_message = 'Unknown internal error'

class UnsupportedFormatException(CustomException):
    """ Amazon Rekognition supports only the following image formats: jpg, jpeg, png """
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.status_code = 400
        self.s3_error_code = 'UnexpectedContent'
        self.error_message = "Formats other than jpg, jpeg, and png are not supported"


class S3GetException(CustomException):
    """ Errors trying to retrieve the object from S3 """
    def __init__(self, s3_http_code, s3_error_code, s3_error_message, *args, **kwargs):
        super().__init__(*args)
        self.status_code = s3_http_code
        self.s3_error_code = s3_error_code 
        self.error_message = s3_error_message


class ExceedingFileSizeException(CustomException):
    """ Amazon Rekognition does not support images more than 5MB in this implementation. Use images stored on Amazon S3. 
    See here: https://docs.aws.amazon.com/rekognition/latest/dg/limits.html """
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.status_code = 400
        self.s3_error_code = 'EntityTooLarge'
        self.error_message = 'Images larger than 5MB are not supported'

    