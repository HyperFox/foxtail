# -*- coding: utf-8 -*-
"""
This script is used to render a webpage from a template similar as django.
Rules:
 1. all executable codes is wrapped by {%%}, you can write real python code here, more powerful than django
 2. all output variables is wrapped by {{}}, you can write multiple variables separated by comma
 3. if corresponds to endif, while corresponds to endwhile, for corresponds to endfor
 4. block represents a block which can be replaced entirely
 5. extends means this is a sub template which only provides definitions to its parent template

:copyright: (c) 2018 by Hyperfox
:license: BSD
"""


import re
import os
from collections import OrderedDict


class WebRenderEngine(object):

    @staticmethod
    def _pre_process(src_file):
        """
        remove comments and combine the slices in the same type
        :type src_file: str
        :rtype: list
        """
        slices = []
        handled_slices = []
        with open(src_file) as fs:
            for line in fs:
                slices.extend(re.split(r'({[%{#].+?[%}#]})', line))

        flg_is_comment = False
        handled_line = ''
        for slice in slices:
            if slice.startswith('{#'):
                flg_is_comment = True
            elif slice.startswith('#}'):
                flg_is_comment = False
                slice = slice[2:].strip()

            if flg_is_comment:
                continue
            elif slice.startswith('{%') or slice.startswith('{{'):
                if handled_line:
                    handled_slices.append(handled_line)
                    handled_line = ''
                handled_slices.append(slice)
            elif slice:
                handled_line += slice
        if handled_line:
            handled_slices.append(handled_line)
        return handled_slices

    @staticmethod
    def _parse_tokens(slice):
        """
        handle with pre-defined tokens, this usually in this format, {% command arg1 arg2 ... %}
        :type slice: str
        :rtype: tuple
        """
        slice_list = slice.split(' ', 1)
        keyword = slice_list[0]
        arguments = ''
        if len(slice_list) > 1:
            arguments = slice_list[1]
        return keyword, arguments

    def _expand(self, src_file, slices, data_dict):
        """
        expand the extends and replace the blocks with the proper values
        :param src_file:
        :param slices:
        :param data_dict:
        :rtype: list
        """
        flg_reparse_count = 1
        handled_slices = OrderedDict()
        while flg_reparse_count:
            flg_reparse_count -= 1
            handled_slices = OrderedDict()
            flg_first_keyword = True
            block_handle = None
            for index, slice in enumerate(slices):
                if slice.startswith('{%'):
                    keyword, arguments = self._parse_tokens(slice[2:-2].strip())
                    if keyword == 'extends':
                        if not flg_first_keyword:  # extends only works if it's the first keyword
                            continue
                        base_file = eval(arguments, globals(), data_dict)  # arguments maybe a variable or an expression
                        if not os.path.isabs(base_file):
                            base_dir = os.path.dirname(os.path.abspath(src_file))
                            base_file = os.path.join(base_dir, base_file)
                        base_slices = self._pre_process(base_file)
                        base_slices.extend(slices[index+1:])
                        slices = base_slices
                        flg_reparse_count += 1
                        break
                    elif keyword == 'include':
                        inc_file = eval(arguments, globals(), data_dict)  # arguments maybe a variable or an expression
                        if not os.path.isabs(inc_file):
                            base_dir = os.path.dirname(src_file)
                            inc_file = os.path.join(base_dir, arguments)
                        inc_slices = self._pre_process(inc_file)
                        if block_handle is not None:
                            block_handle.extend(inc_slices)
                        else:
                            handled_slices[index] = inc_slices
                    elif keyword == 'block':
                        handled_slices[arguments] = []
                        block_handle = handled_slices[arguments]
                    elif keyword == 'endblock':
                        block_handle = None
                    elif block_handle is not None:
                        block_handle.append(slice)
                    else:
                        handled_slices[index] = slice
                    flg_first_keyword = False
                else:
                    if block_handle is not None:
                        block_handle.append(slice)
                    else:
                        handled_slices[index] = slice
        # flatern
        handled_slices_list = []
        for value in handled_slices.itervalues():
            if isinstance(value, list):
                handled_slices_list.extend(value)
            else:
                handled_slices_list.append(value)
        return handled_slices_list

    def _process(self, slices, data_dict):
        """
        parse the contents and convert it to a python script
        :type slices: list
        :type data_dict: dict
        :rtype: list
        """
        handled_slices = ['from __future__ import print_function\n']
        indent = 0
        for index, slice in enumerate(slices):
            if slice.startswith('{%'):
                slice = slice[2:-2].strip()
                keyword, arguments = self._parse_tokens(slice)
                if keyword in ('if', 'for', 'while'):
                    # add a litle trick
                    if slice.endswith('.iteritems') or slice.endswith('.items'):
                        slice += '()'
                    handled_slice = '%s%s:\n' % ('    '*indent, slice)
                    handled_slices.append(handled_slice)
                    indent += 1
                elif keyword in ('elif', 'else'):
                    indent -= 1
                    handled_slice = '%s%s:\n' % ('    ' * indent, slice)
                    handled_slices.append(handled_slice)
                    indent += 1
                elif keyword in ('endif', 'endfor', 'endwhile'):
                    indent -= 1
                elif keyword == 'static':
                    arguments = eval(arguments, globals(), data_dict)
                    if arguments:
                        quote = "'''" if arguments[-1] == '"' else '"""'
                        handled_slice = '%sprint(r%s%s%s, file=output18E9zf, end="")\n' % ('    '*indent, quote, arguments, quote)
                        handled_slices.append(handled_slice)
                elif keyword == 'load':
                    pass  # doesn't support this keyword now
                else:
                    handled_slice = '%sprint(%s, file=output18E9zf, end="")\n' % ('    ' * indent, slice)
                    handled_slices.append(handled_slice)
                # ignore unknown codes
            elif slice.startswith('{{'):
                handled_slice = '%sprint(%s, file=output18E9zf, end="")\n' % ('    '*indent, slice[2:-2].strip())
                handled_slices.append(handled_slice)
            elif slice:
                quote = "'''" if slice[-1] == '"' else '"""'
                handled_slice = '%sprint(r%s%s%s, file=output18E9zf, end="")\n' % ('    ' * indent, quote, slice, quote)
                handled_slices.append(handled_slice)
        return handled_slices

    def render(self, src_file, context, output_file):
        """
        render a template using context data and generate an output_file
        :param src_file: template file path
        :type src_file: str
        :param context: we use these context data to render the template
        :type context: dict
        :param output_file: will save the render result using this path
        :type output_file: str
        """
        handled_slices = self._pre_process(src_file)
        handled_slices = self._expand(src_file, handled_slices, context)
        mid_contents = self._process(handled_slices, context)
        with open('tmpD2pkN41a.py', 'w') as fs:
            fs.writelines(mid_contents)
        with open(output_file, 'w') as fs:
            context['output18E9zf'] = fs
            execfile('tmpD2pkN41a.py', globals(), context)
        os.remove('tmpD2pkN41a.py')
