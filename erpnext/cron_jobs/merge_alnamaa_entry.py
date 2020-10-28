# -*- coding: utf-8 -*-

import frappe

def execute():

    journal_entry_id = "ANAM0000001"

    others = ["ANAM0000954", "ANAM0000955", "ANAM0000956"]

    journal_entry_doc = frappe.get_doc(
        "Journal Entry",
        journal_entry_id
    )

    for entry_id in others:
        entry_doc = frappe.get_doc(
            "Journal Entry",
            entry_id
        )

        for acc_entry in entry_doc.accounts:
            journal_entry_doc.append("accounts", dict(
                account=acc_entry.account,
                party_type=acc_entry.party_type,
                party=acc_entry.party,
                exchange_rate=acc_entry.exchange_rate,
                debit_in_account_currency=acc_entry.debit_in_account_currency,
                debit=acc_entry.debit,
                credit_in_account_currency=acc_entry.credit_in_account_currency,
                credit=acc_entry.credit,
                project=acc_entry.project,
                is_advance=acc_entry.is_advance,
                against_account=acc_entry.against_account,
                cost_center=acc_entry.cost_center,
                journal_note=acc_entry.journal_note,
                customer_group=acc_entry.customer_group,
                title=acc_entry.title
            ))

    journal_entry_doc.save()
    frappe.db.commit()
