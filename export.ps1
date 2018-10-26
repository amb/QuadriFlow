Remove-Item qf.zip
Copy-Item -Recurse addon quadriflow
7z a qf.zip quadriflow
Remove-Item -Recurse quadriflow
Remove-Item -Recurse "C:\Users\hyppa\AppData\Roaming\Blender Foundation\Blender\2.79\scripts\addons\quadriflow\*"
Copy-Item -Recurse addon\* "C:\Users\hyppa\AppData\Roaming\Blender Foundation\Blender\2.79\scripts\addons\quadriflow\"
Copy-Item qf.zip "E:\vm\transact"