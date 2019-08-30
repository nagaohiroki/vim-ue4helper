import json
import codecs
import os
import sys
import subprocess
import re
is_vim = True
try:
    import vim
except ModuleNotFoundError:
    is_vim = False


def build(param):
    conf = 'Development'
    if 'build' in param:
        conf = param['build']
    cmd = [
        get_build_batch(param),
        param['project'] + 'Editor',
        'Win64',
        conf,
        '-Project=' + get_uproject(param),
        '-WaitMutex',
        '-FromMsBuild']
    subprocess.call(cmd, shell=True)


def dumps(param):
    logs = []
    log = os.path.join(
        param['engine_path'],
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


def fzf(path):
    if is_vim:
        vim.command(':FZF ' + os.path.join(path, 'Source'))


def get_sln_path(param):
    if is_in_engine(param):
        return os.path.join(param['engine_path'], 'UE4.sln')
    return os.path.join(param['project_path'], param['project'] + '.sln')


def get_devenv():
    return os.path.join(get_vspath(), 'Common7', 'IDE', 'devenv')


def generate_project(param):
    work_dir = param['engine_path']
    generate_project_cmd = ['GenerateProjectFiles.bat']
    if not is_in_engine(param):
        work_dir = param['project_path']
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
    uproject = get_uproject(param)
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
        os.path.join(param['engine_path'], 'Engine'),
        param['project_path']]
    for path in src:
        cmd += ['-R', path]
    return cmd


def get_param():
    path = os.path.join(os.path.expanduser('~'), 'ue4_project.json')
    with codecs.open(path, 'r', 'utf-8') as f:
        return json.load(f)


def is_in_engine(param):
    return param['engine_path'] == os.path.dirname(param['project_path'])


def get_build_batch(param):
    engine = param['engine_path']
    return os.path.join(engine, 'Engine', 'Build', 'BatchFiles', 'Build')


def get_uproject(dic):
    return os.path.join(dic['project_path'], dic['project'] + '.uproject')


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


def open_project(param):
    cmd = None
    if is_in_engine(param):
        cmd = open_project_in_engine(param)
    else:
        cmd = open_project_only(param)
    subprocess.Popen(cmd, shell=True)


def open_project_in_engine(param):
    editor = 'UE4Editor'
    debug = None
    if 'build' in param:
        build = param['build']
        if build == 'DebugGame':
            debug = '-debug'
        if build == 'Debug':
            editor = 'UE4Editor-Win64-Debug'
            debug = '-debug'
    ue4 = os.path.join(
        param['engine_path'],
        'Engine',
        'Binaries',
        'Win64',
        editor
    )
    cmd = [ue4, param['project']]
    if debug:
        cmd += [debug]
    return cmd


def open_project_only(param):
    debug = None
    if 'build' in param:
        build = param['build']
        if build == 'DebugGame':
            debug = '-debug'
        if build == 'Debug':
            debug = '-debug'
    cmd = get_uproject(param)
    if debug:
        cmd += [debug]
    return cmd


def action(arg):
    param = get_param()
    if arg == '-build':
        build(param)
    if arg == '-generate_project':
        generate_project(param)
    if arg == '-dumps':
        dumps(param)
    if arg == '-open_project':
        open_project(param)
    vs_open_prefix = '-vs_open_file='
    if arg.startswith(vs_open_prefix):
        file_path = arg.replace(vs_open_prefix, '')
        subprocess.call([get_devenv(), '/edit', file_path], shell=True)
    if arg == '-open_sln':
        subprocess.call(get_sln_path(param), shell=True)
    if arg == '-run_sln':
        subprocess.call([get_devenv(), '/r', get_sln_path(param)], shell=True)
    if arg == '-fzf_project':
        fzf(param['project_path'])
    if arg == '-fzf_engine':
        fzf(os.path.join(param['engine_path'], 'Engine'))


def main():
    for arg in sys.argv:
        action(arg)


if __name__ == '__main__':
    main()
