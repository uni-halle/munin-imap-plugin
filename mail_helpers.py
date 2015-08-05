# -*- coding: utf-8 -*-

#---
#--- Python
import email
import email.header


#---
def iterEmailHeaders(emailObj, **keywords) :
    """
    @type emailObj: email.

    @keyword truncateAt: When greater than len(ellipsis), limits output accordingly.
        Truncated values are indicated by trailing ellipsis (e.g. '...')
    @type    truncateAt: int

    @keyword ellipsis: default is '...'
    @type    ellipsis: str
    """
    truncateAt = keywords.get('truncateAt', 0)
    ELLIPSIS = keywords.get('ellipsis', "...")
    ELLIPSIS_LEN  = len(ELLIPSIS)
    for headerType, headerValueRaw in emailObj.items() :
        headerValueAndEncoding =  email.header.decode_header(headerValueRaw)
        headerValue = headerValueAndEncoding[0][0]
        headerEncoding = headerValueAndEncoding[0][1]
        MAX_HEADER_LENGTH = truncateAt
        if truncateAt > ELLIPSIS_LEN :
            if len(headerValue) > MAX_HEADER_LENGTH :
                headerTrunc = headerValue[:MAX_HEADER_LENGTH-ELLIPSIS_LEN] + ELLIPSIS
            else :
                headerTrunc = headerValue
        else :
            headerTrunc = headerValue


        yield (headerType, headerTrunc)


def IsBaseHeader(headerType) :
    """
    Returns True if non of the following conditions evaluate to True:
        - headerType.startswith('DKIM-')
        - headerType.startswith('X-')
    @rtype: bool
    """
    if headerType.startswith('DKIM-') :
        return False
    if headerType.startswith('X-') :
        return False
    return True

def RemoveLineBreaks(headerTrunc) :
    return headerTrunc.replace('\n', ' ').replace('\r', ' ').replace('  ', ' ')
