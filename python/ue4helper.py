import json
import codecs
import os
import subprocess
import re


class UE4Helper:
    def build_project(self):
        param = self.get_param()
        engine = param['engine_path']
        project_name = param['project']
        cmd = [
            self.get_engine_batch(engine),
            project_name + 'Editor',
            'Win64',
            'Development',
            '-Project=' + self.get_uproject(param),
            '-WaitMutex',
            '-FromMsBuild']
        subprocess.call(cmd, shell=True)

    def get_errors(self):
        param = self.get_param()
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
        if not logs:
            return
        return str(logs)

    def generate_project(self):
        param = self.get_param()
        engine = param['engine_path']
        project = param['project_path']
        work_dir = engine
        generate_project_cmd = 'GenerateProject.bat'
        if not os.path.exists(os.path.join(engine, generate_project_cmd)):
            work_dir = project
            generate_project_cmd = [
                self.get_engine_batch(engine),
                '-projectfiles',
                '-project=' + self.get_uproject(param),
                '-game',
                '-rocket']
        os.chdir(work_dir)
        subprocess.call(generate_project_cmd, shell=True)
        subprocess.call(generate_project_cmd + ['-CMakefile'], shell=True)
        cmake_proc = self.create_compiler_commands(param['vs_common_path'])
        ctags_proc = self.create_ctags([
            os.path.join(engine, 'Engine', 'Source'),
            os.path.join(project, 'Source')])
        cmake_proc.wait()
        ctags_proc.wait()

    def create_compiler_commands(self, vs_common_path):
        cmd = [
            os.path.join(vs_common_path, 'Tools', 'VsDevCmd.bat'),
            '&',
            'cmake',
            '-G',
            'Ninja',
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=1',
            '.']
        return subprocess.Popen(cmd, shell=True)

    def create_ctags(self, source_path):
        cmd = [
            'ctags',
            '--languages=c++',
            '--output-format=e-ctags']
        for path in source_path:
            cmd += ['-R', path]
        return subprocess.Popen(cmd, shell=True)

    def get_param(self):
        return json.load(codecs.open('ue4_project.json', 'r', 'utf-8'))

    def get_engine_batch(self, path):
        return os.path.join(path, 'Engine', 'Build', 'BatchFiles', 'Build.bat')

    def get_uproject(self, dic):
        return os.path.join(dic['project_path'], dic['project'] + '.uproject')


def main():
    ue4helper = UE4Helper()
    # ue4helper.generate_project()
    # ue4helper.build_project()
    print(ue4helper.get_errors())


if __name__ == '__main__':
    main()
