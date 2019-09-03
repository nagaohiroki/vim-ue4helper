import json
import codecs
import os
import subprocess
import re
import argparse
import sys
is_vim = True
try:
    import vim
except ModuleNotFoundError:
    is_vim = False


def build(param, config):
    if is_in_engine(param):
        return [
            get_build_batch(param),
            get_project_name(param) + 'Editor',
            'Win64',
            config,
            '-WaitMutex',
            '-FromMsBuild']
    return [
        get_build_batch(param),
        get_project_name(param) + 'Editor',
        'Win64',
        config,
        '-Project=' + param['project'],
        '-WaitMutex',
        '-FromMsBuild']


def dumps(param):
    logs = []
    log = os.path.join(
        param['engine'],
        'Engine',
        'Programs',
        'UnrealBuildTool',
        'Log.txt')
    pattern_msvc = re.compile(r".*?([A-Z]:.*?)\(([0-9]+)\): (.*)")
    pattern_clang = re.compile(r".*?([A-Z]:.*?)\(([0-9]+),([0-9]+)\): (.*)")
    with codecs.open(log, 'r', 'utf-8') as file:
        for line in file.readlines():
            match = re.match(pattern_msvc, line)
            dic = {}
            if match:
                dic['text'] = match[3]
            else:
                match = re.match(pattern_clang, line)
                if match:
                    dic['col'] = match[3]
                    dic['text'] = match[4]
                else:
                    continue
            dic['filename'] = match[1].replace(os.path.sep, os.path.altsep)
            dic['lnum'] = match[2]
            dic['type'] = 'E'
            if 'warning' in dic['text'] or 'note' in dic['text']:
                dic['type'] = 'W'
            logs.append(dic)
    if is_vim:
        vim.command(':call setqflist(' + str(logs) + ')')


def fzf(param, key):
    path = None
    if key == 'engine':
        path = os.path.join(param[key], 'Engine')
    if key == 'project':
        path = os.path.dirname(param[key])
    if not path:
        return
    path = os.path.join(path, 'Source')
    cmd = ':FZF ' + path.replace(os.path.sep, os.path.altsep)
    if is_vim:
        vim.command(cmd)
        return
    print(cmd)


def get_sln_path(param):
    if is_in_engine(param):
        return os.path.join(param['engine'], 'UE4.sln')
    base, _ = os.path.splitext(param['project'])
    return base + '.sln'


def get_devenv():
    return os.path.join(get_vspath(), 'Common7', 'IDE', 'devenv')


def generate_project(param):
    work_dir = param['engine']
    generate_project_cmd = ['GenerateProjectFiles.bat']
    if not is_in_engine(param):
        work_dir = os.path.dirname(param['project'])
        generate_project_cmd = get_generate_project_cmd(param)
    os.chdir(work_dir)
    subprocess.call(generate_project_cmd, shell=True)
    subprocess.call(generate_project_cmd + ['-CMakefile'], shell=True)
    cmake_proc = subprocess.Popen(get_compiler_cmd(), shell=True)
    ctags_proc = subprocess.Popen(get_ctags_cmd(param), shell=True)
    cmake_proc.wait()
    ctags_proc.wait()
    print('done')


def get_generate_project_cmd(param):
    uproject = param['project']
    build = get_build_batch(param)
    return [build, '-projectfiles', '-project=' + uproject, '-game', '-rocket']


def get_compiler_cmd():
    cmd = ['cmake', '-G', 'Ninja', '-DCMAKE_EXPORT_COMPILE_COMMANDS=1', '.']
    vsdevcmd = os.path.join(get_vspath(), 'Common7', 'Tools', 'VsDevCmd')
    if os.path.exists(vsdevcmd):
        return [vsdevcmd, '&'] + cmd
    return cmd


def get_ctags_cmd(param):
    cmd = [
        'ctags',
        '--languages=c++',
        '--exclude=Intermediate',
        '--output-format=e-ctags']
    src = [
        os.path.join(param['engine'], 'Engine'),
        param['project']]
    for path in src:
        cmd += ['-R', path]
    return cmd


def get_param():
    path = os.path.join(os.path.expanduser('~'), 'ue4_project.json')
    with codecs.open(path, 'r', 'utf-8') as f:
        return json.load(f)


def is_in_engine(param):
    root = os.path.dirname(os.path.dirname(param['project']))
    return param['engine'] == root


def get_build_batch(param):
    engine = param['engine']
    return os.path.join(engine, 'Engine', 'Build', 'BatchFiles', 'Build')


def get_project_name(param):
    return os.path.splitext(os.path.basename(param['project']))[0]


def get_vspath():
    vs15 = get_vs15path()
    if vs15:
        return vs15
    return get_vs14path()


def get_vs15path():
    try:
        cmd = ['vswhere', '-format', 'json']
        proc = subprocess.check_output(cmd, encoding='cp932')
    except FileNotFoundError:
        return
    dic = json.loads(proc)
    if len(dic) < 1:
        return
    tag = 'installationPath'
    if tag in dic[0]:
        return dic[0][tag]


def get_vs14path():
    vs14path = os.getenv('VS140COMNTOOLS')
    if vs14path:
        return os.path.dirname(os.path.dirname(os.path.dirname(vs14path)))


def get_project_cmd(param, config):
    if is_in_engine(param):
        return open_project_in_engine(param, config)
    return open_project_only(param, config)


def open_project_in_engine(param, config):
    ue4 = os.path.join(
        param['engine'],
        'Engine',
        'Binaries',
        'Win64',
        'UE4Editor')
    cmd = [ue4, get_project_name(param)]
    if config == '-debug':
        cmd += [config]
    return cmd


def open_project_only(param, config):
    cmd = param['project']
    if config == '-debug':
        cmd + [config]
    return cmd


def info(param):
    print(is_in_engine(param))
    print(get_sln_path(param))
    print(get_devenv())
    print(get_generate_project_cmd(param))
    print(get_compiler_cmd())
    print(get_ctags_cmd(param))
    print(get_build_batch(param))
    print(get_project_name(param))
    print(get_vspath())
    print(get_project_cmd(param, None))


def arguments():
    parser = argparse.ArgumentParser(description='ue4')
    parser.add_argument('--info', action='store_true')
    parser.add_argument('--build')
    parser.add_argument('--generateproject', action='store_true')
    parser.add_argument('--dumps', action='store_true')
    parser.add_argument('--openproject')
    parser.add_argument('--opensln', action='store_true')
    parser.add_argument('--runsln', action='store_true')
    parser.add_argument('--fzf', metavar='project engine')
    args, _ = parser.parse_known_args(sys.argv)
    action(args)


def action(arg):
    param = get_param()
    if arg.info:
        info(param)
    if arg.generateproject:
        generate_project(param)
    if arg.build:
        subprocess.call(build(param, arg.build), shell=True)
    if arg.dumps:
        dumps(param)
    if arg.openproject:
        subprocess.Popen(get_project_cmd(param, arg.openproject), shell=True)
    if arg.opensln:
        subprocess.call(get_sln_path(param), shell=True)
    if arg.runsln:
        subprocess.call([get_devenv(), '/r', get_sln_path(param)], shell=True)
    if arg.fzf:
        fzf(param, arg.fzf)


def main():
    arguments()


if __name__ == '__main__':
    main()
