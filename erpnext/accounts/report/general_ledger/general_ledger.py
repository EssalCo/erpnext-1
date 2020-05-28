# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

from six import iteritems

import frappe
from erpnext import get_company_currency, get_default_company
# from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
# from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from erpnext.accounts.utils import get_account_currency
from frappe import _, _dict
from frappe.utils import getdate, cstr, flt

from erpnext.utilities.send_telegram import send_msg_telegram


@frappe.whitelist()
def execute(filters=None):
    if not filters:
        return [], []

    account_details = {}

    if filters and filters.get('print_in_account_currency') and \
            not filters.get('account'):
        frappe.throw(_("Select an account to print in account currency"))

    for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
        account_details.setdefault(acc.name, acc)

    if filters.get('party'):
        filters.party = filters.get("party")

    validate_filters(filters, account_details)

    validate_party(filters)

    filters = set_account_currency(filters)

    columns = get_columns(filters)

    res = get_result(filters, account_details)

    return columns, res


def parse_json(val):
    """
    Parses json if string else return
    """
    import json

    if isinstance(val, (str, unicode, basestring)):
        val = json.loads(val)
    if isinstance(val, dict):
        val = frappe._dict(val)
    return val


def validate_filters(filters, account_details):
    if not filters.get('company'):
        frappe.throw(_('{0} is mandatory').format(_('Company')))

    if filters.get("account") and not account_details.get(filters.account):
        frappe.throw(_("Account {0} does not exists").format(filters.account))

    if (filters.get("account") and filters.get("group_by") == _('Group by Account')
            and account_details[filters.account].is_group == 0):
        frappe.throw(_("Can not filter based on Account, if grouped by Account"))

    if (filters.get("voucher_no")
            and filters.get("group_by") in [_('Group by Voucher')]):
        frappe.throw(_("Can not filter based on Voucher No, if grouped by Voucher"))

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))

    if filters.get('project'):
        filters.project = filters.get('project')

    if filters.get('cost_center'):
        filters.cost_center = filters.get('cost_center')


def validate_party(filters):
    party_type, party = filters.get("party_type"), filters.get("party")

    if party:
        if not party_type:
            frappe.throw(_("To filter based on Party, select Party Type first"))
        else:
            # for d in party:
            if not frappe.db.exists(party_type, party):
                frappe.throw(_("Invalid {0}: {1}").format(party_type, party))


def set_account_currency(filters):
    if filters.get("account") or (filters.get('party') and len(filters.party) == 1):
        filters["company_currency"] = frappe.get_value('Company', filters.company, "default_currency")
        account_currency = None

        if filters.get("account"):
            account_currency = get_account_currency(filters.account)
        elif filters.get("party"):
            gle_currency = frappe.db.get_value(
                "GL Entry", {
                    "party_type": filters.party_type, "party": filters.party[0], "company": filters.company
                },
                "account_currency"
            )

            if gle_currency:
                account_currency = gle_currency
            else:
                account_currency = (None if filters.party_type in ["Employee", "Student", "Shareholder", "Member"] else
                                    frappe.db.get_value(filters.party_type, filters.party[0], "default_currency"))

        filters["account_currency"] = account_currency or filters.company_currency
        if filters.account_currency != filters.company_currency and not filters.presentation_currency:
            filters.presentation_currency = filters.account_currency

    return filters


def get_result(filters, account_details):
    gl_entries = get_gl_entries(filters)

    data = get_data_with_opening_closing(filters, account_details, gl_entries)

    result = get_result_as_list(data, filters)

    return result


def get_gl_entries(filters):
    select_fields = """, debit, credit, debit_in_account_currency,
		credit_in_account_currency """

    group_by_statement = 'group by name'
    order_by_statement = "order by posting_date, account"

    if filters.get("group_by") == _("Group by Voucher"):
        order_by_statement = "order by posting_date, voucher_type, voucher_no"

    if filters.get("group_by") == _("Group by Voucher (Consolidated)"):
        group_by_statement = "group by voucher_type, voucher_no, account, cost_center"

        select_fields = """, sum(debit) as debit, sum(credit) as credit,
			round(sum(debit_in_account_currency), 4) as debit_in_account_currency,
			round(sum(credit_in_account_currency), 4) as  credit_in_account_currency"""
    party_filter = ""

    if filters.get("party_name"):
        if filters['party_type'] == "Customer":
            party_name = frappe.get_value(filters['party_type'], filters['party_name'], "name")
            if not party_name:
                party_name = frappe.get_value(filters['party_type'], dict(
                    customer_name=filters['party_name']), "name")
        else:
            party_name = filters['party_name']
        import re
        party_name = u''.join((party_name,)).encode('utf-8')
        # party_name = "".join(re.split("[^a-zA-Z 1234567890()#$&@*']*", party_name))
        if party_name != filters['party_name']:
            party_filter = ' and party like "%{party_name}%" '.format(party_name=party_name)
            send_msg_telegram(party_filter)

        else:
            party_filter = ' and party="{0}" '.format(filters['party_name'])
    gl_entries = frappe.db.sql(
        """
        select
            posting_date, account, party_type, party,
            voucher_type, voucher_no, cost_center, project,
            against_voucher_type, against_voucher, account_currency,
            remarks, against, is_opening {select_fields}
        from `tabGL Entry`
        where company=%(company)s {conditions} {party_filter} {group_by_statement} 
        {order_by_statement}
        """.format(
            select_fields=select_fields, conditions=get_conditions(filters),
            group_by_statement=group_by_statement,
            order_by_statement=order_by_statement,
            party_filter=party_filter
        ),
        filters, as_dict=1)
    send_msg_telegram("""
        select
            posting_date, account, party_type, party,
            voucher_type, voucher_no, cost_center, project,
            against_voucher_type, against_voucher, account_currency,
            remarks, against, is_opening {select_fields}
        from `tabGL Entry`
        where company=%(company)s {conditions} {party_filter} {group_by_statement} 
        {order_by_statement}
        """.format(
        select_fields=select_fields, conditions=get_conditions(filters),
        group_by_statement=group_by_statement,
        order_by_statement=order_by_statement,
        party_filter=party_filter
    ) % filters)
    return gl_entries


