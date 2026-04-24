from markupsafe import Markup, escape

from odoo import api, fields, models


class SdReportsHistoryWizard(models.TransientModel):
    _name = "sd.reports.history.wizard"
    _description = "Reports History Timeline"

    partner_id = fields.Many2one("res.partner", string="Contact", required=True, readonly=True)
    line_ids = fields.One2many(
        "sd.reports.history.wizard.line",
        "wizard_id",
        string="History Items",
        readonly=True,
    )
    timeline_html = fields.Html(
        string="Timeline",
        compute="_compute_timeline_html",
        readonly=True,
        sanitize=False,
    )
    date_filter = fields.Selection(
        [
            ("all", "All Dates"),
            ("30", "Last 30 Days"),
            ("90", "Last 90 Days"),
            ("year", "Last Year"),
        ],
        string="Date",
        default="all",
        required=True,
    )
    state_filter = fields.Selection(
        [
            ("all", "All Statuses"),
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="all",
        required=True,
    )
    visible_limit = fields.Integer(default=10, required=True)
    history_total_count = fields.Integer(string="Total", readonly=True)
    has_more = fields.Boolean(string="Has More", readonly=True)
    history_counter = fields.Char(
        string="Showing",
        compute="_compute_history_counter",
        readonly=True,
    )

    @api.model
    def create_from_partner(self, partner):
        partner.ensure_one()
        wizard = self.create({"partner_id": partner.id})
        wizard._load_timeline_lines()
        return wizard

    def _load_timeline_lines(self):
        for wizard in self:
            wizard.line_ids.unlink()
            domain = wizard._get_sale_order_domain()
            total_count = self.env["sale.order"].search_count(domain)
            sale_orders = self.env["sale.order"].search(
                domain,
                order="date_order desc, id desc",
                limit=wizard.visible_limit,
            )
            line_commands = []
            for order in sale_orders:
                line_commands.append(
                    (
                        0,
                        0,
                        {
                            "line_date": order.date_order,
                            "kind": "sale_order",
                            "title": order.name,
                            "description": order.state,
                            "amount": order.amount_total,
                            "currency_id": order.currency_id.id,
                            "source_model": order._name,
                            "source_id": order.id,
                        },
                    )
                )
            wizard.write(
                {
                    "line_ids": line_commands,
                    "history_total_count": total_count,
                    "has_more": total_count > len(sale_orders),
                }
            )

    def _get_sale_order_domain(self):
        self.ensure_one()
        domain = [("partner_id", "child_of", self.partner_id.id)]
        if self.date_filter != "all":
            if self.date_filter == "30":
                date_from = fields.Datetime.subtract(fields.Datetime.now(), days=30)
            elif self.date_filter == "90":
                date_from = fields.Datetime.subtract(fields.Datetime.now(), days=90)
            else:
                date_from = fields.Datetime.subtract(fields.Datetime.now(), years=1)
            domain.append(("date_order", ">=", date_from))
        if self.state_filter != "all":
            domain.append(("state", "=", self.state_filter))
        return domain

    @api.depends("line_ids", "history_total_count")
    def _compute_history_counter(self):
        for wizard in self:
            wizard.history_counter = "Showing %s of %s" % (
                len(wizard.line_ids),
                wizard.history_total_count,
            )

    def action_apply_filters(self):
        self.ensure_one()
        self.visible_limit = 10
        self._load_timeline_lines()
        return self._reload_wizard_action()

    def action_load_more(self):
        self.ensure_one()
        self.visible_limit += 10
        self._load_timeline_lines()
        return self._reload_wizard_action()

    def _reload_wizard_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reports History",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.depends(
        "line_ids.line_date",
        "line_ids.kind",
        "line_ids.title",
        "line_ids.description",
        "line_ids.amount",
        "line_ids.currency_id",
        "line_ids.source_model",
        "line_ids.source_id",
    )
    def _compute_timeline_html(self):
        for wizard in self:
            if not wizard.line_ids:
                wizard.timeline_html = Markup(
                    "<div class='sd_reports_history_empty'>No history items found.</div>"
                )
                continue

            items = []
            for line in wizard.line_ids.sorted(
                key=lambda item: (item.line_date or fields.Datetime.now(), item.id),
                reverse=True,
            ):
                date_label = ""
                if line.line_date:
                    date_label = fields.Datetime.context_timestamp(
                        wizard, line.line_date
                    ).strftime("%Y-%m-%d %H:%M")
                amount_label = ""
                if line.currency_id and line.amount:
                    amount_label = "%s %.2f" % (line.currency_id.symbol or "", line.amount)
                product_timeline = wizard._get_product_timeline_html(line)
                items.append(
                    Markup(
                        """
                        <div class="sd_reports_history_item">
                            <div class="sd_reports_history_marker"></div>
                            <details class="sd_reports_history_details">
                                <summary class="sd_reports_history_card">
                                    <div class="sd_reports_history_item_header">
                                        <span class="sd_reports_history_title">%(title)s</span>
                                        <span class="sd_reports_history_date">%(date)s</span>
                                    </div>
                                    <div class="sd_reports_history_meta">
                                        <span>%(kind)s</span>
                                        <span>%(description)s</span>
                                        <span>%(amount)s</span>
                                    </div>
                                </summary>
                                %(product_timeline)s
                            </details>
                        </div>
                        """
                    )
                    % {
                        "title": escape(line.title or ""),
                        "date": escape(date_label),
                        "kind": escape(line.kind_label),
                        "description": escape(line.description or ""),
                        "amount": escape(amount_label),
                        "product_timeline": product_timeline,
                    }
                )
            wizard.timeline_html = Markup(
                "<div class='sd_reports_history_timeline'>%s</div>"
            ) % Markup("").join(items)

    def _get_product_timeline_html(self, line):
        if line.source_model != "sale.order" or not line.source_id:
            return Markup(
                "<div class='sd_reports_history_nested_empty'>No product details for this item.</div>"
            )

        order = self.env["sale.order"].browse(line.source_id).exists()
        if not order:
            return Markup(
                "<div class='sd_reports_history_nested_empty'>The related order was not found.</div>"
            )

        order_lines = order.order_line.filtered(lambda order_line: not order_line.display_type)
        if not order_lines:
            return Markup(
                "<div class='sd_reports_history_nested_empty'>No products on this order.</div>"
            )

        product_items = []
        for order_line in order_lines:
            product = order_line.product_id
            currency = order_line.currency_id or order.currency_id
            image_html = Markup("")
            if product:
                image_html = Markup(
                    """
                    <img
                        class="sd_reports_history_product_image"
                        src="/web/image/product.product/%(product_id)s/image_128"
                        alt="%(product_name)s"/>
                    """
                ) % {
                    "product_id": product.id,
                    "product_name": escape(product.display_name or ""),
                }
            taxes = ", ".join(order_line.tax_id.mapped("name"))
            product_items.append(
                Markup(
                    """
                    <div class="sd_reports_history_product_item">
                        <div class="sd_reports_history_product_marker"></div>
                        <div class="sd_reports_history_product_card">
                            %(image_html)s
                            <div class="sd_reports_history_product_content">
                                <div class="sd_reports_history_product_header">
                                    <span class="sd_reports_history_product_title">%(product_name)s</span>
                                    <span class="sd_reports_history_product_subtotal">%(subtotal)s</span>
                                </div>
                                <div class="sd_reports_history_product_description">%(description)s</div>
                                <div class="sd_reports_history_product_meta">
                                    <span>Qty: %(quantity)s %(uom)s</span>
                                    <span>Unit Price: %(unit_price)s</span>
                                    <span>Taxes: %(taxes)s</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                )
                % {
                    "image_html": image_html,
                    "product_name": escape(product.display_name or order_line.name or ""),
                    "subtotal": escape(self._format_amount(currency, order_line.price_subtotal)),
                    "description": escape(order_line.name or ""),
                    "quantity": escape("%s" % order_line.product_uom_qty),
                    "uom": escape(order_line.product_uom.name or ""),
                    "unit_price": escape(self._format_amount(currency, order_line.price_unit)),
                    "taxes": escape(taxes or "None"),
                }
            )

        return Markup(
            """
            <div class="sd_reports_history_product_timeline">
                <div class="sd_reports_history_product_timeline_title">Products</div>
                %s
            </div>
            """
        ) % Markup("").join(product_items)

    def _format_amount(self, currency, amount):
        if not currency:
            return "%.2f" % amount
        return "%s %.2f" % (currency.symbol or currency.name or "", amount)


class SdReportsHistoryWizardLine(models.TransientModel):
    _name = "sd.reports.history.wizard.line"
    _description = "Reports History Timeline Item"
    _order = "line_date desc, id desc"

    wizard_id = fields.Many2one(
        "sd.reports.history.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    line_date = fields.Datetime(string="Date", readonly=True)
    kind = fields.Selection(
        [
            ("sale_order", "Sale Order"),
        ],
        string="Type",
        required=True,
        readonly=True,
    )
    kind_label = fields.Char(string="Type Label", compute="_compute_kind_label")
    title = fields.Char(string="Reference", readonly=True)
    description = fields.Char(string="Description", readonly=True)
    amount = fields.Monetary(string="Amount", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    source_model = fields.Char(string="Source Model", readonly=True)
    source_id = fields.Integer(string="Source ID", readonly=True)

    @api.depends("kind")
    def _compute_kind_label(self):
        selection = dict(self._fields["kind"].selection)
        for line in self:
            line.kind_label = selection.get(line.kind, "")
