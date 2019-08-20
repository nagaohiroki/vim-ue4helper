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


def build(config):
    param = get_param()
    engine = param['engine_path']
    project_name = param['project']
    cmd = [
        get_engine_batch(engine),
        project_name + 'Editor',
        'Win64',
        config,
        '-Project=' + get_uproject(param),
        '-WaitMutex',
        '-FromMsBuild']
    subprocess.call(cmd, shell=True)


def dumps():
    param = get_param()
    logs = []
    log = os.path.join(
        param['engine_path'],
        'Engine',
        'Programs',
        'UnrealBuildTool',
        'Log.txt')
    pattern = re.compile(r".*?:   (.*?)\(([0-9]+)\): (.*)")
    with codecs.open(log, 'r', 'utf-8') as file:
        for line in file.readlines():
            if ' error ' in line:
                match = re.match(pattern, line)
                logs.append({
                    'filename': match[1].replace(os.path.sep, os.path.altsep),
                    'lnum': match[2],
                    'text': match[3],
                    'type': 'E'})
    if is_vim:
        vim.command(':let s:ue4_dumps = ' + str(logs))


def get_sln_path():
    param = get_param()
    engine = param['engine_path']
    if os.path.exists(os.path.join(engine, get_generate_project_file_bat())):
        return os.path.join(engine, 'UE4.sln')
    return os.path.join(param['project_path'], param['project'] + '.sln')


def get_devenv():
    return os.path.join(get_vspath(), 'Common7', 'IDE', 'devenv')


def generate_project():
    param = get_param()
    engine = param['engine_path']
    project = param['project_path']
    work_dir = engine
    generate_project_cmd = get_generate_project_file_bat()
    if not os.path.exists(os.path.join(engine, generate_project_cmd)):
        work_dir = project
        generate_project_cmd = [
            get_engine_batch(engine),
            '-projectfiles',
            '-project=' + get_uproject(param),
            '-game',
            '-rocket']
    os.chdir(work_dir)
    subprocess.call(generate_project_cmd, shell=True)
    subprocess.call(generate_project_cmd + ['-CMakefile'], shell=True)
    cmake_proc = create_compiler_commands()
    ctags_proc = create_ctags([
        os.path.join(engine, 'Engine', 'Source'),
        os.path.join(project, 'Source')])
    cmake_proc.wait()
    ctags_proc.wait()


def create_compiler_commands():
    cmd = [
        'cmake',
        '-G',
        'Ninja',
        '-DCMAKE_EXPORT_COMPILE_COMMANDS=1',
        '.']
    vsdevcmd = os.path.join(get_vspath(), 'Common7', 'Tools', 'VsDevCmd')
    if os.path.exists(vsdevcmd):
        return subprocess.Popen([vsdevcmd, '&'], cmd, shell=True)
    return subprocess.Popen(cmd, shell=True)


def create_ctags(source_path):
    cmd = [
        'ctags',
        '--languages=c++',
        '--output-format=e-ctags']
    for path in source_path:
        cmd += ['-R', path]
    return subprocess.Popen(cmd, shell=True)


def get_param():
    path = os.path.join(os.path.expanduser('~'), 'ue4_project.json')
    with codecs.open(path, 'r', 'utf-8') as f:
        return json.load(f)


def get_engine_batch(path):
    return os.path.join(path, 'Engine', 'Build', 'BatchFiles', 'Build')


def get_uproject(dic):
    return os.path.join(dic['project_path'], dic['project'] + '.uproject')


def get_generate_project_file_bat():
    return 'GenerateProjectFiles.bat'


def get_vspath():
    vs14path = os.getenv('VS140COMNTOOLS')
    if vs14path:
        vs14path = os.path.dirname(os.path.dirname(os.path.dirname(vs14path)))
    try:
        proc = subprocess.check_output('vswhere', encoding='cp932')
    except FileNotFoundError:
        return vs14path
    prefix = 'installationPath: '
    vs15path = None
    for line in proc.split('\n'):
        if line.startswith(prefix):
            vs15path = line.replace(prefix, '')
            break
    if vs15path:
        return vs15path
    return vs14path


def main():
    for arg in sys.argv:
        if arg == '-build':
            build('Development')
        if arg == '-generate_project':
            generate_project()
        if arg == '-dumps':
            dumps()
        if arg == '-open_project':
            subprocess.call(get_uproject(get_param()), shell=True)
        vs_open_prefix = '-vs_open_file='
        if arg.startswith(vs_open_prefix):
            file_path = arg.replace(vs_open_prefix, '')
            subprocess.call([get_devenv(), '/edit', file_path], shell=True)
        if arg == '-open_sln':
            subprocess.call(get_sln_path(), shell=True)
        if arg == '-run_sln':
            subprocess.call([get_devenv(), '/r', get_sln_path()], shell=True)


if __name__ == '__main__':
    main()
