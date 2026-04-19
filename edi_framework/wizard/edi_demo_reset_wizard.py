from odoo import fields, models


class EdiDemoResetWizard(models.TransientModel):
    _name = "edi.demo.reset.wizard"
    _description = "Wizard de Reset da Demo EDI"

    exchange_id = fields.Many2one("edi.exchange", string="Exchange", required=True, readonly=True)
    reset_logs = fields.Boolean(string="Limpar Logs e Eventos", default=True)
    run_after_reset = fields.Boolean(string="Executar Após Reset", default=True)

    def action_confirm(self):
        self.ensure_one()
        self.exchange_id.action_reset_demo_state(reset_logs=self.reset_logs)
        if self.run_after_reset:
            self.exchange_id.action_run_demo_now()
        return {
            "type": "ir.actions.act_window",
            "name": "Exchange EDI",
            "res_model": "edi.exchange",
            "view_mode": "form",
            "res_id": self.exchange_id.id,
            "target": "current",
        }
