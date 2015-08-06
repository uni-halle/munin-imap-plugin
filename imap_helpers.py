# -*- coding: utf-8 -*-

#---
#--- Python
import email
import email.header
import mail_helpers

#---
def iterMailboxNames(conn) :
    """
    @param conn: The IMAP4-Connection
    @type  conn: imaplib.IMAP4 | imaplib.IMAP4_SSL
    """
    (listCode, listResult) = conn.list() # Unterschied zu IMAP4.lsub ?
    for mbString in listResult :
        if mbString is None :
            continue
        mbParts = mbString.split('"/"')
        mbNameWithQuotes = mbParts[-1].strip()
        firstPartStripped = mbParts[0].strip()
        firstPart = firstPartStripped[1:-1]
        markers = list(m.lower().strip() for m in firstPart.split(' '))
        isQuoted = mbNameWithQuotes.startswith('"') or mbNameWithQuotes.startswith("'")
        if isQuoted :
            mbName = mbNameWithQuotes[1:-1]
        else :
            mbName = mbNameWithQuotes
        yield mbName, markers
        continue



def decodeMailboxName(mbNameEncoded) :
    """
    Replace special characters with corresponding UTF-8 characters:
        - &APY- = german umlaut oe
        - &APw- = german umlaut ue
        - ...
    """
    mbName = mbNameEncoded
    replaceMap = {
        # sorted lexicographically
        "&APY-" : "ö",
        "&APw-" : "ü",
    }
    for fromString, toString in replaceMap.iteritems() :
        mbName = mbName.replace(fromString, toString)
    return mbName.decode('utf-8')



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
        rawMail = mailData[0][1]
        emailObj = email.message_from_string(rawMail)
        yield (sid, emailObj)
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
        rawMail = mailData[0][1]
        emailObj = email.message_from_string(rawMail)
        yield (uid, emailObj)
        break


def iterMailboxDisplayNames(conn) :
    return (decodeMailboxName(mbNameEncoded)
            for mbNameEncoded, markers in iterMailboxNames(conn))

def printMailboxesWithItemCount(conn) :
    """
    List details for all mailboxes
    """
    maxNameLen = max([20] + map(len, iterMailboxDisplayNames(conn)))
    print
    headFormatString = "  %%-%is | #count | marked | SPECIAL-USE | other attributes" % (maxNameLen,)
    lineFormatString="  %%(mbDisplayName)-%is | %%(msgCount)5s  | %%(markerString)6s | %%(specialUse)-11s | %%(attributeString)s " % (maxNameLen,)
    print headFormatString % ("Mailbox",)
    print "  %s-+--------+--------+-%s-+-%s" % ("-"*20,"-"*11,"-"*20)
    for mbNameEncoded, markers in iterMailboxNames(conn) :
        mbDisplayName = decodeMailboxName(mbNameEncoded)
        (Okselect, msgCountList) = conn.select(mbNameEncoded, readonly = True)

        isMarked = '\marked' in markers
        markerString = "MARKED" if isMarked else "  NO  "
        attributeSet = set(markers)
        markerSet = set(['\marked', '\unmarked'])
        for an in markerSet :
            attributeSet.discard(an)

        # RFC6154 SPECIAL-USE
        specialSet = set([
            r'\all',
            r'\archive',
            r'\drafts',
            r'\flagged',
            r'\junk',
            r'\sent',
            r'\trash',
        ])
        folderUsage = specialSet.intersection(markers)
        specialUse = ", ".join(sorted(folderUsage))
        for an in folderUsage :
            attributeSet.discard(an)

        attributeString = ", ".join(("'%s'" % an for an in sorted(attributeSet)))
        msgCount = msgCountList[0]

	if 0 :
	    acl = M.myrights(mbNameEncoded) # works only with ACL

        if 0 :
            quotaRoots = M.getquotaroot(mbNameEncoded) # works only with QUOTA

        if 0 :
            # deaktiviert, da bei gmx.net folgender Fehler kam:
            # imaplib.error: command CHECK illegal in state AUTH,
	    # only allowed in states SELECTED
            (okCheck, checkResultList) = conn.check()
            checkResult = checkResultList[0]
            pass

        print lineFormatString % locals()


