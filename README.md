# PayZen-Python-VADS-payment-example

## Introduction
The code presented here is a demonstration of the implementation of the VADS PayZen payment system, aimed to ease its use and learning.

This demonstration uses Flask micro-framework, please refer to http://flask.pocoo.org/ for installation procedure


## Contents
This code is divided in two files:
* payzen.form.example.py, the main file, entry point of the VADS payment process, defining a minimal [Flask](http://flask.pocoo.org/) application handling the three web pages involved in a PayZen VADS payment: the payment form, the IPN, and the payment return pages
* PayZenFormToolBox.py, the core file, defining an utility class encapsulating all the PayZen logics of this example


## The first use
1. Place the files on the same directory, under the root of your server. This server must be reachable through HTTP by the PayZen servers, via its IP or a domain name
2. In `payzen.form.example.py`, replace the occurences of `[***CHANGE-ME***]` by the actual values of your PayZen account, and by the IPN and return url (typically something like http://my.server:5000/ipn and http://my.server:5000/return)
3. Launch the Flask application with:
> python payzen.form.example.py
By default, the Flask application will listen on port 5000 for incoming HTTP request
4. Access `http://my.server:5000/form_payment` from your browser, and validate-it
5. Follow the PayZen indications to perform the payment


## The next steps
You can follow the on-file documentation in `payzen.form.example.py` to change the properties of the payment you want to initiate, like the amount or the informations of the customer payment card.

You can also change the `TEST` parameter to `PRODUCTION` to switch to _real_ payment mode, with *all* the caution this decision expects.


## Note
* The documentation used to write this code was [Payment form implementation guide](https://payzen.io/en-EN/form-payment/standard-payment/sitemap.html)



