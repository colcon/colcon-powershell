# generated from colcon_powershell/shell/template/prefix.ps1.em
@[if pkg_names]@

# function to source another script with conditional trace output
# first argument: the name of the script file
function colcon_prefix_source_powershell_script {
  param (
    $_colcon_prefix_source_powershell_script
  )
  # source script with conditional trace output
  if (Test-Path $_colcon_prefix_source_powershell_script) {
    if ($env:COLCON_TRACE) {
      echo ". '$_colcon_prefix_source_powershell_script'"
    }
    . "$_colcon_prefix_source_powershell_script"
  } else {
    if ($env:COLCON_TRACE) {
      echo "not found: '$_colcon_prefix_source_powershell_script'"
    }
  }
}


@[end if]@
@[for i, pkg_name in enumerate(pkg_names)]@
@[  if i == 0]@
# a powershell script is able to determine its own path
@[  end if]@
$env:COLCON_CURRENT_PREFIX=(Split-Path $PSCommandPath -Parent) + "@('' if merge_install else ('/' + pkg_name))"
colcon_prefix_source_powershell_script "$env:COLCON_CURRENT_PREFIX/share/@(pkg_name)/package.ps1"

@[end for]@
