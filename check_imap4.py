#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
#
# Copyright (C) 2005 Bertera Pietro <pietro@bertera.it>
# Copyright (C) 2012 Bernhard Schmidt <berni@birkenwald.de>
# Copyright (C) 2015 David Lukas Müller <david-lukas.mueller@itz.uni-halle.de>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.
# 

import sys
import os
import imaplib
import getopt
import time

#---
#--- Nagios Constants (https://nagios-plugins.org/doc/guidelines.html)

#: The plugin was able to check the service and it appeared to be
#: functioning properly
NAGIOS_RC_OK = 0 

#: The plugin was able to check the service, but it appeared to be above
#: some "warning" threshold or did not appear to be working properly
NAGIOS_RC_WARNING = 1 

#: The plugin detected that either the service was not running or it was
#: above some "critical" threshold
NAGIOS_RC_CRITICAL = 2

#: Invalid command line arguments were supplied to the plugin or low-level
#: failures internal to the plugin (such as unable to fork, or open a tcp
#: socket) that prevent it from performing the specified operation.
#: Higher-level errors (such as name resolution errors, socket timeouts, etc)
#: are outside of the control of plugins and should generally NOT be reported
#: as UNKNOWN states.
NAGIOS_RC_UNKNOWN = 3

#---
#--- Munin Constants

#---
def usage():
    print "-u <user>"
    print "-p <password>"
    print "-s use SSL"
    print "-H <host>"

    
