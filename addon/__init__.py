# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, version 3 of the license.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Quadriflow",
    "category": "Mesh",
    "description": "Quadriflow remesh",
    "author": "ambi",
    "location": "3D view > Tools > Retopology",
    "version": (1, 0, 0),
    "blender": (2, 79, 0)
}


# import/reload all source files
if "bpy" in locals():
    import importlib
    importlib.reload(qf_remesh)
    importlib.reload(qf)
else:
    from . import qf_remesh
    from . import qf

import bpy


def register():
    bpy.types.Scene.qf_polys = bpy.props.IntProperty(name="Polycount", default=1000, min=10, max=1000000)
    bpy.utils.register_class(qf_remesh.QFRemeshOperator)
    bpy.utils.register_class(qf_remesh.QFRemeshPanel)

def unregister():
    bpy.utils.unregister_class(qf_remesh.QFRemeshOperator)
    bpy.utils.unregister_class(qf_remesh.QFRemeshPanel)
    del bpy.types.Scene.qf_polys
