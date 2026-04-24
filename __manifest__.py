{
    "name": "SD Reports History",
    "summary": "Adds a partner timeline dialog for reports history.",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "author": "Derasat",
    "license": "LGPL-3",
    "depends": ["contacts", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizards/sd_reports_history_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sd_reports_history/static/src/js/sd_reports_history_accordion.js",
            "sd_reports_history/static/src/scss/sd_reports_history.scss",
        ],
    },
    "installable": True,
    "application": False,
}
