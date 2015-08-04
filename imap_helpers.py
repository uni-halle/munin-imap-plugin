# -*- Coding: utf-8 -*-

#---
#--- Python
import email
import email.header

#---
def iterMailboxNames(conn) :
    """
    @param conn: The IMAP4-Connection
    @type  conn: imaplib.IMAP4 | imaplib.IMAP4_SSL
    """
    (listCode, listResult) = conn.list() # Unterschied zu IMAP4.lsub ?
    for mbString in listResult :
        mbParts = mbString.split('"/"')
        mbNameWithQuotes = mbParts[-1].strip()
        firstPart = mbParts[0].strip()[1:-1]
        markers = list(m.lower().strip() for m in firstPart.split(' '))
        if mbNameWithQuotes.startswith('"') or mbNameWithQuotes.startswith("'") :
            mbName = mbNameWithQuotes[1:-1]
        else :
            mbName = mbNameWithQuotes
        yield mbName, markers



def iterMailboxContent_sequentialID(conn, mbName) :
    """
    @precondition: Mailbox must be SELECTED
    @return: generator[(id, rawMail)]
    """
    # Sequential IDs (SID)
    sidResult, sidData = conn.search(None, "ALL") # returns sequential id
    sid_string = sidData[0]
    sid_list = sid_string.split() # separated by SPACE

    for sid in reversed(sid_list) :
        mailResult, mailData = conn.fetch(sid, "(RFC822)") # feth the body
        sid_raw_email = mailData[0][1]
        yield (sid, raw_email)
        break



def iterMailboxContent_uniqueID(conn, mbName) :
    """
    @precondition: Mailbox must be SELECTED
    @return: generator[(id, rawMail)]
    """
    # Unique IDs (UID)
    uidResult, uidData = conn.uid('search', None, "ALL")
    uid_list = uidData[0].split()
    for uid in reversed(uid_list) :
        mailResult, mailData = conn.uid('fetch', uid, '(RFC822)')
        raw_email = mailData[0][1]
        yield (uid, raw_email)
        break




def printMailboxesWithItemCount(conn) :
    """
    List details for all mailboxes
    """
    print
    print "  %-20s | #count | marked | other attributes" % ("Mailbox",)
    print "  %s-+--------+--------+-%s" % ("-"*20,"-"*20)
    for mailbox, markers in iterMailboxNames(conn) :
        (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
        isMarked = '\marked' in markers
        attributeSet = set(markers)
        attributeSet.discard('\marked')
        attributeSet.discard('\unmarked')
        markerString = "MARKED" if isMarked else "  NO  "
        attributeString = ", ".join(sorted(attributeSet))
        msgCount = msgCountList[0]

        if 0 :
            acl = M.myrights(mailbox) # works only with ACL

        if 0 :
            quotaRoots = M.getquotaroot(mailbox) # works only with QUOTA

        if 0 :
            (okCheck, checkResultList) = conn.check()
            checkResult = checkResultList[0]

        print "  %(mailbox)-20s | %(msgCount)5s  | %(markerString)6s | %(attributeString)s " % locals()

def printMailboxesWithLatestMail(conn) :
    """
    Prints all mailboxes with the lates message on top

    Inspired by:
    https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
    """
    for mailbox, markers in iterMailboxNames(conn) :
        (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
        print "%(mailbox)s" % locals()
        #iterMailboxContent = iterMailboxContent_sequentialID
        iterMailboxContent = iterMailboxContent_uniqueID

        for id, rawMail in iterMailboxContent(conn, mailbox) :
            email_message = email.message_from_string(rawMail)
            print "UID = %(id)s" % locals()
            emailTo =email_message['To']
            emailFrom = email.utils.parseaddr(email_message['From'])
            #print "To = %s" % (emailTo,)
            #print "From = %s" % (emailFrom,)
            for headerType, headerValueRaw in email_message.items() :
                headerValueAndEncoding =  email.header.decode_header(headerValueRaw)
                headerValue = headerValueAndEncoding[0][0]
                headerEncoding = headerValueAndEncoding[0][1]
                MAX_HEADER_LENGTH = 110
                if len(headerValue) > MAX_HEADER_LENGTH :
                    headerTrunc = headerValue[:MAX_HEADER_LENGTH-3] + '...'
                else :
                    headerTrunc = headerValue
                print "    %-20s %s" % (headerType, headerTrunc,)

            if 0 :
                # note that if you want to get text content (body) and the email contains
                # multiple payloads (plaintext/ html), you must parse each message separately.
                # use something like the following: (taken from a stackoverflow post)
                def get_first_text_block(self, email_message_instance):
                    maintype = email_message_instance.get_content_maintype()
                    if maintype == 'multipart':
                        for part in email_message_instance.get_payload():
                            if part.get_content_maintype() == 'text':
                                return part.get_payload()
                    elif maintype == 'text':
                        return email_message_instance.get_payload()

            print
        print


