import logging
import json
import os
import shutil
import sys

from pyarmor.pyarmor import (main as pyarmor_main, pytransform_bootstrap,
                             get_registration_code, query_keyinfo,
                             version as pyarmor_version)
from pyarmor.project import Project


def call_pyarmor(args):
    pyarmor_main(args)


class BaseHandler():

    def __init__(self, config):
        self._config = config
        self.children = []

    def dispatch(self, path, args):
        i = path.find('/')
        if i == -1:
            if hasattr(self, 'do_' + path):
                return getattr(self, 'do_' + path)(args)
            raise RuntimeError('No route for %s', path)
        else:
            name = path[:i]
            for handler in self.children:
                if handler.name == name:
                    return handler.dispatch(path[i+1:], args)
            raise RuntimeError('No route for %s', name)


class RootHandler(BaseHandler):

    def __init__(self, config):
        super().__init__(config)
        self.children.extend([ProjectHandler(config), LicenseHandler(config)])

    def do_version(self, args=None):
        pytransform_bootstrap()
        rcode = get_registration_code()
        return {
            'version': pyarmor_version,
            'rcode': rcode if rcode else '',
            'info': query_keyinfo(rcode) if rcode else ''
        }

    def do_listdir(self, args):
        path = args.get('path', '')
        if os.path.exists(path):
            return [x for x in os.listdir(path) if os.path.isdir(x)]

        if sys.platform == 'win32':
            from ctypes import cdll
            drives = cdll.kernel32.GetLogicalDrives()
            result = []
            for i in range(26):
                if drives & 1:
                    result.append(chr(i + 65) + ':\\')
                drives >>= 1
        return ['/']


class ProjectHandler(BaseHandler):

    data_file = 'index.json'
    temp_id = 0

    def __init__(self, config):
        super().__init__(config)
        self.name = 'project'

    def do_build_temp(self, args):
        name = 'project-%s' % self.temp_id
        path = os.path.join(self._get_path(), name)

        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)

        cmd_args = ['init', '--src', path, path]
        call_pyarmor(cmd_args)

        data = args.get('config', {})
        project = Project()
        project.open(path)

        project._update(data)
        project.save(path)

        cmd_args = ['build']
        target = args.get('traget')
        if target and target not in ('obfuscate', 'default'):
            cmd_args.extend(['--target', target])
        output = args.get('output')
        if output:
            cmd_args.extend(['--output', output])

        cmd_args.append(path)
        call_pyarmor(cmd_args)

        return output if output else os.path.join(path, 'dist')


    def do_new(self, args):
        c = self._get_config()
        i = c['counter'] + 1

        while True:
            name = 'project-%d' % i
            path = os.path.join(self._get_path(), name)
            if not os.path.exists(path):
                logging.info('Make project path %s', path)
                os.mkdir(path)
                break
            i += 1

        cmd_args = ['init', '--src', path, path]
        call_pyarmor(cmd_args)

        project = {
            'name': name,
            'title': args.get('title', name),
            'target': args.get('target', ''),
            'path': os.path.abspath(path)
        }

        c['projects'][i] = project
        c['counter'] = i
        self._set_config(c)

        return {
            'id': i,
            'project': project
        }

    def do_update(self, args):
        c, p = self._get_project(args)
        if 'target' in args:
            p['target'] = args['target']
            self._set_config(c)

        data = args.get('config')
        if data:
            if 'name' in data:
                p['name'] = data['name']
                self._set_config(c)
            if 'title' in data:
                p['title'] = data['title']
                self._set_config(c)

            path = p['path']
            project = Project()
            project.open(path)

            project._update(data)
            project.save(path)

        return {
            'id': args['id'],
            'project': p,
            'config': project
        }

    def do_list(self, args):
        c = self._get_config()
        return c['projects'].items()

    def do_remove(self, args):
        c, p = self._get_project(args)
        c['projects'].remove(p)
        self._set_config(c)

        if args.get('clean') and p['path'].startswith(self._get_path()):
            shutil.rmtree(p['path'])
        return p

    def do_info(self, args):
        c, p = self._get_project(args)
        path = p['path']
        project = Project()
        project.open(path)
        return project

    def do_build(self, args):
        c, p = self._get_project(args)
        path = p['path']

        cmd_args = ['build']
        target = args.get('traget')
        if target and target not in ('obfuscate', 'default'):
            cmd_args.extend(['--target', target])
        output = args.get('output')
        if output:
            cmd_args.extend(['--output', output])
        cmd_args.append(path)
        call_pyarmor(cmd_args)

        return output if output else os.path.join(path, 'dist')

    def _get_project(self, args):
        c = self._get_config()
        p = c['projects'].get(args.get('id'))
        if not p:
            raise RuntimeError('No project found')
        return c, p

    def _get_path(self):
        c = self._config
        return os.path.join(c['homepath'], c['propath'])

    def _config_filename(self):
        path = self._get_path()
        filename = os.path.join(path, self.data_file)
        if not os.path.exists(filename):
            if not os.path.exists(path):
                os.makedirs(path)
            with open(filename, 'w') as fp:
                json.dump(dict(counter=0, projects={}), fp)
        return filename

    def _get_config(self):
        with open(self._config_filename(), 'r') as fp:
            return json.load(fp)

    def _set_config(self, data):
        with open(self._config_filename(), 'w') as fp:
            return json.dump(data, fp, indent=2)


class LicenseHandler(BaseHandler):

    counter_file = 'COUNTER'

    def __init__(self, config):
        super().__init__(config)
        self.name = 'license'

    def do_new(self, args):
        path = self._get_path()
        output = args.get('output', path)
        cmd_args = ['licenses', '--output', output]
        cmd_args.extend(args.get('options', []))

        rcode = args.get('rcode')
        if rcode is None:
            rcode = self._fetch_code()
        cmd_args.append(rcode)
        call_pyarmor(cmd_args)

        return os.path.join(path, rcode, 'license.lic')

    def do_remove(self, args):
        path = self._get_path()
        rcode = args.get('rcode')
        if not rcode:
            raise RuntimeError('No registration code')

        licpath = os.path.join(path, rcode)
        if os.path.exists(licpath):
            shutil.rmtree(licpath)
        return os.path.join(licpath, 'license.lic')

    def do_list(self, args=None):
        path = self._get_path()
        return [x for x in os.listdir(path) if os.path.isdir(x)]

    def do_info(self, args):
        path = self._get_path()
        rcode = args.get('rcode')
        if not rcode:
            raise RuntimeError('No registration code')

        filename = os.path.join(path, rcode, 'license.lic.txt')
        if not os.path.exists(filename):
            raise RuntimeError('No license information file')

        with open(filename) as f:
            info = f.read()

        return info

    def _get_path(self):
        c = self._config
        return os.path.join(c['homepath'], c['licpath'])

    def _fetch_code(self):
        filename = os.path.join(self._get_path(), self.counter_file)
        if os.path.exists(filename):
            with open(filename) as f:
                n = int(f.read())
        else:
            n = 0
        n += 1
        with open(filename, 'w') as f:
            f.write('%s' % n)
        return 'reg-%06d' % n


if __name__ == '__main__':
    import doctest
    doctest.testmod()
