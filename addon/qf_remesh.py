# Copyright 2018 Tommi Hyppänen, license: GNU General Public License v2.0

from . import qf

import numpy as np
import bpy
import bmesh
import random
import cProfile, pstats, io


def write_fast(ve, tr, qu):
    me = bpy.data.meshes.new("testmesh")

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
    
    # [::-1] makes normals consistent (from OpenVDB)
    v_out = np.concatenate((tr.ravel()[::-1], qu.ravel()[::-1]))

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


def safe_bincount(data, weights, dts, conn):
    bc = np.bincount(data, weights)
    dts[:len(bc)] += bc
    bc = np.bincount(data)
    conn[:len(bc)] += bc
    return (dts, conn)


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
            min=10, default=500)

    sharp = bpy.props.BoolProperty(
            name="Sharpness",
            description="Take into account sharp corners",
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

        print(nverts)
        print(ntris)
        print(nverts.shape, ntris.shape)
        print(nverts[0], ntris[0])
        print(max([len(i) for i in ntris]))

        new_mesh = qf.remesh(list(nverts), list(ntris))
        print("*** remesh complete ***")
        
        # print(type(new_mesh[0]), type(new_mesh[1]))

        # self.vert_1 = len(new_mesh[0])
        # self.face_1 = len(new_mesh[1])
   
        #remeshed = write_fast(np.array(new_mesh[0]), np.array(new_mesh[1]), [])
        #context.active_object.data = remeshed

        return {'FINISHED'}

    
    def draw(self, context):
        layout = self.layout
        col = layout.column()

        row = layout.row()
        row.prop(self, "voxel_size_def", expand=True, text="Island margin quality/performance")

        row = layout.row()
        col = row.column(align=True)
        if self.voxel_size_def == "relative":
            col.prop(self, "voxel_size_object")
        else:
            col.prop(self, "voxel_size_world")

        row = layout.row()
        col = row.column(align=True)
        col.prop(self, "isovalue")

        col.prop(self, "adaptivity")

        #row = layout.row()
        #row.prop(self, "filter_style", expand=True, text="Type of filter to be iterated on the voxels")
        #row = layout.row()
        row = layout.row()
        col = row.column(align=True)

        col.prop(self, "filter_iterations")
        col.prop(self, "filter_width")
        col.prop(self, "filter_sigma")

        row = layout.row()
        #row.prop(self, "only_quads")
        row.prop(self, "smooth")
        row.prop(self, "nearest")

        if hasattr(self, 'vert_0'):
            infotext = "Change: {:.2%}".format(self.vert_1/self.vert_0)
            row = layout.row()
            row.label(text=infotext)
            row = layout.row()
            row.label(text="Verts: {}, Polys: {}".format(self.vert_1, self.face_1))

            row = layout.row()
            row.label(text="Cache: {} voxels".format(self.grid.activeVoxelCount()))



