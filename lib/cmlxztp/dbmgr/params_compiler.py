'''
Created on Feb 15, 2018

@author: samerd
'''
import re


class ParamsError(Exception):
    pass


class CompiledLine(object):
    VAR_REGEX = re.compile(r'<<(\w+)>>')

    def __init__(self, line):
        self._line = line
        self._variables = set()

    def compile(self):
        self._variables = self._read_vars(self._line)

    @classmethod
    def _read_vars(cls, line):
        variables = cls.VAR_REGEX.findall(line)
        return set(variables)

    def _translate_line(self, line, variables, params):
        for var in variables:
            var_val = params[var]
            line = line.replace("<<%s>>" % var, var_val.strip())
        return line

    def translate(self, params):
        translated_line = self._translate_line(
            self._line, self._variables, params)
        return [translated_line]


class CompiledLoopLine(CompiledLine):
    LOOP_REGEX = re.compile(r'^LOOP<<(\w+)>>\:(.*)$')

    def __init__(self, line):
        super(CompiledLoopLine, self).__init__(line)
        self._loop_var = None

    def compile(self):
        match = self.LOOP_REGEX.match(self._line)
        if not match:
            raise ParamsError('Invalid loop line: %s' % self._line)
        self._loop_var = match.group(1)
        self._line = match.group(2)
        self._variables = self._read_vars(self._line)

    def translate(self, params):
        template_line = self._translate_line(
            self._line, self._variables, params)
        val_list = params[self._loop_var].split()
        translated_lines = []
        for item in val_list:
            loop_param = {}
            loop_vals = item.split(':')
            variables = []
            for index, val in enumerate(loop_vals):
                var_name = 'LOOP_VAR:%s' % (index + 1)
                variables.append(var_name)
                loop_param[var_name] = val
            translated_line = self._translate_line(
                template_line, variables, loop_param)
            translated_lines.append(translated_line)
        return translated_lines


class ParamsCompiler(object):
    LOOP_PREFIX = 'LOOP<'

    def __init__(self, cfg_file):
        self._cfg_file = cfg_file
        self._compiled_lines = []

    def _read(self):
        lines = []
        try:
            with open(self._cfg_file, 'r') as fp:
                for line in fp:
                    line = line.strip()
                    if line:
                        lines.append(line)
        except IOError as e:
            raise ParamsError('Failed to read file: %s (%s)' %
                              (self._cfg_file, str(e)))
        return lines

    def compile(self):
        lines = self._read()
        for line in lines:
            if line.startswith(self.LOOP_PREFIX):
                compiled_line = CompiledLoopLine(line)
            else:
                compiled_line = CompiledLine(line)
            compiled_line.compile()
            self._compiled_lines.append(compiled_line)

    def translate(self, params):
        if not self._compiled_lines:
            raise ParamsError('Trying to translate file: %s before compile' %
                              self._cfg_file)
        translated_lines = []
        for compiled_line in self._compiled_lines:
            lines = compiled_line.translate(params)
            translated_lines.extend(lines)
        return translated_lines
