# Copyright 2026 The colcon-powershell contributors
# Licensed under the Apache License, Version 2.0

import asyncio

import colcon_core.shell
from colcon_powershell.shell import powershell


def test_command_environment_preserves_names_and_values(monkeypatch, tmp_path):
    async def check_output(cmd, **kwargs):
        delimiter = b'\0' if '`0' in cmd[-1] else b'\n'
        return delimiter.join([
            b'PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages',
            b'INPUT_TARGET-ROS1-DISTRO=',
            b'MULTILINE=first\nsecond',
        ]) + delimiter

    monkeypatch.setattr(colcon_core.shell, 'check_output', check_output)
    monkeypatch.setattr(powershell, 'POWERSHELL_EXECUTABLE', 'pwsh')

    extension = powershell.PowerShellExtension()
    extension._is_primary = True
    loop = asyncio.new_event_loop()
    try:
        env = loop.run_until_complete(extension.generate_command_environment(
            'test', tmp_path, {}))
    finally:
        loop.close()

    assert env['PYTHONPATH'] == \
        '/opt/ros/jazzy/lib/python3.12/site-packages'
    assert env['INPUT_TARGET-ROS1-DISTRO'] == ''
    assert env['MULTILINE'] == 'first\nsecond'
