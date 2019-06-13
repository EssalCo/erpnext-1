// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Account', {
	setup: function(frm) {
		frm.add_fetch('parent_account', 'report_type', 'report_type');
		frm.add_fetch('parent_account', 'root_type', 'root_type');
	},
	onload: function(frm) {
		frm.set_query('parent_account', function(doc) {
			return {
				filters: {
					"is_group": 1,
					"company": doc.company
				}
			};
		});
	},
	refresh: function(frm) {
		if (frm.doc.__islocal) {
			frappe.msgprint(__("Please create new account from Chart of Accounts."));
			throw "cannot create";
			
		}
		
		if (frm.doc.account_serial === undefined || frm.doc.account_serial == "" || frm.doc.account_serial == "0") {
			frappe.db.get_value('Account', {'name': frm.doc.parent_account}, ["account_serial"], function (r) {
			frm.set_value('account_serial', r.account_serial === undefined ? r.account_serial : 1);
		});
		}
		frm.toggle_display('account_name', frm.doc.__islocal);

		// hide fields if group
		frm.toggle_display(['account_type', 'tax_rate'], cint(frm.doc.is_group) == 0);

		// disable fields
		frm.toggle_enable(['account_name', 'is_group', 'company'], false);

		if (cint(frm.doc.is_group) == 0) {
			frm.toggle_display('freeze_account', frm.doc.__onload
				&& frm.doc.__onload.can_freeze_account);
		}

		// read-only for root accounts
		if (!frm.doc.parent_account) {
			frm.set_read_only();
			frm.set_intro(__("This is a root account and cannot be edited."));
		} else {
			// credit days and type if customer or supplier
			frm.set_intro(null);
			frm.trigger('account_type');

			// show / hide convert buttons
			frm.trigger('add_toolbar_buttons');
		}

		if(!frm.doc.__islocal) {
			frm.add_custom_button(__('Update Account Name / Number'), function () {
				frm.trigger("update_account_number");
			});
		}

		if(!frm.doc.__islocal) {
			frm.add_custom_button(__('Merge Account'), function () {
				frm.trigger("merge_account");
			});
		}
	},
	account_type: function (frm) {
		if (frm.doc.is_group == 0) {
			frm.toggle_display(['tax_rate'], frm.doc.account_type == 'Tax');
			frm.toggle_display('warehouse', frm.doc.account_type == 'Stock');
		}
	},
	add_toolbar_buttons: function(frm) {
		frm.add_custom_button(__('Chart of Accounts'),
			function () { frappe.set_route("Tree", "Account"); });

		if (frm.doc.is_group == 1) {
			frm.add_custom_button(__('Group to Non-Group'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'convert_group_to_ledger',
					callback: function() {
						frm.refresh();
					}
				});
			});
		} else if (cint(frm.doc.is_group) == 0
			&& frappe.boot.user.can_read.indexOf("GL Entry") !== -1) {
			cur_frm.add_custom_button(__('Ledger'), function () {
				frappe.route_options = {
					"account": frm.doc.name,
					"from_date": frappe.sys_defaults.year_start_date,
					"to_date": frappe.sys_defaults.year_end_date,
					"company": frm.doc.company
				};
				frappe.set_route("query-report", "General Ledger");
			});

			frm.add_custom_button(__('Non-Group to Group'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'convert_ledger_to_group',
					callback: function() {
						frm.refresh();
					}
				});
			});
		}
	},

	merge_account: function(frm) {
		var d = new frappe.ui.Dialog({
			title: __('Merge with Existing Account'),
			fields: [
				{
					"label" : "Name",
					"fieldname": "name",
					"fieldtype": "Data",
					"reqd": 1,
					"default": frm.doc.name
				}
			],
			primary_action: function() {
				var data = d.get_values();
				frappe.call({
					method: "erpnext.accounts.doctype.account.account.merge_account",
					args: {
						old: frm.doc.name,
						new: data.name,
						is_group: frm.doc.is_group,
						root_type: frm.doc.root_type,
						company: frm.doc.company
					},
					callback: function(r) {
						if(!r.exc) {
							if(r.message) {
								frappe.set_route("Form", "Account", r.message);
							}
							d.hide();
						}
					}
				});
			},
			primary_action_label: __('Merge')
		});
		d.show();
	},

	update_account_number: function(frm) {
		var d = new frappe.ui.Dialog({
			title: __('Update Account Number / Name'),
			fields: [
				{
					"label": "Account Name",
					"fieldname": "account_name",
					"fieldtype": "Data",
					"reqd": 1,
					"default": frm.doc.account_name
				},
				{
					"label": "Account Number",
					"fieldname": "account_number",
					"fieldtype": "Data",
					"default": frm.doc.account_number
				}
			],
			primary_action: function() {
				var data = d.get_values();
				if(data.account_number === frm.doc.account_number && data.account_name === frm.doc.account_name) {
					d.hide();
					return;
				}

				frappe.call({
					method: "erpnext.accounts.doctype.account.account.update_account_number",
					args: {
						account_number: data.account_number,
						account_name: data.account_name,
						name: frm.doc.name
					},
					callback: function(r) {
						if(!r.exc) {
							if(r.message) {
								frappe.set_route("Form", "Account", r.message);
							} else {
								frm.set_value("account_number", data.account_number);
								frm.set_value("account_name", data.account_name);
							}
							d.hide();
						}
					}
				});
			},
			primary_action_label: __('Update')
		});
		d.show();
	}
});
