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


def build():
    param = get_param()
    engine = param['engine_path']
    project_name = param['project']
    cmd = [
        get_engine_batch(engine),
        project_name + 'Editor',
        'Win64',
        'Development',
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
                    'filename': match[1].replace('\\', '/'),
                    'lnum': match[2],
                    'text': match[3],
                    'type': 'E'})
    if is_vim:
        vim.command(':let s:ue4_dumps = ' + str(logs))


def open_project():
    subprocess(get_uproject(get_param()), shell=True)


def generate_project():
    param = get_param()
    engine = param['engine_path']
    project = param['project_path']
    work_dir = engine
    generate_project_cmd = 'GenerateProject.bat'
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
    cmake_proc = create_compiler_commands(param['vs_common_path'])
    ctags_proc = create_ctags([
        os.path.join(engine, 'Engine', 'Source'),
        os.path.join(project, 'Source')])
    cmake_proc.wait()
    ctags_proc.wait()


def create_compiler_commands(vs_common_path):
    cmd = [
        os.path.join(vs_common_path, 'Common7', 'Tools', 'VsDevCmd'),
        '&',
        'cmake',
        '-G',
        'Ninja',
        '-DCMAKE_EXPORT_COMPILE_COMMANDS=1',
        '.']
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
    home = os.path.expanduser('~')
    path = os.path.join(home, 'ue4_project.json')
    return json.load(codecs.open(path, 'r', 'utf-8'))


def get_engine_batch(path):
    return os.path.join(path, 'Engine', 'Build', 'BatchFiles', 'Build')


def get_uproject(dic):
    return os.path.join(dic['project_path'], dic['project'] + '.uproject')


def main():
    if '-build' in sys.argv:
        build()
    if '-generate_project' in sys.argv:
        generate_project()
    if '-dumps' in sys.argv:
        dumps()
    if '-open_project' in sys.argv:
        open_project()


if __name__ == '__main__':
    main()
