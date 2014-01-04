#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['OperationTracking']
__metaclass__ = PoolMeta


class OperationTracking:
    'Operation'
    __name__ = 'production.operation.tracking'

    start = fields.DateTime('Start')
    end = fields.DateTime('End')
