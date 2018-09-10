# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.utilities.hijri_date import convert_to_hijri

class PaymentReconciliationInvoice(Document):
	def before_save(self):
		self.invoice_hijri_date = convert_to_hijri(self.invoice_date)
