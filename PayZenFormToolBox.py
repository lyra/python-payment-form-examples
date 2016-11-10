#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" PayZenFormToolBox.py: Define Python2 classes for PayZen VADS simple requesting """

import uuid
import hmac
import base64
from datetime import datetime
import hashlib
import logging
import json


class PayZenFormToolBox:
    """ PayZen VADS Tool Box v0.2 """

    # PayZen platform data container
    platform = {
        'url': 'https://secure.payzen.eu/vads-payment/'
    }

    # Shop platform data container
    shop = {
        'ipn_url': None,
        'return_url': None
    }

    def __init__(self, site_id, cert_test, cert_prod, mode='TEST', logger=None):
        """Constructor, stores the PayZen user's account informations.

        Keyword arguments:
        site_id -- the account site id as provided by Payzen
        cert_test --- certificate, test-version, as provided by PayZen
        cert_prod -- certificate, production-version, as provided by PayZen
        mode -- ("TEST" or "PRODUCTION"), the PayZen mode to operate
        logger --logging.logger object, the logger to use. Will be created if not provided
        """
        self.logger = logger or logging.getLogger()
        self.account = {
            'site_id': site_id,
            'cert': {
                'TEST': cert_test,
                'PRODUCTION': cert_prod
            },
            'mode': mode
        }


    # Getter and setter for ipn_url and return_url properties
    @property
    def ipn_url(self):
	return self.shop['ipn_url']


    @ipn_url.setter
    def ipn_url(self, url):
	self.shop['ipn_url'] = url


    @property
    def return_url(self):
	return self.shop['return_url']


    @return_url.setter
    def return_url(self, url):
	self.shop['return_url'] = url


    def form(self, trans_id, amount, currency):
	""" Utility method, returns the fields and the data mandatory for a simple payment form.

	Keyword arguments:
	trans_id -- the transaction id from user site
	amount -- the amount of the payment
	currency -- the code of the currency to use

	Returns:
	the mandatory fields and data
	"""
	return {
	    "form": {
		"action": self.platform['url'],
		"method": "POST",
		"accept-charset": "UTF-8",
		"enctype": "multipart/form-data"
	    },
	    "fields": self.fields(self.account['site_id'], trans_id, amount, currency)
	}


    def fields(self, site_id, trans_id, amount, currency):
	""" Utility method, returns the mandatory fields for a simple payment form.

	Keyword arguments:
	trans_id -- the transaction id from user site
	amount -- the amount of the payment
	currency -- the code of the currency to use

	Returns:
	the mandatory fields and data
	"""
	fields = {
	    "vads_site_id": site_id,
	    "vads_ctx_mode": self.account['mode'],
	    "vads_trans_id": trans_id,
	    "vads_trans_date": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
	    "vads_amount": amount,
	    "vads_currency": currency,
	    "vads_action_mode": "INTERACTIVE",
	    "vads_page_action": "PAYMENT",
	    "vads_version": "V2",
	    "vads_payment_config": "SINGLE",
	    "vads_capture_delay": "0",
	    "vads_validation_mode": "0"
	}

	if self.ipn_url:
	    fields['vads_url_check'] = self.ipn_url

	if self.return_url:
	    fields['vads_url_return'] = self.return_url

	fields['signature'] = self.sign(fields)
	return fields


    def sign(self, fields):
	""" Utility function, builds and returns the signature string of the data being transmitted to the PayZen platform

	Keyword arguments:
	fields -- dict of data being signed

	Returns:
	the signature
	"""
	data = []
	for key in sorted(fields):
	    data.append(str(fields[key]))
	data.append(self.account['cert'][self.account['mode']])
	return hashlib.sha1('+'.join(data)).hexdigest()


    def ipn_pay(self, fields):
	""" Utility function, process the IPN request for a PAY action

	Keyword arguments:
	fields -- dict, the data received from PayZen platform

	Only 'DEBIT' operations are handled, not the "CREDIT" ones

	Throws:
	Exception if the operation type is not 'DEBIT'
	PayZenPaymentRefused if the payment is refused
	PayZenPaymentInvalidated if the payment is canceled or abandoned
	PayZenPaymentPending if the payment authorisation is delayed
	"""
	if fields['vads_operation_type'] != 'DEBIT':
	    raise Exception("Unhandled operation type " + fields['vads_operation_type'])
	if fields['vads_trans_status'] in ['AUTHORISED', 'CAPTURED']:
	    self.logger.info("IPN - Payment for trans_id {} is authorised!".format(fields['vads_trans_id']))
	    return
	if fields['vads_trans_status'] in ['REFUSED']:
	    raise PayZenPaymentRefused("Payment is not authorised - Given status is " + fields['vads_trans_status'])
	if fields['vads_trans_status'] in ['ABANDONED', 'EXPIRED', 'CANCELED', 'NOT_CREATED']:
	    raise PayZenPaymentInvalidated("Payment is not authorised - Given status is " + fields['vads_trans_status'])
	if fields['vads_trans_status'] in ['AUTHORISED_TO_VALIDATE',
					   'WAITING_AUTHORISATION',
					   'WAITING_AUTHORISATION_TO_VALIDATE',
					   'UNDER_VERIFICATION']:
	    raise PayZenPaymentPending("Payment is not yet authorised - Given status is " + fields['vads_trans_status'])



    def ipn(self, fields):
	""" Utility function, check and process the IPN request

	Only 'DEBIT' operations are handled, not the "CREDIT" ones

	Keyword arguments:
	fields -- dict, the data received from PayZen platform

	Returns:
	a valid Flash response (status string)

	Throws:
	Exception if the data signature is incorrect
	Exception if the action is not 'PAY', 'BATCH_AUTO' or 'BO'
	"""
	self.logger.debug("IPN request with fields: " + json.dumps(fields))
	data = {}
	for key, value in fields.iteritems():
	    if str(key).startswith('vads_'):
		data[key] = value
	self.logger.debug("IPN values retained for signature calculation:" + json.dumps(data))

	signature = self.sign(data)
	if signature != fields['signature']:
	    err = 'Signature mismatch - Payment is not confirmed (received: {} / computed: {})'.format(
		    fields['signature'], signature)
	    self.logger.warning(err)
	    raise Exception(err)

	if fields['vads_url_check_src'] in ['PAY', 'BATCH_AUTO']:
	    return self.ipn_pay(fields)

	if fields['vads_url_check_src'] == 'BO':
	    return 'Hello PayZen BO!'

	raise Exception("IPN action unhandled: " + fields[
	    'vads_url_check_src'])  ############ Custom exceptions aimed to discrimate the payment statuses #################


    class PayZenPaymentRefused(Exception):
	pass


    class PayZenPaymentInvalidated(Exception):
	pass


    class PayZenPaymentPending(Exception):
	pass
