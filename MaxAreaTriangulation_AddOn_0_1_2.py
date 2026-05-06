bl_info = {
    "name": "Max Area Triangulation",
    "blender": (4, 0, 0),
    "category": "Mesh",
    "description": "Fill a selected loop using Max Area Triangulation method",
    "author": "PatBom",
    "version": (0, 1, 2),
    "location": "View 3D > Sidebar > Edit Tab > Max Area Triangulation (panel)",
}

import bpy
import bmesh

class ObjectMaxAreaTriangulate(bpy.types.Operator):
    bl_idname = "object.max_area_triangulate"
    bl_label = "MAT"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def is_selected_loop():
            obj = bpy.context.edit_object
            if not obj: return False
            bm = bmesh.from_edit_mesh(obj.data)
            
            selected_verts = {v for v in bm.verts if v.select}
            if len(selected_verts) < 3:
                return False

            # Check neighboring verts
            for v in selected_verts:
                selected_neighbors = 0
                for e in v.link_edges:
                    if e.other_vert(v).select:
                        selected_neighbors += 1
                
                # Each wert should have 2 neighbors
                if selected_neighbors != 2:
                    return False
                    
            # Allow only one loop at a time to avoid confusion
            visited = set()
            start_v = next(iter(selected_verts))
            stack = [start_v]
            
            while stack:
                v = stack.pop()
                if v not in visited:
                    visited.add(v)
                    for e in v.link_edges:
                        neighbor = e.other_vert(v)
                        if neighbor.select and neighbor not in visited:
                            stack.append(neighbor)
            
            return len(visited) == len(selected_verts)
         
        def max_area_triangulation():
            obj = context.edit_object
            if not obj: return []
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            
            # Select verts and order into loop
            selected_verts = [v for v in bm.verts if v.select]
            if len(selected_verts) < 3: return []

            # Follow edges
            ordered_verts = []
            curr = selected_verts[0]
            prev = None
            
            for _ in range(len(selected_verts)):
                ordered_verts.append(curr)
                next_v = None
                for e in curr.link_edges:
                    v_other = e.other_vert(curr)
                    if v_other.select and v_other != prev:
                        next_v = v_other
                        break
                if next_v is None: break
                prev, curr = curr, next_v
            
            verts = ordered_verts
            indexes = []
            
            first_vert_idx = verts[0].index
            
            # Main loop for creating triangles
            while len(verts) >= 3:
                first_three = verts[:3]
                
                indexes.append(first_three[0].index)
                indexes.append(first_three[1].index)
                
                bmesh.ops.contextual_create(bm, geom=first_three)
                
                first_three[0].select = False
                first_three[1].select = False
                
                verts = [v for v in ordered_verts if v.select]

            if len(verts) > 0:
                for v in verts:
                    indexes.append(v.index)
                
                bm.verts.ensure_lookup_table()
                bm.verts[first_vert_idx].select = True
                
                final_verts = [v for v in bm.verts if v.select]
                if len(final_verts) >= 3:
                    bmesh.ops.contextual_create(bm, geom=final_verts)
            
            bmesh.update_edit_mesh(me)
            return indexes[::2]

        def update_selected_verts(triangulation_results):
            if not triangulation_results: return 0
            bm = bmesh.from_edit_mesh(context.edit_object.data)
            for v in bm.verts: v.select = False
            for idx in triangulation_results:
                if idx < len(bm.verts):
                    bm.verts[idx].select = True
            bmesh.update_edit_mesh(context.edit_object.data)
            return len(triangulation_results)

        if is_selected_loop():
            n = 3
            while n >= 3:
                res = max_area_triangulation()
                n = update_selected_verts(res)
                if not res: break
        else:
            print("Selected not a loop!")
        
        return {'FINISHED'}

class VIEW3D_PT_MAT_Panel(bpy.types.Panel):
    bl_label = "Max Area Triangulate"
    bl_idname = "VIEW3D_PT_mat_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"

    def draw(self, context):
        layout = self.layout
        layout.label(text="To use:")
        layout.label(text="Select a loop that can be made into an endcap.")
        layout.operator("object.max_area_triangulate", text="Triangulate")

classes = (ObjectMaxAreaTriangulate, VIEW3D_PT_MAT_Panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
