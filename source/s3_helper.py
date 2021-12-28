# Adopted from https://github.com/aws-samples/amazon-comprehend-s3-object-lambda-functions

import re

def parse_s3_error_response(error_response):
    """
    Extract error code and message from original http response.
    For more details see https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList
    """

    ERROR_RE = r'(?<=<Error>).*(?=<\/Error>)'
    CODE_RE = r'(?<=<Code>).*(?=<\/Code>)'
    MESSAGE_RE = r'(?<=<Message>).*(?=<\/Message>)'
    
    s3_error_code =  "InternalError "
    s3_error_message = "Unknown Error"

    # Remove line breaks and XML header
    xml = ''.join(error_response.split('\n')[1:])

    error_matched = re.search(ERROR_RE, xml)
    code_matched = re.search(CODE_RE, xml)
    message_matched = re.search(MESSAGE_RE, xml)
    
    if code_matched:
        s3_error_code = code_matched[0]
    if message_matched:
        s3_error_message = message_matched[0]

    return s3_error_code, s3_error_message


def translate_response_headers_to_writegetobjectresponse(headers):
    """
    Convert response headers received from s3 presigned download call to the format similar to arguments of WriteGetObjectResponse API.
    :param headers: http headers received as part of response from downloading the object from s3
    """
        
    S3GET_TO_WGOR_HEADER_TRANSLATION_MAP = {
        "accept-ranges": ("AcceptRanges", str),
        "Cache-Control": ("CacheControl", str),
        "Content-Disposition": ("ContentDisposition", str),
        "Content-Encoding": ("ContentEncoding", str),
        "Content-Language": ("ContentLanguage", str),
        "Content-Length": ("ContentLength", int),
        "Content-Range": ("ContentRange", str),
        "Content-Type": ("ContentType", str),
        "x-amz-delete-marker": ("DeleteMarker", bool),
        "ETag": ("ETag", str),
        "Expires": ("Expires", str),
        "x-amz-expiration": ("Expiration", str),
        "Last-Modified": ("LastModified", str),
        "x-amz-missing-meta": ("MissingMeta", str),
        "x-amz-meta-": ("Metadata", str),
        "x-amz-object-lock-mode": ("ObjectLockMode", str),
        "x-amz-object-lock-legal-hold": ("ObjectLockLegalHoldStatus", str),
        "x-amz-object-lock-retain-until-date": ("ObjectLockRetainUntilDate", str),
        "x-amz-mp-parts-count": ("PartsCount", int),
        "x-amz-replication-status": ("ReplicationStatus", str),
        "x-amz-request-charged": ("RequestCharged", str),
        "x-amz-restore": ("Restore", str),
        "x-amz-server-side-encryption": ("ServerSideEncryption", str),
        "x-amz-server-side-encryption-customer-algorithm": ("SSECustomerAlgorithm", str),
        "x-amz-server-side-encryption-aws-kms-key-id": ("SSEKMSKeyId", str),
        "x-amz-server-side-encryption-customer-key-MD5": ("SSECustomerKeyMD5", str),
        "x-amz-storage-class": ("StorageClass", str),
        "x-amz-tagging-count": ("TagCount", int),
        "x-amz-version-id": ("VersionId", str),
    }
        
    transformed_headers = {}
    for header_name in headers:
        if header_name in S3GET_TO_WGOR_HEADER_TRANSLATION_MAP:
            header_value = S3GET_TO_WGOR_HEADER_TRANSLATION_MAP[header_name][1](headers[header_name])
            transformed_headers[S3GET_TO_WGOR_HEADER_TRANSLATION_MAP[header_name][0]] = header_value

    return transformed_headers