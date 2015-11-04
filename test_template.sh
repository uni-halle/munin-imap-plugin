#!/bin/bash

export RECEIVING_USERNAME=username
export RECEIVING_PASSWORD=password
export IMAP_HOST=hostname
export POP3_HOST=hostname

export SENDING_USERNAME=username
export SENDING_PASSWORD=password
export SMTP_HOST=hostname
export SMTP_PORT=portnumber

python check_both.py
# python check_imap4.py
# python check_pop3.py

