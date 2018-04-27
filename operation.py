#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from datetime import datetime
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Operation', 'OperationTracking']



class Operation:
    __name__ = 'production.operation'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(Operation, cls).__setup__()
        cls._error_messages.update({
                'work_center_required': ('You can not run operation '
                    '%(operation)s without a work center set.'),
                'operation_running': ('You can not run a new operation in '
                    'production %(production)s because operation %(operation)s '
                    'is already running.'),
                })

    @classmethod
    def run(cls, operations):
        for operation in operations:
            if not operation.work_center:
                cls.raise_user_error('work_center_required', error_args={
                        'operation': operation.rec_name,
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
        Line = Pool().get('production.operation.tracking')
        lines = Line.search([
                ('operation.work_center.employee', '=',
                    self.work_center.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        if lines:
            self.raise_user_error('operation_running', error_args={
                    'production': self.production.rec_name,
                    'operation': lines[0].operation.rec_name,
                    })
        line = Line()
        line.operation = self.id
        line.uom = self.work_center.uom
        line.start = datetime.now()
        line.save()

    def stop_operation_tracking(self):
        Line = Pool().get('production.operation.tracking')
        lines = Line.search([
                ('operation.work_center.employee', '=',
                    self.work_center.employee.id),
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
    __metaclass__ = PoolMeta

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
