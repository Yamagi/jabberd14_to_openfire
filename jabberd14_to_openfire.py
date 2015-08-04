#!/usr/bin/env python

# Copyright (c) 2015 Y. Burmeister <yamagi@yamagi.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
 
# ----

import math
import sys
import time

import pymysql
import xmltodict

# ----

# Database stuff
dbdatabase="databasename"
dbhost="mysql server"
dbpass="mysql password"
dbport=3306
dbuser="mysql user"

# Realm (domain) to migrate
realm="example.com"

# XML file to generate
xmlfile="/path/to/output.xml"

# ----

class User:
    def __init__(self, username):
        self.username = username


    def getMail(self):
        return self.mail


    def getName(self):
        return self.name


    def getPasswd(self):
        return self.passwd


    def getRoster(self):
        return self.roster


    def getUsername(self):
        return self.username


    def setMail(self, mail):
        self.mail = mail


    def setName(self, name):
        self.name = name


    def setPasswd(self, passwd):
        self.passwd = passwd


    def setRoster(self, roster):
        self.roster = roster

# ----

def connecttodb():
    try:
        con = pymysql.connect(host=dbhost, port=dbport, user=dbuser, passwd=dbpass, db=dbdatabase)
    except Exception as e:
        print("Can't connect to db: %s" % (e))
        sys.exit(1)

    return con


def getaccounts(con):
    users = []

    cur = con.cursor()
    cur.execute("SELECT user FROM users WHERE realm='%s'" % realm)

    for r in cur:
        users.append(r[0])

    cur.close()

    return users
 

def getvalue(con, query):
    cur = con.cursor()
    cur.execute(query)

    r = cur.fetchone()[0]
    cur.close()

    return r
 
# ----

# Read accounts
con = connecttodb()
users = []

for account in getaccounts(con):
    user = User(account)

    # General stuff
    user.setPasswd(getvalue(con, "SELECT password FROM users WHERE user='%s' AND realm='%s'" % (account, realm)))
    user.setMail(getvalue(con, "SELECT email FROM vcard WHERE user='%s' AND realm='%s'" % (account, realm)))
    user.setName(getvalue(con, "SELECT name FROM vcard WHERE user='%s' AND realm='%s'" % (account, realm)))


    # The crappy roster
    roster = getvalue(con, "SELECT xml FROM roster WHERE user='%s' AND realm='%s'" % (account, realm))

    contacts = []

    try:
        rcontacts = xmltodict.parse(roster)["query"]["item"]
    except KeyError:
        # Roster's empty, next one please
        continue

    if type(rcontacts) is list:
        # Roster has more than 1 contact
        for rcontact in rcontacts:
            contact = {}
            contact["jid"] = rcontact.get("@jid")
            contact["name"] = rcontact.get("@name")
            contact["group"] = rcontact.get("group")
            contact["subscription"] = rcontact.get("@subscription")
            
            contacts.append(contact)
    else:
        # Roster has only 1 contact
        contact = {}
        contact["jid"] = rcontacts.get("@jid")
        contact["name"] = rcontacts.get("@name")
        contact["group"] = rcontacts.get("group")
        contact["subscription"] = rcontacts.get("@subscription")

        contacts.append(contact)

    user.setRoster(contacts)
    users.append(user)

con.close()


# Write accounts

output = {}
output["Openfire"] = {}
output["Openfire"]["User"] = []

for user in users:
    entry = {}
    entry["Roster"] = {}

    entry["Username"] = user.getUsername()
    entry["Password"] = user.getPasswd()
    entry["Email"] = user.getMail()
    entry["Name"] = user.getName()

    # Jabberd14 didn't save this data -> fake it
    entry["CreationDate"] = str(math.ceil(time.time()))
    entry["ModifiedDate"] = str(math.ceil(time.time()))

    entry["Roster"]["Item"] = []

    for contact in user.getRoster():
        item = {}
        item["@jid"] = contact["jid"]
        
        # Not all contacts have names
        if contact["name"]:
            item["@name"] = contact["name"]

        # Asume that there are no pending subscriptions
        item["@askstatus"] = "-1"
        item["@recvstatus"] = "-1"

        # Translate subscription status
        if contact["subscription"] == "none":
            item["@substatus"] = "0"
        elif contact["subscription"] == "from":
            item["@substatus"] = "1"
        elif contact["subscription"] == "to":
            item["@substatus"] = "2"
        elif contact["subscription"] == "both":
            item["@substatus"] = "3"

        # Not all contacts are in a group
        if contact["group"]:
            item["Group"] = contact["group"]

        entry["Roster"]["Item"].append(item)

    output["Openfire"]["User"].append(entry)

try:
    fd = open(xmlfile, "w")
    fd.write(xmltodict.unparse(output, pretty=True))
    fd.close()
except Exception as e:
    print("Couldn't create output file: %s" % (e))
    sys.exit(1)

