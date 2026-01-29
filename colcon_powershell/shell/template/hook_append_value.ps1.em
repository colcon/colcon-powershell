# generated from colcon_powershell/shell/template/hook_append_value.ps1.em

@{
import os
value = '$env:COLCON_CURRENT_PREFIX'
if subdirectory:
    value += os.sep + subdirectory
}@
colcon_append_unique_value @(name) "@(value)"
