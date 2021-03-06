#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os.path

from flask import current_app, redirect, render_template, request, send_file, url_for
from flask.ext.babel import gettext
from sqlalchemy.orm.exc import NoResultFound

from pokr.cache import cache
from pokr.models.bill import Bill
from pokr.models.election import current_parliament_id
from utils.jinja import breadcrumb


def register(app):

    app.views['bill'] = 'bill_main'
    gettext('bill') # for babel extraction

    @app.route('/bill/', methods=['GET'])
    @breadcrumb(app)
    def bill_main():
        assembly_id = int(request.args.get('assembly_id', current_parliament_id('assembly')) or 0)
        bills = Bill.query.filter(Bill.assembly_id==assembly_id)\
                          .order_by(Bill.proposed_date.desc().nullslast(),
                                    Bill.id.desc())
        return render_template('bills.html',\
                assembly_id=assembly_id, bills=bills)

    @app.route('/bill/<id>', methods=['GET'])
    @breadcrumb(app, 'bill')
    def bill(id):
        try:
            bill = Bill.query.filter_by(id=id).one()

        except NoResultFound, e:
            return render_template('not-found.html'), 404

        return render_template('bill.html', bill=bill)

    @app.route('/bill/<id>/pdf', methods=['GET'])
    def bill_pdf(id):
        try:
            bill = Bill.query.filter_by(id=id).one()

        except NoResultFound, e:
            return render_template('not-found.html'), 404

        if bill.document_pdf_path:
            response = send_file(bill.document_pdf_path)
            response.headers['Content-Disposition'] = 'filename=%s.pdf' % id
            return response
        else:
            return render_template('not-found.html'), 404

    @app.route('/bill/<id>/text', methods=['GET'])
    @breadcrumb(app, 'bill')
    def bill_text(id):
        try:
            bill = Bill.query.filter_by(id=id).one()

        except NoResultFound, e:
            return render_template('not-found.html'), 404

        if bill.document_text_path:
            glossary_js = generate_glossary_js()
            with open(bill.document_text_path) as f:
                response = render_template('bill-text.html', bill=bill, f=f,
                        glossary_js=glossary_js)
            return response
        else:
            return render_template('not-found.html'), 404

    @app.route('/bill/<id>/official', methods=['GET'])
    def bill_official(id):
        try:
            bill = Bill.query.filter_by(id=id).one()

        except NoResultFound, e:
            return render_template('not-found.html'), 404

        return redirect("http://likms.assembly.go.kr/bill/jsp/BillDetail.jsp?bill_id={0}".format(bill.link_id))

@cache.memoize(timeout=60*60*24)
def generate_glossary_js():
    datadir = os.path.join(current_app.root_path, 'data')
    terms_regex = open('%s/glossary-terms.regex' % datadir).read().decode('utf-8').strip()
    dictionary = open('%s/glossary-map.json' % datadir).read().decode('utf-8').strip()
    return render_template('js/glossary.js', terms_regex=terms_regex,
            dictionary=dictionary)