def printMailboxesWithLatestMail(conn) :
    """
    Prints all mailboxes with the lates message on top

    Inspired by:
    https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
    """
    for mailbox, markers in iterMailboxNames(conn) :
        (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
	mailboxPretty = decodeMailboxName(mailbox)

        print "%(mailboxPretty)s" % locals()

        #iterMailboxContent = iterMailboxContent_sequentialID
        iterMailboxContent = iterMailboxContent_uniqueID
	prettyMailbox = decodeMailboxName(mailbox)

        for id, emailObj in iterMailboxContent(conn, mailbox) :


            print "UID = %(id)s" % locals()

            #emailTo = emailObj['To']
            #emailFrom = email.utils.parseaddr(emailObj['From'])

	    for headerType, headerTrunc in mail_helpers.iterEmailHeaders(emailObj, truncateAt = 70) :
                if mail_helpers.IsBaseHeader(headerType) :
                    headerDisplay = mail_helpers.RemoveLineBreaks(headerTrunc)
                    print "    %-30s %s" % (headerType, headerDisplay,)

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




def printCapabilities(conn, capabilities) :
    """
    What capabilities does the IMAP server support?
    On http://www.iana.org/assignments/imap-capabilities/imap-capabilities.xhtml
    the following capabilities are listed::

        ACL                     [RFC4314]
        ANNOTATE-EXPERIMENT-1   [RFC5257]
        AUTH=                   [RFC3501]
        BINARY                  [RFC3516]
        CATENATE                [RFC4469]
        CHILDREN                [RFC3348]
        COMPRESS=DEFLATE        [RFC4978]
        CONDSTORE               [RFC7162]
        CONTEXT=SEARCH          [RFC5267]
        CONTEXT=SORT            [RFC5267]
        CONVERT                 [RFC5259]
        CREATE-SPECIAL-USE      [RFC6154] # IMAP LIST Extension for Special-Use Mailboxes
        ENABLE                  [RFC5161]
        ESEARCH                 [RFC4731]
        ESORT                   [RFC5267]
        FILTERS                 [RFC5466]
        I18NLEVEL=1             [RFC5255]
        I18NLEVEL=2             [RFC5255]
        ID                      [RFC2971]
        IDLE                    [RFC2177]
        IMAPSIEVE=              [RFC6785]
        LANGUAGE                [RFC5255]
        LIST
        LIST-EXTENDED           [RFC5258]
        LIST-STATUS             [RFC5819]
        LITERAL+                [RFC2088]
        LOGIN-REFERRALS         [RFC2221]
        LOGINDISABLED           [RFC2595][RFC3501]
        MAILBOX-REFERRALS       [RFC2193]
        METADATA                [RFC5464]
        METADATA-SERVER         [RFC5464]
        MOVE                    [RFC6851]
        MULTIAPPEND             [RFC3502]
        MULTISEARCH             [RFC7377]
        NAMESPACE               [RFC2342]
        NOTIFY                  [RFC5465]
        QRESYNC                 [RFC7162]
        QUOTA                   [RFC2087]
        RIGHTS=                 [RFC4314]
        SASL-IR                 [RFC4959]
        SEARCH=FUZZY            [RFC6203]
        SEARCHRES               [RFC5182]
        SORT                    [RFC5256]
        SORT=DISPLAY            [RFC5957]
        SPECIAL-USE             [RFC6154] # IMAP LIST Extension for Special-Use Mailboxes
        STARTTLS                [RFC2595][RFC3501]
        THREAD                  [RFC5256]
        UIDPLUS                 [RFC4315]
        UNSELECT                [RFC3691]
        URLFETCH=BINARY         [RFC5524]
        URL-PARTIAL             [RFC5550]
        URLAUTH                 [RFC4467]
        UTF8=ACCEPT             [RFC6855]
        UTF8=ALL     (OBSOLETE) [RFC5738][RFC6855]
        UTF8=APPEND  (OBSOLETE) [RFC5738][RFC6855]
        UTF8=ONLY               [RFC6855]
        UTF8=USER    (OBSOLETE) [RFC5738][RFC6855]
        WITHIN                  [RFC5032]

    Other important RFCs are::

        RFC2060  INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1
            obsoletes RFC1730

        RFC3501  INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1
            obsoletes RFC2060
            updated by RFC4466 Collected Extensions to IMAP4 ABNF
            updated by RFC4469 Internet Message Access Protocol (IMAP) CATENATE Extension
            updated by RFC4551 IMAP Extension for Conditional STORE Operation
                               or Quick Flag Changes Resynchronization
            updated by RFC5032 WITHIN Search Extension to the IMAP Protocol
            updated by RFC5182 IMAP Extension for Referencing the Last SEARCH Result
            updated by RFC5738 IMAP Support for UTF-8
            updated by RFC6186 Use of SRV Records for Locating Email Submission/Access Services
            updated by RFC6858 Simplified POP and IMAP Downgrading for Internationalized Email

        RFC2222 Simple Authentication and Security Layer (SASL)



    @param capabilites: contains the CAPABILITIES of the IMAP server
    @type  capabilites: tuple of str
    """

    #print "  namespace: %r" % M.namespace()

    # Some methods from the Python library 'imaplib' will only work
    # if the server does support the specific capabilities.
    capabilitiesOfInterest = set(capabilities)
    capabilitiesOfInterest.add('ACL') # e.g. Cyrus Server
    capabilitiesOfInterest.add('ANNOTATIONS') # non-standard, but supported by Cyrus Server
    capabilitiesOfInterest.add('CHILDREN') # /Noinferiors
    capabilitiesOfInterest.add('IDLE') # Push-Notification
    capabilitiesOfInterest.add('QUOTA')
    capabilitiesOfInterest.add('SPECIAL-USE') # Auszeichnugn von Junk, Trash etc.
    capabilitiesOfInterest.add('AUTH=CRAM-MD5')
    capabilitiesOfInterest.add('NAMESPACE')

    # Novel Groupwiese
    # https://www.novell.com/documentation/groupwise_sdk/gwsdk_gwimap/data/al7te9j.html
    capabilitiesOfInterest.add('XGWEXTENSIONS')

    print
    print "  %-29s | supported " % ("Capabilities",)
    print "  %s-+-----------" % ("-"*29,)

    for capName in sorted(capabilitiesOfInterest) :
        supported = capName in capabilities
        print "  %-29s | %s" % (capName, "%s" % ('SUPPORTED' if supported else 'NO'))

#    for xcapName in sorted(capabilitiesOfInterest) :
#        if xcapName.startswith('X') :
#            print
#            print xcapName
#            print conn.xatom(xcapName)
