# -*- coding: utf-8 -*-

#---
#--- Python
import datetime
import email
import email.header
import re

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
    for headerType, headerValueRaw in list(emailObj.items()) :
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

def iterReceivedHeadLines(emailObj) :
    for headerType, headerValueRaw in list(emailObj.items()) :
        headerValueAndEncoding =  email.header.decode_header(headerValueRaw)
        headerValue = headerValueAndEncoding[0][0]
        headerEncoding = headerValueAndEncoding[0][1]
        if headerType.upper() == 'RECEIVED' :
            yield headerValue

def parseReceivedValue(receivedValue) :
    """
    """
    line = " ".join(l.strip() for l in receivedValue.split('\n')).strip()
    regexp = re.compile("from (?P<from>.+) by (?P<by>.+)( with (?P<with>.+)?)( for (?P<for>.+))?; (?P<atString>.+)")
    m = regexp.match(line)
    receivedDict =m.groupdict()
    atString = receivedDict["atString"]
    try :
        receivedDict["at"] = parseReceivedAt(atString).isoformat()
    except Exception :
        receivedDict["at"] = atString
    return receivedDict


def parseMailDate(dateString) :
    # f = "%a, %d %b %Y %H:%M:%S %z"
    # # Python 2.7.10: ValueError: 'z' is a bad directive
    # in format '%a, %d %b %Y %H:%M:%S %z'
    valueWithoutTZ = " ".join(dateString.split(' ')[:-1])
    f = "%a, %d %b %Y %H:%M:%S"
    return datetime.datetime.strptime(valueWithoutTZ, f)


def parseReceivedAt(dateString) :
    """
    Doctests::

        >>> parseReceivedAt('Mon, 09 Nov 2015 16:08:10 +0100')
        datetime.datetime(2015, 11, 9, 16, 8, 10)
        >>> parseReceivedAt('Mon,  9 Nov 2015 16:08:10 +0100 (CET)')
        datetime.datetime(2015, 11, 9, 16, 8, 10)

    """
    # f = "%a, %d %b %Y %H:%M:%S %z"
    # # Python 2.7.10: ValueError: 'z' is a bad directive
    # in format '%a, %d %b %Y %H:%M:%S %z'
    valueWithoutTZ = dateString[:25]
    f = "%a, %d %b %Y %H:%M:%S"
    return datetime.datetime.strptime(valueWithoutTZ, f)


def getFromAddress(fromField) :
    fromAddressMaybeWithBracket = email.header.decode_header(fromField)[-1][0]
    if fromAddressMaybeWithBracket.startswith('<') :
        fromAddress = fromAddressMaybeWithBracket[1:-1]
    else :
        fromAddress = fromAddressMaybeWithBracket
    return fromAddress


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

if __name__ == "__main__" :
    import doctest
    doctest.testmod()
