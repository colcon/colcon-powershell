# generated from colcon_powershell/shell/template/prefix.ps1.em

# This script extends the environment with all packages contained in this
# prefix path.
@[if pkg_names]@

# function to source another script with conditional trace output
# first argument: the path of the script
function _colcon_prefix_powershell_source_script {
  param (
    $_colcon_prefix_powershell_source_script_param
  )
  # source script with conditional trace output
  if (Test-Path $_colcon_prefix_powershell_source_script_param) {
    if ($env:COLCON_TRACE) {
      echo ". '$_colcon_prefix_powershell_source_script_param'"
    }
    . "$_colcon_prefix_powershell_source_script_param"
  } else {
    Write-Error "not found: '$_colcon_prefix_powershell_source_script_param'"
  }
}

# source packages
@[  for i, pkg_name in enumerate(pkg_names)]@
$env:COLCON_CURRENT_PREFIX=(Split-Path $PSCommandPath -Parent) + "@('' if merge_install else ('\\' + pkg_name))"
_colcon_prefix_powershell_source_script "$env:COLCON_CURRENT_PREFIX\share\@(pkg_name)\package.ps1"
@[    if i < len(pkg_names) - 1]@

@[    end if]@
@[  end for]@
@[end if]@
