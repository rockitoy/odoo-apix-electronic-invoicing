# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from hashlib import sha256
import requests
from datetime import timezone, datetime
import json
import base64
from xml.dom.minidom import parseString
import xml.dom.minidom


class ResCompany(models.Model):
    _inherit = 'res.company'

    apix_userid = fields.Char(string="User Id")
    apix_pwd = fields.Char(string="Password")
    apix_enviroment = fields.Selection([('test', 'Test'), ('prod', 'Production')], string="Enviroment", default='test')
    apix_transfer_id = fields.Char(string="Transfer Id")
    apix_transfer_key = fields.Char(string="Transfer Key")
    unique_comp_id = fields.Char(string="Unique Company ID")

    def retrieve_transfer_key(self):
        if not self.apix_userid or not self.apix_pwd:
            raise UserError(_("Please enter the APIX UserID and Password"))
        pw_digest = sha256(self.apix_pwd.encode('utf-8')).hexdigest()
        timestamp = datetime.strftime(datetime.utcnow(), "%Y%m%d%H%M%S")
        digest = sha256((self.company_registry+"+"+"y-tunnus"+"+"+self.apix_userid+"+"+timestamp+"+"+pw_digest).encode('utf-8')).hexdigest()
        if self.apix_enviroment == 'test':
            response = requests.get('https://test-api.apix.fi/app-transferID?id=%s&idq=%s&uid=%s&ts=%s&d=SHA-256:%s' % (self.company_registry, "y-tunnus", self.apix_userid,timestamp,digest ), headers={'Authorization': "SHA-256:" + digest})
            res = response.content
        else:
            response = requests.get(' https://api.apix.fi/app-transferID?id=%s&idq=%s&uid=%s&ts=%s&d=SHA-256:%s' % (self.company_registry, "y-tunnus", self.apix_userid,timestamp,digest ), headers={'Authorization': "SHA-256:" + digest})
            res = response.content
        res = res.decode('utf-8')
        DOMTree = xml.dom.minidom.parseString(res)
        collection = DOMTree.documentElement
        values = collection.getElementsByTagName('Value')
        for val in values:
            if val.getAttribute("type") == "TransferKey":
                self.apix_transfer_key = val.childNodes[0].data
            if val.getAttribute("type") == "TransferID":
                self.apix_transfer_id = val.childNodes[0].data
            if val.getAttribute("type") == "UniqueCompanyID":
                self.unique_comp_id = val.childNodes[0].data



