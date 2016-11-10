#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" PayZen VADS payment Python2 example as a Flask application

Depends:
Flask 0.10.1
http://flask.pocoo.org/
"""

from flask import render_template
from flask import Flask
from flask import request

from PayZenFormToolBox import *
import calendar
import time
import logging

# All log go to local file ./payzen_form.log
logging.basicConfig(filename="payzen_form.log", level=logging.INFO)

logger = logging.getLogger()

payzen = Flask(__name__)

payzenTB = PayZenFormToolBox(
        '[***CHANGE-ME***]',  # shopId
        '[***CHANGE-ME***]',  # certificate, TEST-version
        '[***CHANGE-ME***]',  # certificate, PRODUCTION-version
        'TEST',               # TEST-mode toggle
        logger                # logger object the toolbox must use
)

# IPN url optionnal configuration
ipn_url = '[***CHANGE-ME***]'
payzenTB.ipn_url = ipn_url  # Oerrides the IPN url configured in the PayZen back-office

# Return url optionnal configuration
return_url = '[***CHANGE-ME***]'
payzenTB.return_url = return_url  # Overrides the return url configured in the PayZen back-office


######### URL for the form generation ###########
@payzen.route('/form_payment', methods=['GET'])
def form_payment():
    ## Payment data
    amount = 1000  # payment amount - Change-it to reflect your needs
    currency = 978  # payment currency code - Change-it to reflect your needs
    trans_id = str(calendar.timegm(time.gmtime()))[
               -6:]  # a daily-unique transaction id - Change-it to reflect your needs

    form = payzenTB.form(trans_id, amount, currency)

    return render_template('./form_payment.html', form=form)


######### IPN URL called by PayZen platform #########
@payzen.route('/ipn', methods=['POST'])
def form_ipn():
    try:
        data = request.form
        response = payzenTB.ipn(data)
        # No exception, the payment is valid and authorised
        # here the code for an accepted payment
        logger.info("Payment with trans_id {} is accepted, time to validate the order ".format(data['vads_trans_id']))
        return 'Notification processed!'

    except PayZenPaymentRefused:
        # here the code for a refused payment
        logger.info("Payment with trans_id {} is refused, time to close the order ".format(data['vads_trans_id']))
        return 'Notification processed!'

    except PayZenPaymentInvalidated:
        # here the code for a invalidated payment
        # ie when a customer cancels it
        logger.info("Payment with trans_id {} is invalidated, time to close the order ".format(data['vads_trans_id']))
        return 'Notification processed!'

    except PayZenPaymentPending:
        # here the code for a payment not yet validated
        # could be to mark the corresponding order to 'pending' status
        logger.info("Payment with trans_id {} is in pending zone, time to mark the order as 'pending'".format(
                data['vads_trans_id']))
        return 'Notification processed!'


######### URL for the 'return from payment' page ###########
@payzen.route('/return', methods=['GET'])
def return_from_payment():
    return "Welcome back, dear Customer!"


if __name__ == '__main__':
    payzen.debug = True
    payzen.run(host='0.0.0.0')