def iterMailboxNames(conn) :
    """
    @param conn: The IMAP4-Connection 
    @type  conn: imaplib.IMAP4 | imaplib.IMAP4_SSL
    """
    (listCode, listResult) = conn.list() # Unterschied zu IMAP4.lsub ?
    for mbString in listResult :
        mbParts = mbString.split('"/"')
        mbNameWithQuotes = mbParts[-1].strip()
        mbName = mbNameWithQuotes[1:-1]
        yield mbName
        continue

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:sH:")
    except getopt.GetoptError:
        usage()
        return NAGIOS_RC_UNKNOWN
    
    user = host = password = use_ssl = None
    
    for o, a in opts:
        if o == "-u":
            user = a
        elif o == "-p":
            password = a
        elif o == "-s":
            use_ssl = True
        elif o == "-H":
            host = a  
    if user == None or password == None or host == None:
        usage()
        return NAGIOS_RC_WARNING

    timepreconnect = time.time()
    
    try:
        if use_ssl:
            M = imaplib.IMAP4_SSL(host=host)
        else:
            M = imaplib.IMAP4(host)
    except Exception, e:
        print "CRITICAL: Could not connect to %s: %s" % (host, e)
        return NAGIOS_RC_CRITICAL
    
    timeprelogin = time.time()
    
    try:        
        M.login(user, password)
    except Exception, e:
        print "CRITICAL: IMAP Login not Successful: %s" % e
        return NAGIOS_RC_CRITICAL
    
    timepostlogin = time.time()
    connectdelay = (timeprelogin-timepreconnect)*1000
    logindelay = (timepostlogin-timeprelogin)*1000

    capabilities = M.capabilities
    
    print "OK IMAP Login Successful"
    print "  Connect:  %(connectdelay).2fms" % locals()
    print "  Login:    %(logindelay).2fms" % locals()

    #print "  namespace: %r" % M.namespace()
     
    # What capabilities does the IMAP server support?
    # http://www.iana.org/assignments/imap-capabilities/imap-capabilities.xhtml
    # ACL                       [RFC4314]
    # ANNOTATE-EXPERIMENT-1     [RFC5257]
    # AUTH= 	                [RFC3501]
    # BINARY 	                [RFC3516]
    # CATENATE 	                [RFC4469]
    # CHILDREN 	                [RFC3348]
    # COMPRESS=DEFLATE 	        [RFC4978]
    # CONDSTORE 	        [RFC7162]
    # CONTEXT=SEARCH 	        [RFC5267]
    # CONTEXT=SORT 	        [RFC5267]
    # CONVERT 	                [RFC5259]
    # CREATE-SPECIAL-USE 	[RFC6154]
    # ENABLE 	                [RFC5161]
    # ESEARCH 	                [RFC4731]
    # ESORT 	                [RFC5267]
    # FILTERS 	                [RFC5466]
    # I18NLEVEL=1 	        [RFC5255]
    # I18NLEVEL=2 	        [RFC5255]
    # ID 	                [RFC2971]
    # IDLE 	                [RFC2177]
    # IMAPSIEVE= 	        [RFC6785]
    # LANGUAGE 	                [RFC5255]
    # LIST-EXTENDED 	        [RFC5258]
    # LIST-STATUS 	        [RFC5819]
    # LITERAL+ 	                [RFC2088]
    # LOGIN-REFERRALS 	        [RFC2221]
    # LOGINDISABLED 	        [RFC2595][RFC3501]
    # MAILBOX-REFERRALS 	[RFC2193]
    # METADATA 	                [RFC5464]
    # METADATA-SERVER 	        [RFC5464]
    # MOVE 	                [RFC6851]
    # MULTIAPPEND 	        [RFC3502]
    # MULTISEARCH 	        [RFC7377]
    # NAMESPACE 	        [RFC2342]
    # NOTIFY 	                [RFC5465]
    # QRESYNC 	                [RFC7162]
    # QUOTA 	                [RFC2087]
    # RIGHTS= 	                [RFC4314]
    # SASL-IR 	                [RFC4959]
    # SEARCH=FUZZY 	        [RFC6203]
    # SEARCHRES 	        [RFC5182]
    # SORT 	                [RFC5256]
    # SORT=DISPLAY 	        [RFC5957]
    # SPECIAL-USE 	        [RFC6154]
    # STARTTLS 	                [RFC2595][RFC3501]
    # THREAD 	                [RFC5256]
    # UIDPLUS 	                [RFC4315]
    # UNSELECT 	                [RFC3691]
    # URLFETCH=BINARY 	        [RFC5524]
    # URL-PARTIAL 	        [RFC5550]
    # URLAUTH 	                [RFC4467]
    # UTF8=ACCEPT 	        [RFC6855]
    # UTF8=ALL      (OBSOLETE) 	[RFC5738][RFC6855]
    # UTF8=APPEND   (OBSOLETE) 	[RFC5738][RFC6855]
    # UTF8=ONLY 	        [RFC6855]
    # UTF8=USER     (OBSOLETE) 	[RFC5738][RFC6855]
    # WITHIN 	                [RFC5032]

    # Some methods from the Python library 'imaplib' will only work
    # if the server does support the specific capabilities.
    capabilitiesOfInterest = set(capabilities)
    capabilitiesOfInterest.add('ACL') # e.g. Cyrus Server
    capabilitiesOfInterest.add('QUOTA')
    capabilitiesOfInterest.add('AUTH=CRAM-MD5')
    capabilitiesOfInterest.add('NAMESPACE')
    
    print
    print "  %-20s | present " % ("Capabilities",)
    print "  %s-+--------" % ("-"*20,)
    
    for capName in sorted(capabilitiesOfInterest) :
        supported = capName in capabilities
        print "  %-20s | %s  " % (capName, "  %s  " % ('X' if supported else ' '))
        

    # List details for all mailboxes
    print
    print "  %-20s | #count " % ("Mailbox",)
    print "  %s-+--------" % ("-"*20,)
    for mailbox in iterMailboxNames(M) :
        (okSelect, msgCountList) = M.select(mailbox, readonly = True)
        msgCount = msgCountList[0]
        #acl = M.myrights(mailbox) # works only with ACL
        #quotaRoots = M.getquotaroot(mailbox) # works only with QUOTA
        (okCheck, checkResultList) = M.check()
        checkResult = checkResultList[0]
        print "  %(mailbox)-20s | %(msgCount)5s  " % locals()
      
    
    M.logout()
    return NAGIOS_RC_OK

if __name__ == "__main__":
    sys.exit(main())

