#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.pool import Pool
from . import operation


def register():
    Pool.register(
        operation.Configuration,
        operation.Operation,
        operation.OperationTracking,
        module='production_operation_tracking', type_='model')
