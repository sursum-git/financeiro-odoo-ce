from odoo import fields, models


class EdiTransactionMixin(models.AbstractModel):
    _name = "edi.transaction.mixin"
    _description = "EDI Transaction Mixin"

    edi_transaction_id = fields.Many2one(
        "edi.transaction",
        string="Transação EDI",
        tracking=True,
        copy=False,
    )

    def _edi_transaction_start_values(self):
        self.ensure_one()
        return {
            "record": self,
            "external_ref": getattr(self, "name", False) or getattr(self, "display_name", False),
        }

    def action_start_edi_transaction(self, **kwargs):
        self.ensure_one()
        values = self._edi_transaction_start_values()
        values.update(kwargs)
        transaction = self.env["edi.transaction.service"].start_transaction(**values)
        self.edi_transaction_id = transaction.id
        return transaction

    def action_open_edi_transaction(self):
        self.ensure_one()
        if not self.edi_transaction_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Transação EDI",
            "res_model": "edi.transaction",
            "view_mode": "form",
            "res_id": self.edi_transaction_id.id,
            "target": "current",
        }
