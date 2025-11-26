# Add this script to your powershell startup script to make the scripts and
# tools in this package accessible from any directory on your system.

# Get input arguments
param(
	[string]$ProjectPath,
	[bool]$Verbose
)

$GrafViewerScriptPath = Join-Path -Path $ProjectPath -ChildPath "src\graf\scripts\grafviewer.py"
function grafviewer {
	param(
		[Parameter(ValueFromRemainingArguments=$true)]
		[string[]]$args
	)
	
	python $GrafViewerScriptPath @args
}

$GrafScriptScriptPath = Join-Path -Path $ProjectPath -ChildPath "src\graf\scripts\grafscript.py"
function grafscript {
	param(
		[Parameter(ValueFromRemainingArguments=$true)]
		[string[]]$args
	)
	python $GrafScriptScriptPath @args
}

# Success message if requested
if ($Verbose){
	Write-Output "Added Graf at path:" $ProjectPath
}