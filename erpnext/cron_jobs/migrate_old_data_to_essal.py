# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys

import frappe

sys.path.append('../..')
import csv
from frappe.utils.file_manager import get_file_path
from datetime import datetime
from umalqurra.hijri_date import HijriDate


def execute():
    journal_file = "/private/files/journal_entry.csv"
    cost_centers = "/private/files/cost_centers.csv"
    accounts_tree = "/private/files/accounts_tree.csv"
    year = "1439"
    try:
        company = frappe.get_doc(
            dict(
                doctype="Company",
                company_name="Alnama1439",
                abbr="A39",
                default_currency="SAR",
                country="Saudi Arabia"
            )
        ).insert(ignore_permissions=True)
    except Exception as e:
        print str(e)
        company = frappe.get_doc(
            "Company",
            dict(
                company_name="Alnama1439"
            )
        )
    current_file = get_file_path(cost_centers)
    current_file = current_file.replace("s1.essal.co", "alnamaa.s1.essal.co")
    print("Starting Cost Centers..")

    with open(current_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=str(","), quotechar=str("|"))
        for row in spamreader:
            try:
                serial_no = int(row[0])
            except:
                continue
            cost_center_name = row[1].decode('utf-8')
            parent_cost_center = row[6].decode('utf-8')
            children_units = row[4]

            doc = frappe.get_doc(
                dict(
                    doctype="Cost Center",
                    cost_center_name=cost_center_name,
                    parent_cost_center=parent_cost_center,
                    company=company.name,
                    is_group=int(children_units) > 0
                )
            )
            doc.flags.ignore_mandatory = True
            doc.insert(ignore_permissions=True)

            print cost_center_name
    frappe.db.commit()

    print("Done Cost Centers")
    print ("****************")
    print("Starting Accounts..")

    current_file = get_file_path(accounts_tree)
    current_file = current_file.replace("s1.essal.co", "alnamaa.s1.essal.co")

    with open(current_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=str(","), quotechar=str("|"))
        for row in spamreader:
            try:
                serial_no = int(row[0])
            except:
                continue
            account_name = row[1].decode('utf-8')
            account_type = row[2].decode('utf-8')
            children_units = row[12]
            parent_account = row[14].decode('utf-8')
            doc = frappe.get_doc(
                dict(
                    doctype="Account",
                    account_name=account_name,
                    account_number=None,
                    account_serial=serial_no,
                    company=company.name,
                    is_group=int(children_units) > 0,
                    account_currency="SAR",
                    parent_account=frappe.get_value(
                        "Account",
                        dict(
                            account_name="{0} - {1}".format(company.abbr, parent_account)
                        ),
                        "name"
                    ),
                    report_type="Balance Sheet",
                    root_type="Expense"
                )
            )
            doc.flags.ignore_mandatory = True
            doc.insert(ignore_permissions=True)
            frappe.db.set_value(
                "Account",
                doc.name,
                "account_serial",
                serial_no
            )
        print account_name
    print("Done Accounts.")

    print ("****************")
    print("Starting Journal Entries..")
    current_file = get_file_path(journal_file)
    current_file = current_file.replace("s1.essal.co", "alnamaa.s1.essal.co")

    with open(current_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=str(","), quotechar=str("|"))
        current_entry_index, total_credit, total_debit = 0, 0, 0
        journal_entry = None
        for row in spamreader:
            try:
                serial_no = int(row[0])
            except:
                continue
            if not serial_no:
                continue
            journal_date = str(row[1].decode('utf-8')).split("/")
            day = int(journal_date[2].replace(" ", ""))
            month = int(journal_date[1].replace(" ", ""))
            year = int(journal_date[0].replace(" ", ""))
            journal_date = HijriDate(year, month, day, gr=False)
            journal_date = "{:04d}-{:02d}-{:02d}".format(journal_date.year_gr, journal_date.month_gr, journal_date.day_gr)
            if serial_no != current_entry_index:
                if journal_entry:
                    journal_entry.total_debit = abs(total_debit)
                    journal_entry.total_credit = abs(total_credit)
                    journal_entry.difference = abs(total_debit - total_credit)
                    journal_entry.insert(ignore_permissions=True)

                    journal_entry = frappe.get_doc(
                        dict(
                            doctype="Journal Entry",
                            title="القيد رقم ({0}) سنة".format(serial_no, year),
                            voucher_type="Journal Entry",
                            naming_series="JV-",
                            posting_date=journal_date,
                            company=company.name,
                            user_remark="القيد رقم ({0}) سنة".format(serial_no, year),
                            multi_currency=0,
                            remark="القيد رقم ({0}) سنة".format(serial_no, year),
                            bill_date=datetime.now(),
                            is_opening="No",
                            third_party_creation=journal_date,
                            accounts=[]
                        )
                    )
                    current_entry_index = serial_no

            account_name = row[2].decode('utf-8')
            account_name = account_name[account_name.index("[") + 1:account_name.index("]")]
            account_name = frappe.get_value("Account",
                                            dict(
                                                company=company.name,
                                                account_serial=account_name
                                            ),
                                            "name")
            debit = row[3]
            credit = row[4]
            description = row[7].decode('utf-8')

            if credit:
                total_credit += credit
                journal_entry.append("accounts", dict(
                    account=account_name,
                    party_type=None,
                    party=None,
                    title=description,
                    exchange_rate=1,
                    debit_in_account_currency=0,
                    debit=0,
                    journal_note=description,
                    credit_in_account_currency=abs(credit),
                    credit=abs(credit),
                    is_advance="No",
                    cost_center=None
                ))
            else:
                total_debit += debit
                journal_entry.append("accounts", dict(
                    party_type=None,
                    party=None,
                    account=account_name,
                    exchange_rate=1,
                    title=description,
                    debit_in_account_currency=abs(debit),
                    debit=abs(debit),
                    credit_in_account_currency=0,
                    credit=0,
                    project=None,
                    journal_note=description,
                    is_advance="No",
                    cost_center=None
                ))

    print("Done Accounts.")