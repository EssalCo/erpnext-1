// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'department', 'department');
// cur_frm.cscript.custom_employee = function(doc, cdt, cd) {
//     alert("Ggg");
// }
cur_frm.add_fetch("employee", "date_of_joining", "work_start_date");

frappe.ui.form.on('End of Service Award', {
    refresh: function(frm) {
        // if (!cur_frm.doc.__islocal) {
        //     for (var key in cur_frm.fields_dict) {
        //         cur_frm.fields_dict[key].df.read_only = 1;
        //     }
        //     cur_frm.disable_save();
        // } else {
        //     cur_frm.enable_save();
        // }
        // frappe.call({
        //     method: "unallowed_actions",
        //     doc: frm.doc,
        //     freeze: true,
        //     callback: function(r) {
        //         if (r.message && frappe.session.user != "Administrator") {
        //             frm.page.clear_actions_menu();
        //         }
        //     }
        // });
            if (cur_frm.doc.contract_type == "Limited") {
                cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
            } else {
                cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
            } 
            // else {
            //     cur_frm.set_df_property("reason", "options", "");
            // }
    },
    employee: function(frm) {
        
        if(cur_frm.doc.employee){
            // frappe.call({
            //     method: "erpnext.hr.doctype.salary_structure.salary_structure.make_salary_slip",
            //     args: {
            //         source_name: frm.doc.name,
            //         employee: frm.doc.employee
            //     },
            //     callback: function(r) {
            //         console.log(r.message);
            //         // var new_window = window.open();
            //         // new_window.document.write(r.message);
            //         // frappe.msgprint(r.message);
            //     }
            // });

            frappe.call({
                "method": "get_salary",
                doc: cur_frm.doc,
                args: { "employee": cur_frm.doc.employee },
                callback: function(data) {
                    if (data) {
                        // cur_frm.set_value('ticket_number', );
                        // cur_frm.set_value('leave_number', );
                        // cur_frm.set_value('leave_cost', );
                        // cur_frm.set_value('ticket_cost', );
                        // cur_frm.set_value('ticket_total_cost', );
                        // cur_frm.set_value('leave_total_cost', );
                        // cur_frm.set_value('total', );

                        cur_frm.set_value('salary', data.message);
                        cur_frm.set_value('leave_cost', Math.round(data.message/30));
                    }
                }
            });
        }

        if(cur_frm.doc.employee && cur_frm.doc.end_date){
            cur_frm.set_value("worked_days", frappe.datetime.get_day_diff(cur_frm.doc.end_date,frappe.datetime.month_start(cur_frm.doc.end_date)))
        }
        if(cur_frm.doc.salary && cur_frm.doc.worked_days){
            month_days_count = frappe.datetime.get_day_diff(frappe.datetime.month_end(cur_frm.doc.end_date),frappe.datetime.month_start(cur_frm.doc.end_date))
            
            cur_frm.set_value("month_salary",  Math.round((cur_frm.doc.salary/month_days_count) * cur_frm.doc.worked_days))
        }

    },
    salary: function(frm) {
        if(cur_frm.doc.salary){
            frappe.call({
                "method": "get_leave_balance",
                doc: cur_frm.doc,
                args: { "employee": cur_frm.doc.employee },
                callback: function(data) {
                    if (data.message) {
                        cur_frm.set_value('leave_number', data.message);
                        cur_frm.set_value('leave_total_cost', Math.round(data.message*cur_frm.doc.leave_cost));
                    }
                }
            });
        }
    },
    contract_type: function(frm) {
        if (cur_frm.doc.contract_type == "Limited") {
            cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
        } else {
            cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
        }
        //  else {
        //     cur_frm.set_df_property("reason", "options", "");
        // }
    },
    end_date: function(frm) {
        frm.trigger("get_days_months_years");

        if(cur_frm.doc.employee && cur_frm.doc.end_date){
            cur_frm.set_value("worked_days", frappe.datetime.get_day_diff(cur_frm.doc.end_date,frappe.datetime.month_start(cur_frm.doc.end_date)))
        }
        if(cur_frm.doc.salary && cur_frm.doc.worked_days){
            month_days_count = frappe.datetime.get_day_diff(frappe.datetime.month_end(cur_frm.doc.end_date),frappe.datetime.month_start(cur_frm.doc.end_date))

            cur_frm.set_value("month_salary",  Math.round((cur_frm.doc.salary/month_days_count) * cur_frm.doc.worked_days))
        }
        
        // frappe.call({
        //     method: "erpnext.hr.doctype.end_of_service_award.end_of_service_award.get_award",
        //     args: {
        //         start_date: frm.doc.work_start_date,
        //         end_date: frm.doc.end_date,
        //         salary: frm.doc.salary,
        //         toc: frm.doc.toc,
        //         reason: frm.doc.reason
        //     },
        //     callback: function(r) {
        //         console.log(r);

        //     }
        // });
    },
    get_days_months_years: function(frm) {
        start = cur_frm.doc.work_start_date;
        end = cur_frm.doc.end_date;

        if (end < start) {
            cur_frm.set_value('years', 0);
            cur_frm.set_value('months', 0);
            cur_frm.set_value('days', 0);
            validated = false;
            frappe.throw(__("Work start date should be before end date"));
            

        } else {
            var date1 = new Date(start);
            var date2 = new Date(end);
            var timeDiff = Math.abs(date2.getTime() - date1.getTime());
            var diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24));
            years = Math.floor(diffDays / 365);
            daysrem = diffDays - (years * 365);
            months = Math.floor(daysrem / 30.416);
            monthss = months
            days = Math.ceil(daysrem - (months * 30.416));

            cur_frm.set_value('years', years);
            cur_frm.set_value('months', monthss);
            cur_frm.set_value('days', days);

        };


    },
    validate: function(frm) {
        frm.trigger("get_award");
        // frm.set_value('total', cur_frm.doc.leave_total_cost+cur_frm.doc.award);
        // console.log(cur_frm.doc.total)
    },
    after_save:function(frm) {
        // cur_frm.set_value('total', cur_frm.doc.leave_total_cost+cur_frm.doc.award);
    },
    find: function(frm) {
        frm.trigger("get_award");
    },

    get_award: function(frm) {

        if (!cur_frm.doc.reason) {
            frappe.throw(__("Please select the reason end of service"));
        }
        cur_frm.set_value('award', 0);

        // frappe.call({
        //     "method": "get_salary",
        //     doc: cur_frm.doc,
        //     args: { "employee": cur_frm.doc.employee },
        //     callback: function(data) {
        //         if (data) {
        //             cur_frm.set_value('salary', data.message);
        //         } else {
        //             cur_frm.set_value('award', "");

        //         }
        //     }
        // });


        frm.trigger("get_days_months_years");

        var salary = cur_frm.doc.salary;
        var years = parseInt(cur_frm.doc.years) + (parseInt(cur_frm.doc.months) / 12) + (parseInt(cur_frm.doc.days) / 365);
        var reason = cur_frm.doc.reason;

        if (!reason) {
            frappe.throw(__("Please select the reason end of service "));
            cur_frm.set_value('award', 0);
        } else {


            if (cur_frm.doc.contract_type == "Limited") {
                if (cur_frm.doc.reason == "فسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)" || cur_frm.doc.reason == "فسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)") {
                    cur_frm.set_value('award', "لا يستحق الموظف مكافأة نهاية خدمة");
                } else {
                    cur_frm.set_value('award', 0);

                    // cur_frm.set_value('award', "");
                    var firstPeriod, secondPeriod = 0;
                    // set periods
                    if (years > 5) {
                        firstPeriod = 5;
                        secondPeriod = years - 5;
                    } else {
                        firstPeriod = years;
                    }
                    // calculate
                    result = (firstPeriod * cur_frm.doc.salary * 0.5) + (secondPeriod * cur_frm.doc.salary);
                    cur_frm.set_value('award', Math.round(result*100)/100);
                    cur_frm.set_value('total', cur_frm.doc.leave_total_cost+cur_frm.doc.award);

                }
            } else /*if (cur_frm.doc.employment_type == "دوام كامل")*/ {


                if (cur_frm.doc.reason == "فسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)" || cur_frm.doc.reason == "ترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)") {
                    cur_frm.set_value('award', 0);
                } else if (cur_frm.doc.reason == "استقالة الموظف") {
                    if (years < 2) {
                        result = 0;
                    } else if (years <= 5) {
                        result = (1 / 6) * cur_frm.doc.salary * years;
                    } else if (years <= 10) {
                        result = ((1 / 3) * cur_frm.doc.salary * 5) + ((2 / 3) * cur_frm.doc.salary * (years - 5));
                    } else {
                        result = (0.5 * cur_frm.doc.salary * 5) + (cur_frm.doc.salary * (years - 5));
                    }
                    
                    cur_frm.set_value('award', Math.round(result*100)/100 );
                    cur_frm.set_value('total', cur_frm.doc.leave_total_cost+cur_frm.doc.award);
                    // console.log(Math.round(result*100)/100);
                    // (result).toFixed(2)
                    // console.log(result);
                } else {
                    if (years <= 5) {
                        result = 0.5 * cur_frm.doc.salary * years;
                    } else {
                        result = (0.5 * cur_frm.doc.salary * 5) + (cur_frm.doc.salary * (years - 5));
                    }
                    
                    cur_frm.set_value('award', Math.round(result*100)/100);
                    cur_frm.set_value('total', cur_frm.doc.leave_total_cost+cur_frm.doc.award);
                    // console.log(Math.round(result*100)/100);
                }


            }
        };
    }

});