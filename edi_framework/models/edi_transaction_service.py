from odoo import models

from ..services import TransactionService


class EdiTransactionService(models.AbstractModel):
    _name = "edi.transaction.service"
    _description = "EDI Transaction Service"

    def start_transaction(self, **kwargs):
        return TransactionService(self.env).start_transaction(**kwargs)
