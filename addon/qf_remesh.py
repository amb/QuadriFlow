# Copyright 2018 Tommi Hyppänen, license: GNU General Public License v2.0

from . import qf

import numpy as np
import bpy
import bmesh
import random
import cProfile, pstats, io


def write_fast(ve, qu):
    me = bpy.data.meshes.new("testmesh")

    tr = np.array([])
    quadcount = len(qu)
    tricount  = len(tr)

    me.vertices.add(count=len(ve))

    loopcount = quadcount * 4 + tricount * 3
    facecount = quadcount + tricount
    
    me.loops.add(loopcount)
    me.polygons.add(facecount)

    face_lengths = np.zeros(facecount, dtype=np.int)
    face_lengths[:tricount] = 3
    face_lengths[tricount:] = 4

    loops = np.concatenate((np.arange(tricount) * 3, np.arange(quadcount) * 4 + tricount * 3))
    
    v_out = np.concatenate((tr.ravel(), qu.ravel()))

    me.vertices.foreach_set("co", ve.ravel())
    me.polygons.foreach_set("loop_total", face_lengths)
    me.polygons.foreach_set("loop_start", loops)
    me.polygons.foreach_set("vertices", v_out)
    
    me.update(calc_edges=True)
    #me.validate(verbose=True)

    return me


def read_loops(mesh):
    loops = np.zeros((len(mesh.polygons)), dtype=np.int)
    mesh.polygons.foreach_get("loop_total", loops)
    return loops 


def read_bmesh(bmesh):
    bmesh.verts.ensure_lookup_table()
    bmesh.faces.ensure_lookup_table()

    verts = [(i.co[0], i.co[1], i.co[2]) for i in bmesh.verts]
    qu, tr = [], []
    for f in bmesh.faces:
        if len(f.verts) == 4:        
            qu.append([])
            for v in f.verts:
                qu[-1].append(v.index)
        if len(f.verts) == 3:        
            tr.append([])
            for v in f.verts:
                tr[-1].append(v.index)

    return (np.array(verts), np.array(tr), np.array(qu))


class QFRemeshOperator(bpy.types.Operator):
    """Quadriflow Remesh"""
    bl_idname = "object.quadriflow_operator"
    bl_label = "Quadriflow remesh"
    bl_options = {'REGISTER', 'UNDO'}

    polycount = bpy.props.IntProperty(
            name="Polygons",
            description="Output mesh polygon count",
            min=10, default=1000)

    sharp = bpy.props.BoolProperty(
            name="Sharp",
            description="Take into account sharp corners",
            default=False)

    adaptive = bpy.props.BoolProperty(
            name="Adaptive",
            description="Adaptive scale",
            default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # apply modifiers for the active object before remeshing
        for mod in context.active_object.modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except RuntimeError as ex:
                b_print(ex)     

        # start remesh
        me = context.active_object.data
            
        bm = bmesh.new()
        bm.from_mesh(me)

        if len(bm.faces) == 0:
            pass

        loops = read_loops(me)
        if np.max(loops) >= 4:
            # Mesh has ngons/quads! Triangulate ...
            print("Triangulating...")
            bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

        nverts, ntris, nquads = read_bmesh(bm)
        self.vert_0 = len(nverts)
        bm.free()

        print(max([len(i) for i in ntris]))

        nverts = nverts.transpose()
        ntris = ntris.transpose()
        print(nverts.shape, ntris.shape)

        new_mesh = qf.remesh(list(nverts), list(ntris), self.polycount, self.sharp, self.adaptive)
        print("*** remesh complete ***")
        
        print(type(new_mesh[0]), type(new_mesh[1]))

        print(new_mesh[0][0], new_mesh[1][0])
        print(new_mesh[0][0].shape, new_mesh[1][0].shape)

        self.vert_1 = len(new_mesh[0])
        self.face_1 = len(new_mesh[1])

        print(self.vert_1, self.face_1)

        remeshed = write_fast(np.array(new_mesh[0]), np.array(new_mesh[1]))
        context.active_object.data = remeshed

        return {'FINISHED'}


class QFRemeshPanel(bpy.types.Panel):
    """Quadriflow Remesh panel"""
    bl_label = "Quadriflow remesh"
    bl_idname = "object.qfremesh_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Retopology"

    def draw(self, context):
        layout = self.layout

        """
        row = layout.row()
        row.prop(context.scene, "vdb_remesh_voxel_size_def", expand=True, text="Island margin quality/performance")

        row = layout.row()
        col = row.column(align=True)
        if context.scene.vdb_remesh_voxel_size_def == "relative":
            col.prop(context.scene, "vdb_remesh_voxel_size_object")
        else:
            col.prop(context.scene, "vdb_remesh_voxel_size_world")

        col.prop(context.scene, "vdb_remesh_isovalue")
        col.prop(context.scene, "vdb_remesh_adaptivity")
        col.prop(context.scene, "vdb_remesh_blur")

        row = layout.row()
        row.prop(context.scene, "vdb_remesh_only_quads")
        row.prop(context.scene, "vdb_remesh_smooth")
        row.prop(context.scene, "vdb_remesh_project_nearest")
        """

        row = layout.row()
        row.scale_y = 2.0
        row.operator(QFRemeshOperator.bl_idname, text="Quadriflow remesh")




