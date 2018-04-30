# Copyright 2016-2018 Dirk Thomas
# Licensed under the Apache License, Version 2.0

from collections import OrderedDict
import os
from pathlib import Path
import shutil
import sys

from colcon_core.environment_variable import EnvironmentVariable
from colcon_core.plugin_system import satisfies_version
from colcon_core.plugin_system import SkipExtensionException
from colcon_core.shell import get_colcon_prefix_path
from colcon_core.shell import get_environment_variables
from colcon_core.shell import logger
from colcon_core.shell import ShellExtensionPoint
from colcon_core.shell.template import expand_template

"""Environment variable to override the CMake executable"""
POWERSHELL_COMMAND_ENVIRONMENT_VARIABLE = EnvironmentVariable(
    'POWERSHELL_COMMAND', 'The full path to the PowerShell executable')


def which_executable(environment_variable, executable_name):
    """
    Determine the path of an executable.

    An environment variable can be used to override the location instead of
    relying on searching the PATH.

    :param str environment_variable: The name of the environment variable
    :param str executable_name: The name of the executable
    :rtype: str
    """
    value = os.getenv(environment_variable)
    if value:
        return value
    return shutil.which(executable_name)


powershell_executable_name = \
    'PowerShell' if sys.platform == 'win32' else 'pwsh'
POWERSHELL_EXECUTABLE = which_executable(
    POWERSHELL_COMMAND_ENVIRONMENT_VARIABLE.name, powershell_executable_name)


class PowerShellExtension(ShellExtensionPoint):
    """Generate `.ps1` scripts to extend the environment."""

    # the priority needs to be higher than the extension for the sh shell
    # in order to take precedence for command environment generation
    PRIORITY = 300

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(ShellExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')

        # HACK heuristics to determine if the parent shell is PowerShell
        if sys.platform == 'win32':
            pathexts = os.environ.get('PATHEXT', '').lower().split(os.pathsep)
            self._is_primary = '.cpl' in pathexts
        else:
            self._is_primary = bool(os.environ.get('PSModulePath'))

    def create_prefix_script(
        self, prefix_path, pkg_names, merge_install
    ):  # noqa: D102
        prefix_env_path = prefix_path / 'local_setup.ps1'
        logger.info(
            "Creating prefix script '{prefix_env_path}'".format_map(locals()))
        expand_template(
            Path(__file__).parent / 'template' / 'prefix.ps1.em',
            prefix_env_path,
            {
                'pkg_names': pkg_names,
                'merge_install': merge_install,
                'package_script_no_ext': 'package',
            })

        prefix_chain_env_path = prefix_path / 'setup.ps1'
        logger.info(
            "Creating prefix chain script '%s'" % prefix_chain_env_path)
        expand_template(
            Path(__file__).parent / 'template' / 'prefix_chain.ps1.em',
            prefix_chain_env_path,
            {
                'colcon_prefix_path': get_colcon_prefix_path(skip=prefix_path),
                'prefix_script_no_ext': 'local_setup',
            })

    def create_package_script(
        self, prefix_path, pkg_name, hooks
    ):  # noqa: D102
        pkg_env_path = prefix_path / 'share' / pkg_name / 'package.ps1'
        logger.info(
            "Creating package script '{pkg_env_path}'".format_map(locals()))
        expand_template(
            Path(__file__).parent / 'template' / 'package.ps1.em',
            pkg_env_path,
            {
                'pkg_name': pkg_name,
                'hooks': list(filter(
                    lambda hook: str(hook[0]).endswith('.ps1'), hooks)),
            })

    def create_hook_prepend_value(
        self, env_hook_name, prefix_path, pkg_name, name, subdirectory,
    ):  # noqa: D102
        hook_path = prefix_path / 'share' / pkg_name / 'hook' / \
            ('%s.ps1' % env_hook_name)
        logger.info("Creating environment hook '%s'" % hook_path)
        expand_template(
            Path(__file__).parent / 'template' / 'hook_prepend_value.ps1.em',
            hook_path,
            {
                'name': name,
                'subdirectory': subdirectory,
            })
        return hook_path

    async def generate_command_environment(
        self, task_name, build_base, dependencies,
    ):  # noqa: D102
        global powershell_executable_name
        if not self._is_primary:
            raise SkipExtensionException('Not usable outside of PowerShell')

        hook_path = build_base / ('colcon_command_prefix_%s.ps1' % task_name)
        expand_template(
            Path(__file__).parent / 'template' / 'command_prefix.ps1.em',
            hook_path,
            {'dependencies': dependencies})

        # ensure that the referenced scripts exist
        missing = OrderedDict()
        for pkg_name, pkg_install_base in dependencies.items():
            pkg_script = Path(
                pkg_install_base) / 'share' / pkg_name / 'package.ps1'
            if not pkg_script.exists():
                missing[pkg_name] = str(pkg_script)
        if missing:
            raise RuntimeError(
                'Failed to find the following files:' +
                ''.join('\n- %s' % path for path in missing.values()) +
                '\nCheck that the following packages have been built:' +
                ''.join('\n- %s' % name for name in missing.keys()))

        cmd = [
            '.',
            str(hook_path),
            ';',
            '(Get-Item Env:).GetEnumerator()',
            '|',
            'ForEach-Object',
            '{ "$($_.Key)=$($_.Value)" }'
        ]
        if POWERSHELL_EXECUTABLE is None:
            raise RuntimeError(
                "Could not find '{powershell_executable_name}' executable"
                .format(powershell_executable_name=powershell_executable_name))
        cmd = [POWERSHELL_EXECUTABLE, '-Command', ' '.join(cmd)]
        env = await get_environment_variables(
            cmd, cwd=str(build_base), shell=False)

        # write environment variables to file for debugging
        env_path = build_base / \
            ('colcon_command_prefix_%s.ps1.env' % task_name)
        with env_path.open('w') as h:
            for key in sorted(env.keys()):
                value = env[key]
                h.write('{key}={value}\n'.format_map(locals()))

        return env
