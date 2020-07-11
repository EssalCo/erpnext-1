# -*- coding: utf-8 -*-

import frappe


def execute():

    to_be_updated = frappe.db.sql(
        """select parent, fieldname,
	(select issingle from tabDocType dt
	where dt.name = df.parent) as issingle
from tabDocField df
where
	df.options="Account" and df.fieldtype='Link' HAVING issingle = 0 ;""", as_dict=True
    )

    for temp in to_be_updated:

    #     test = frappe.db.sql(
    #         """SELECT CONCAT(TRIM(TRAILING '- نلا' FROM {field}), "- N") as new, {field}  FROM `tab{doctype}`
    # WHERE {field} IS NOT NULL AND {field} LIKE "%- نلا";""".format(
    #             doctype=temp.parent,
    #             field=temp.fieldname
    #         )
    #     )
        # print test
        # continue
        frappe.db.sql(
            """UPDATE `tab{doctype}` SET {field} = CONCAT(TRIM(TRAILING '- N' FROM {field}), "")
    WHERE {field} IS NOT NULL AND {field} LIKE "%- N";""".format(
                doctype=temp.parent,
                field=temp.fieldname
            )
        )
        frappe.db.sql(
            """UPDATE `tabAccount` SET name = CONCAT(TRIM(TRAILING '- N' FROM name), "")
    WHERE name IS NOT NULL AND name LIKE "%- N";"""
        )
        frappe.db.sql(
            """UPDATE `tabGL Entry` SET against = CONCAT(TRIM(TRAILING '- N' FROM against), "")
    WHERE against IS NOT NULL AND against LIKE "%- N";"""
        )