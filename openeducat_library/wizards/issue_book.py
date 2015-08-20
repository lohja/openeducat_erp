# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning

from ..models import book_unit


class IssueBook(models.TransientModel):

    """ Issue Book """
    _name = 'issue.book'

    book_id = fields.Many2one('op.book', 'Book', required=True)
    book_unit_id = fields.Many2one('op.book.unit', 'Book Unit', required=True)
    quantity = fields.Integer('No. Of Books', required=True)
    type = fields.Selection(
        [('student', 'Student'), ('faculty', 'Faculty')],
        'Type', default='student', required=True)
    student_id = fields.Many2one('op.student', 'Student')
    faculty_id = fields.Many2one('op.faculty', 'Faculty')
    library_card_id = fields.Many2one(
        'op.library.card', 'Library Card', required=True)
    issued_date = fields.Date('Issued Date', required=True)
    return_date = fields.Date('Return Date', required=True)
    state = fields.Selection(
        [('issue', 'Issued'), ('available', 'Available'),
         ('lost', 'Lost'), ('reserve', 'Reserved')],
        'Status', default='available')

    @api.onchange('library_card_id')
    def onchange_library_card_id(self):
        self.type = self.library_card_id.type
        self.student_id = self.library_card_id.student_id.id
        self.faculty_id = self.library_card_id.faculty_id.id

    @api.one
    def check_issue(self, student_id, library_card_id):
        book_movement_search = self.env["op.book.movement"].search(
            [('library_card_id', '=', library_card_id),
             ('student_id', '=', student_id),
             ('state', '=', 'issue')])
        if len(book_movement_search) < self.env["op.library.card"].browse(
                library_card_id).allow_book:
            return True
        else:
            return False

    @api.one
    def do_issue(self):
        value = {}
        total_book = 0
        for movement in self.book_unit_id.movement_lines:
            if movement.state == 'issue':
                total_book += movement.quantity
        if self.book_id.number_book > 0 and \
                self.book_id.number_book - total_book > 0:
            if self.check_issue(self.student_id.id, self.library_card_id.id):
                if self.book_unit_id.state and \
                        self.book_unit_id.state == 'available':
                    book_movement_create = {
                        'book_id': self.book_id.id,
                        'book_unit_id': self.book_unit_id.id,
                        'quantity': self.quantity,
                        'type': self.type,
                        'student_id': self.student_id.id or False,
                        'faculty_id': self.faculty_id.id or False,
                        'library_card_id': self.library_card_id.id,
                        'issued_date': self.issued_date,
                        'return_date': self.return_date,
                        'state': 'issue',
                    }
                    self.env['op.book.movement'].create(book_movement_create)
                    self.book_unit_id.state = 'issue'
                    value = {'type': 'ir.actions.act_window_close'}
                else:
                    raise Warning(_('Error!'), _(
                        'Book Unit can not be issued because \
                        book state is : %s') %
                        (dict(book_unit.unit_states).get(
                            self.book_unit_id.state)))
            else:
                raise Warning(_('Error!'), _(
                    'Maximum Number of book allowed for %s is : %s') %
                    (self.student_id.name, self.library_card_id.allow_book))
        else:
            raise Warning(_('Error!'), _('There Is No Book Available'))
        return value


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
