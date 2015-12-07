#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from datetime import datetime
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Operation', 'OperationTracking']
__metaclass__ = PoolMeta


class Operation:
    __name__ = 'production.operation'

    @classmethod
    def __setup__(cls):
        super(Operation, cls).__setup__()
        cls._buttons.update({
                'start_operation_tracking_wizard': {
                    'invisible': Eval('state') != 'waiting',
                    'icon': 'tryton-go-next',
                    },
                })
        cls._error_messages.update({
                'work_center_required': ('You can not run the operation of '
                    'production %(production)s whitout a work center '
                    'deffined.'),
                'operation_running': ('You can not run a new operation in '
                    'production %(production)s because there is an operation '
                    'of production %(production_run)s running.'),
                })

    @classmethod
    def run(cls, operations):
        for operation in operations:
            if not operation.work_center:
                cls.raise_user_error('invalid_production_state', error_args={
                        'production': operation.production.rec_name,
                        })
            if operation.work_center.type == 'employee':
                operation.start_operation_tracking()

        super(Operation, cls).run(operations)

    @classmethod
    def done(cls, operations):
        for operation in operations:
            if operation.work_center.type == 'employee':
                operation.stop_operation_tracking()
        super(Operation, cls).done(operations)

    @classmethod
    def wait(cls, operations):
        for operation in operations:
            if (operation.state != "planned" and
                operation.work_center.type == 'employee'):
                operation.stop_operation_tracking()
        super(Operation, cls).wait(operations)

    def start_operation_tracking(self):
        pool = Pool()
        Line = pool.get('production.operation.tracking')
        User = Pool().get('res.user')

        user = User(Transaction().user)

        lines = Line.search([
                ('operation.work_center.employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])

        if lines:
            self.raise_user_error('operation_running', error_args={
                    'production': self.production.rec_name,
                    'production_run': lines[0].operation.production.rec_name,
                    })

        line = Line()
        line.operation = self.id
        line.uom = self.work_center.uom
        #line.quantity = quantity
        line.start = datetime.now()
        line.save()

    def stop_operation_tracking(self):
        pool = Pool()
        Line = pool.get('production.operation.tracking')
        User = pool.get('res.user')

        user = User(Transaction().user)

        lines = Line.search([
                ('operation.work_center.employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        for line in lines:
            line.end = datetime.now()
            line.quantity = line._calc_quantity(line.end)
            line.save()


class OperationTracking:
    'Operation'
    __name__ = 'production.operation.tracking'

    start = fields.DateTime('Start')
    end = fields.DateTime('End')

    def _calc_quantity(self, end, start=None):
        pool = Pool()
        Uom = pool.get('product.uom')
        ModelData = pool.get('ir.model.data')

        if not start:
            start = self.start
        hours = round((end - start).total_seconds(), 2)
        second_uom_id = ModelData.get_id('product', 'uom_second')
        second_uom = Uom.search([
                ('id', '=', second_uom_id),
                ])
        return Uom.compute_qty(second_uom and second_uom[0] or False, hours,
            self.uom)
