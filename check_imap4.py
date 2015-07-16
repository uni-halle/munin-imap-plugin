#!/usr/bin/python
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
#
# Copyright (C) 2005 Bertera Pietro <pietro@bertera.it>
# Copyright (C) 2012 Bernhard Schmidt <berni@birkenwald.de>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.
# 
# Version 20121106

import sys, os, imaplib, getopt, time

def usage():
    print "-u <user>"
    print "-p <password>"
    print "-s use SSL"
    print "-H <host>"

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:sH:")
    except getopt.GetoptError:
        usage()
        return 3
    
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
        return 1

    timepreconnect = time.time()
    
    try:
        if use_ssl:
            M = imaplib.IMAP4_SSL(host=host)
        else:
            M = imaplib.IMAP4(host)
    except Exception, e:
        print "CRITICAL: Could not connect to %s: %s" % (host, e)
        return 2
    
    timeprelogin = time.time()
    
    try:	
        M.login(user, password)
    except Exception, e:
        print "CRITICAL: IMAP Login not Successful: %s" % e
        return 2
    
    timepostlogin = time.time()

    connectdelay = (timeprelogin-timepreconnect)*1000
    logindelay = (timepostlogin-timeprelogin)*1000

    M.logout()
    print "OK IMAP Login Successful (Connect: %.2fms, Login: %.2fms) | connect=%.2fms login=%.2fms" % ( 
        connectdelay, logindelay,
        connectdelay, logindelay )
    return 0

if __name__ == "__main__":
    sys.exit(main())