def get_conditions(filters):
    conditions = []
    if filters.get("account"):
        lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
        conditions.append("""account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt))

    if filters.get("cost_center"):
        filters.cost_center = get_cost_centers_with_children(filters.cost_center)
        conditions.append("cost_center in %(cost_center)s")

    if filters.get("voucher_no"):
        conditions.append("voucher_no=%(voucher_no)s")

    if filters.get("group_by") == "Group by Party" and not filters.get("party_type"):
        conditions.append("party_type in ('Customer', 'Supplier')")

    if filters.get("party_type"):
        conditions.append("party_type=%(party_type)s")

    if not (filters.get("account") or filters.get("party") or
            filters.get("group_by") in ["Group by Account", "Group by Party"]):
        conditions.append("posting_date >=%(from_date)s")
        conditions.append("posting_date <=%(to_date)s")

    if filters.get("project"):
        conditions.append("project = %(project)s")

    if filters.get("finance_book"):
        conditions.append("ifnull(finance_book, '') in (%(finance_book)s, '')")

    from frappe.desk.reportview import build_match_conditions
    match_conditions = build_match_conditions("GL Entry")

    if match_conditions:
        conditions.append(match_conditions)

    # accounting_dimensions = get_accounting_dimensions()
    #
    # if accounting_dimensions:
    #     for dimension in accounting_dimensions:
    #         if filters.get(dimension):
    #             conditions.append("{0} in (%({0})s)".format(dimension))

    return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_data_with_opening_closing(filters, account_details, gl_entries):
    data = []

    gle_map = initialize_gle_map(gl_entries, filters)

    totals, entries = get_accountwise_gle(filters, gl_entries, gle_map)
    if filters.get("group_by") != _("No Grouping (Consolidated)"):
        # Opening for filtered account
        data.append(totals.opening)

    if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
        for acc, acc_dict in iteritems(gle_map):
            # acc
            if acc_dict.entries:
                if filters.get("group_by") != _("No Grouping (Consolidated)"):
                    # opening
                    data.append({})
                if filters.get("group_by") not in (_("Group by Voucher"), _("No Grouping (Consolidated)")):
                    data.append(acc_dict.totals.opening)

                data += acc_dict.entries
                if filters.get("group_by") != _("No Grouping (Consolidated)"):
                    # totals
                    data.append(acc_dict.totals.total)

                # closing
                if filters.get("group_by") not in (_("Group by Voucher"), _("No Grouping (Consolidated)")):
                    data.append(acc_dict.totals.closing)
        data.append({})
    else:
        data += entries

    # totals
    data.append(totals.total)

    # closing
    data.append(totals.closing)

    return data


def get_totals_dict():
    def _get_debit_credit_dict(label):
        return _dict(
            account="'{0}'".format(label),
            debit=0.0,
            credit=0.0,
            debit_in_account_currency=0.0,
            credit_in_account_currency=0.0
        )

    return _dict(
        opening=_get_debit_credit_dict(_('Opening')),
        total=_get_debit_credit_dict(_('Total')),
        closing=_get_debit_credit_dict(_('Closing (Opening + Total)'))
    )


def group_by_field(group_by):
    if group_by == _('Group by Party'):
        return 'party'
    elif group_by in [_('Group by Voucher (Consolidated)'), _('Group by Account')]:
        return 'account'
    else:
        return 'voucher_no'


def initialize_gle_map(gl_entries, filters):
    gle_map = frappe._dict()
    group_by = group_by_field(filters.get('group_by'))

    for gle in gl_entries:
        gle_map.setdefault(gle.get(group_by), _dict(totals=get_totals_dict(), entries=[]))
    return gle_map


def get_accountwise_gle(filters, gl_entries, gle_map):
    totals = get_totals_dict()
    entries = []
    group_by = group_by_field(filters.get('group_by'))

    def update_value_in_dict(data, key, gle):
        data[key].debit += round(flt(gle.debit), 4)
        data[key].credit += round(flt(gle.credit), 4)

        data[key].debit_in_account_currency += round(flt(gle.debit_in_account_currency), 4)
        data[key].credit_in_account_currency += round(flt(gle.credit_in_account_currency), 4)

    from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
    for gle in gl_entries:
        if (gle.posting_date < from_date or
                (cstr(gle.is_opening) == "Yes" and not filters.get("show_opening_entries"))):
            update_value_in_dict(gle_map[gle.get(group_by)].totals, 'opening', gle)
            update_value_in_dict(totals, 'opening', gle)

            update_value_in_dict(gle_map[gle.get(group_by)].totals, 'closing', gle)
            update_value_in_dict(totals, 'closing', gle)

        elif gle.posting_date <= to_date:
            update_value_in_dict(gle_map[gle.get(group_by)].totals, 'total', gle)
            update_value_in_dict(totals, 'total', gle)
            if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
                gle_map[gle.get(group_by)].entries.append(gle)
            else:
                entries.append(gle)

            update_value_in_dict(gle_map[gle.get(group_by)].totals, 'closing', gle)
            update_value_in_dict(totals, 'closing', gle)

    return totals, entries


def get_result_as_list(data, filters):
    balance, balance_in_account_currency = 0, 0
    inv_details = get_supplier_invoice_details()

    for d in data:
        if not d.get('posting_date'):
            balance, balance_in_account_currency = 0, 0

        balance = get_balance(d, balance, 'debit', 'credit')
        d['balance'] = round(balance, 4)

        d['account_currency'] = filters.account_currency
        d['bill_no'] = inv_details.get(d.get('against_voucher'), '')

    return data


def get_supplier_invoice_details():
    inv_details = {}
    for d in frappe.db.sql(""" select name, bill_no from `tabPurchase Invoice`
		where docstatus = 1 and bill_no is not null and bill_no != '' """, as_dict=1):
        inv_details[d.name] = d.bill_no

    return inv_details


def get_balance(row, balance, debit_field, credit_field):
    balance += (row.get(debit_field, 0) - row.get(credit_field, 0))

    return round(balance, 4)


def get_columns(filters):
    if filters.get("presentation_currency"):
        currency = filters["presentation_currency"]
    else:
        if filters.get("company"):
            currency = get_company_currency(filters["company"])
        else:
            company = get_default_company()
            currency = get_company_currency(company)

    columns = [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 90
        },
        {
            "label": _("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 180
        },
        {
            "label": _("Debit ({0})".format(currency)),
            "fieldname": "debit",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Credit ({0})".format(currency)),
            "fieldname": "credit",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Balance ({0})".format(currency)),
            "fieldname": "balance",
            "fieldtype": "Float",
            "width": 130
        }
    ]

    columns.extend([
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180
        },
        {
            "label": _("Against Account"),
            "fieldname": "against",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Project"),
            "options": "Project",
            "fieldname": "project",
            "fieldtype": "Link",
            "width": 100
        },
        {
            "label": _("Cost Center"),
            "options": "Cost Center",
            "fieldname": "cost_center",
            "width": 100
        },
        {
            "label": _("Against Voucher Type"),
            "fieldname": "against_voucher_type",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Against Voucher"),
            "fieldname": "against_voucher",
            "fieldtype": "Dynamic Link",
            "options": "against_voucher_type",
            "width": 100
        },
        {
            "label": _("Supplier Invoice No"),
            "fieldname": "bill_no",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Remarks"),
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 00
        }
        # {
        #     "label": _("Label"),
        #     "fieldname": "title",
        #     "width": 100
        # }
    ])

    return columns


# def get_cost_centers_with_children(cost_centers):
#     # if not isinstance(cost_centers, list):
#     #     cost_centers = [d.strip() for d in cost_centers.strip().split(',') if d]
#
#     all_cost_centers = [cost_centers]
#     # for d in cost_centers:
#     lft, rgt = frappe.db.get_value("Cost Center", cost_centers, ["lft", "rgt"])
#     children = frappe.get_all("Cost Center", filters={"lft": [">=", lft], "rgt": ["<=", rgt]})
#     all_cost_centers += [c.name for c in children]
#
#     # send_msg_telegram(str(list(set(all_cost_centers))))
#     return list(set(all_cost_centers))

def get_cost_centers_with_children(cost_centers):
    if not isinstance(cost_centers, list):
        cost_centers = [d.strip() for d in cost_centers.strip().split(',') if d]
    all_cost_centers = []
    for d in cost_centers:
        if frappe.db.exists("Cost Center", d):
            lft, rgt = frappe.db.get_value("Cost Center", d, ["lft", "rgt"])
            children = frappe.get_all("Cost Center", filters={"lft": [">=", lft], "rgt": ["<=", rgt]})
            all_cost_centers += [c.name for c in children]
        else:
            frappe.throw(_("Cost Center: {0} does not exist").format(d))

    return list(set(all_cost_centers))
