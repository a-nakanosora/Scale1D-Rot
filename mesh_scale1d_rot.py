import bpy
import bgl
import bmesh
import bpy_extras
from mathutils import Vector, Matrix
import math

bl_info = {
    "name" : "Scale1D+Rot",
    "author" : "A Nakanosora",
    "version" : (0, 2, 8),
    "blender" : (2, 7, 0),
    "location" : "View 3D > Edit Mode > Tool Shelf > Tools Tab",
    "description" : "Scale1D+Rot",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Mesh"
}

ORIENTATION_NAME = 'Scale1D'

running = False

def region_2d_to_view_3d(context, pos2d, depth_location=None):
    region = context.region
    rv3d = context.space_data.region_3d
    vec3d = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, pos2d)

    if depth_location is None:
        vec, viewpoint = get_viewpoint_coordinate(context)
        depth_location = viewpoint + vec

    loc3d = bpy_extras.view3d_utils.region_2d_to_location_3d(region, rv3d, pos2d, depth_location)
    return vec3d, loc3d

def view_3d_to_region_2d(context, co, local_to_global=False):
    area = context.area
    if area.type != 'VIEW_3D':
        raise Exception('view_3d_to_region_2d Error: invalid context.')
    viewport = area.regions[4]

    if local_to_global:
        co_3d = context.edit_object.matrix_world * co
    else:
        co_3d = co
    co_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(viewport, area.spaces[0].region_3d, co)
    return co_2d

def get_viewpoint_coordinate(context):
    region = context.region
    rv3d = context.space_data.region_3d
    p2d = Vector((region.width/2, region.height/2))
    viewpoint = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, p2d)
    center_vec = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, p2d)
    return center_vec, viewpoint

def get_selected_vert_coords():
    obj = bpy.context.edit_object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    return [v.co.copy() for v in bm.verts if v.select]

def exist_all_key(keys, dict):
    for key in keys:
        if not key in dict:
            return False
    return True

def my_draw_handler3d(draw_context):
    if exist_all_key(['line_start', 'line_end', 'line_end2'], draw_context):
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        draw_line3d(draw_context.get('line_start'), draw_context.get('line_end2'), color=(.4,.4,.4,1), line_stipple=True)
        draw_line3d(draw_context.get('line_start'), draw_context.get('line_end'), line_stipple=True)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
    if exist_all_key(['p', 'u', 'v', 'radius'], draw_context):
        radius = draw_context['radius']
        p = draw_context['p']
        u = draw_context['u']
        v = draw_context['v']
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        draw_circle3d(p,u,v,radius)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

def draw_line3d(a,b, color=(0,0,0,1), line_stipple=False):
    if line_stipple:
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glLineStipple(1, 0xe73c)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glColor4f( color[0], color[1], color[2], color[3])
    bgl.glVertex3f(a[0], a[1], a[2])
    bgl.glVertex3f(b[0], b[1], b[2])
    bgl.glEnd()
    if line_stipple:
        bgl.glDisable(bgl.GL_LINE_STIPPLE)

def draw_circle3d(p,u,v, radius, half=False):
    bgl.glPointSize(1)
    bgl.glBegin(bgl.GL_LINE_STRIP);
    bgl.glColor4f(0,0,0,1)

    u = u.normalized()
    v = v.normalized()
    r = radius
    t=0
    last = math.pi*2 if not half else math.pi
    dt = last/40
    while t<last:
        q = p + r*math.cos(t)*u + r*math.sin(t)*v
        bgl.glVertex3f( q.x, q.y, q.z )
        t += dt
    t=last
    q = p + r*math.cos(t)*u + r*math.sin(t)*v

    bgl.glVertex3f( q.x, q.y, q.z )
    bgl.glEnd()

def calc_viewconstant_radius(context, pivot, mouse_r2d):
    def get_perpendicular_co(p,n,a):
        return p + (a-p).dot(n) * n
    pivot_r2d = view_3d_to_region_2d(context, pivot)
    pivot_r2d_epx = pivot_r2d + Vector((1, 0)) * 10
    vec_piv_epx, loc_piv_epx = region_2d_to_view_3d(context, pivot_r2d_epx)
    pivot_epx = get_perpendicular_co(loc_piv_epx, vec_piv_epx, pivot)
    pivot_epx = pivot + (pivot_epx - pivot).normalized()
    vec_m, loc_m = region_2d_to_view_3d(context, mouse_r2d)
    let_va, let_a = region_2d_to_view_3d(context, Vector((100, 100)))
    let_vb, let_b = region_2d_to_view_3d(context, Vector((100, 100+100)))
    let_a = get_perpendicular_co(let_a, let_va, pivot)
    let_b = get_perpendicular_co(let_b, let_vb, pivot)
    radius = (let_b - let_a).length
    return radius

class CustomPanelTest(bpy.types.Panel):
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_context = "mesh_edit"
    bl_category = "Tools"
    bl_label = "Scale1D"

    def draw(self, context):
        layout = self.layout
        layout.operator(OP_Scale1D.bl_idname, text=OP_Scale1D.bl_label)

        return

        col = layout.column(align=True)
        col.operator(OP_Scale1D.bl_idname, text="Scale1D+Rot")

        layout.label(text="")

class DynamicMemberSetAssistantMixin:
    def __init__(self):
        self.__member_dict__ = {}
    def clean_allv(self):
        for name in self.__member_dict__:
            del self.__dict__[name]
            del self.__member_dict__[name]

    def cleanv(self, name):
        if not name in self.__member_dict__:
            raise Exception('MemberSetterMixin2 Error: cleanv no member: '+name)
        del self.__dict__[name]
        del self.__member_dict__[name]

    def initv(self, name, value):
        if name in self.__member_dict__:
            raise Exception('MemberSetterMixin2 Error: the member is already set: '+name)
        self.__dict__[name] = value
        self.__member_dict__[name] = True

    def updatev(self, name, value):
        if not name in self.__member_dict__:
            raise Exception('MemberSetterMixin2 Error: no init member: '+name)
        self.__dict__[name] = value

    def existv(self, name):
        return name in self.__dict__

class OP_Scale1D(bpy.types.Operator, DynamicMemberSetAssistantMixin):
    bl_idname = "transform.scale1d_rot"
    bl_label = "Scale1D+Rot"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global running

        if context.mode != 'EDIT_MESH' or len( get_selected_vert_coords() )==0:
            return {'CANCELLED'}

        if context.area.type == 'VIEW_3D':
            if running is False:
                running = True

                self.clean_allv()

                self.pre_modal_start(context, event)
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        return {'CANCELLED'}

    def modal(self, context, event):
        global running
        if running is False:
            return {'PASS_THROUGH'}

        try:
            if event.type == 'MOUSEMOVE':
                self.modal_loop_main(context, event)
                return {'RUNNING_MODAL'}
            elif event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    self.modal_loop_main(context, event)
                    self.on_modal_exit(context)
                    return {'FINISHED'}
            if event.type == 'RIGHTMOUSE':
                if event.value == 'PRESS':
                    self.modal_loop_main(context, event)
                    self.restore_vert_coords(context)
                    self.on_modal_exit(context)
                    return {'FINISHED'}

            return {'RUNNING_MODAL'}
        except:
            self.report({'WARNING'}, 'An error occurs.')
            print('Error in modal:')
            import sys
            print( sys.exc_info() )
            trb = sys.exc_info()[2]
            import traceback
            traceback.print_tb(trb)
            self.on_modal_exit(context)
            return {'FINISHED'}

    def reset_direction(self, context, event):
        first_vert_coords2 = []
        bm = bmesh.from_edit_mesh(context.edit_object.data)
        for i,v in enumerate( bm.verts ):
            if v.select:
                first_vert_coords2.append( (i, v.co.copy()) )
        self.initv('first_vert_coords2', first_vert_coords2)
        self.initv('first_all_vert_length', len(bm.verts) )

        vs = context.edit_object.data.vertices
        base_coords = [0]*len(vs)*3
        vs.foreach_get('co', base_coords)
        self.initv('base_coords', base_coords )

        def get_pivot(context):
            sel_coords = get_selected_vert_coords()
            return sum(sel_coords, Vector()) / len(sel_coords)

        pivot = context.object.matrix_world * get_pivot(context)
        base_mouse_r2d = Vector((event.mouse_region_x, event.mouse_region_y))
        self.initv('base_pivot', pivot)
        self.initv('base_mouse_r2d', base_mouse_r2d)
        self.initv('n_x', None)
        self.initv('n_y', None)
        self.initv('n_z', None)
        self.reset_angle(context, event, pivot)

    def reset_angle(self, context, event, pivot):
        pivot_r2d = view_3d_to_region_2d(context, pivot)

        mouse_r2d = Vector((event.mouse_region_x, event.mouse_region_y))
        base_mouse_r2d_new = pivot_r2d + (mouse_r2d - pivot_r2d).normalized() * (pivot_r2d - self.base_mouse_r2d).length

        vec_pivot, pivot_reset = region_2d_to_view_3d( context, pivot_r2d )
        vec_mouse_view3d, mouse_view3d = region_2d_to_view_3d( context, base_mouse_r2d_new )

        n_x = (mouse_view3d - pivot_reset).normalized()
        n_z = vec_pivot.normalized()
        n_y = n_z.cross(n_x)

        self.updatev('base_mouse_r2d', base_mouse_r2d_new)
        self.updatev('n_x', n_x)
        self.updatev('n_y', n_y)
        self.updatev('n_z', n_z)
        self.reset_orientation(context)

    def reset_orientation(self, context):
        bpy.ops.transform.create_orientation(name = ORIENTATION_NAME, overwrite = True)
        bpy.context.scene.orientations[ORIENTATION_NAME].matrix = (self.n_x, self.n_y, self.n_z)
        context.area.spaces[0].transform_orientation = ORIENTATION_NAME

    def pre_modal_start(self, context, event):
        self.prev_orientation = context.area.spaces[0].transform_orientation
        self.reset_direction(context, event)
        self.initv('draw_context', {})

        my_draw_handler_handle3d = bpy.types.SpaceView3D.draw_handler_add(my_draw_handler3d, (self.draw_context,), 'WINDOW', 'POST_VIEW')
        self.initv('my_draw_handler_handle3d', my_draw_handler_handle3d )

        self.initv('user_setting__use_mesh_automerge', context.scene.tool_settings.use_mesh_automerge)
        context.scene.tool_settings.use_mesh_automerge = False

    def on_modal_exit(self, context):
        global running
        running = False
        context.area.spaces[0].transform_orientation = self.prev_orientation
        self.cleanv('first_vert_coords2')

        bpy.types.SpaceView3D.draw_handler_remove(self.my_draw_handler_handle3d, 'WINDOW')
        self.cleanv('my_draw_handler_handle3d')

        context.scene.tool_settings.use_mesh_automerge = self.user_setting__use_mesh_automerge
        self.cleanv('user_setting__use_mesh_automerge')

    def restore_vert_coords(self, context):
        bm = bmesh.from_edit_mesh(context.edit_object.data)
        vs = bm.verts
        for i, co in self.first_vert_coords2:
            vs[i].co = co.copy()

    def modal_loop_main(self, context, event):
        no_rotate_mode = False
        reset_angle_mode = False
        if event.alt:
            reset_angle_mode = True
            no_rotate_mode = True
        if event.shift:
            no_rotate_mode = True
            pass
        if event.ctrl:
            pass

        if len( bmesh.from_edit_mesh(context.edit_object.data).verts) != self.first_all_vert_length:
            raise Exception('verts length mismatch.')

        if reset_angle_mode:
            self.reset_angle(context, event, self.base_pivot)

        base_mouse_r2d = self.base_mouse_r2d
        base_pivot_r2d = view_3d_to_region_2d(context, self.base_pivot)
        mouse_r2d = Vector((event.mouse_region_x, event.mouse_region_y))
        val = (mouse_r2d - base_pivot_r2d).length / (base_mouse_r2d - base_pivot_r2d).length

        self.restore_vert_coords(context)

        bpy.ops.transform.resize(value=(val,1,1), constraint_orientation=ORIENTATION_NAME, constraint_axis=(True, False, False))

        vec_pivot, pivot_reset = region_2d_to_view_3d(context, base_pivot_r2d)
        vec_mouse_view3d, mouse_view3d = region_2d_to_view_3d(context, mouse_r2d)
        if not no_rotate_mode:
            t = (mouse_view3d - pivot_reset).normalized()
            tx = self.n_x.dot(t)
            ty = self.n_y.dot(t)
            rot_val = math.atan2(ty, tx)
            bpy.ops.transform.rotate(value=rot_val, axis=self.n_z)

        p = self.base_pivot.copy()
        radius = calc_viewconstant_radius(context, p, mouse_r2d)

        _, base_mouse_view3d = region_2d_to_view_3d(context, base_mouse_r2d, p)
        self.draw_context['line_start'] = p
        if not no_rotate_mode:
            self.draw_context['line_end'] = mouse_view3d
        else:
            temp_mouse_r2d = base_pivot_r2d + (base_mouse_r2d - base_pivot_r2d).normalized() * (mouse_r2d - base_pivot_r2d).length
            _, temp_mouse_view3d = region_2d_to_view_3d(context, temp_mouse_r2d, p)
            self.draw_context['line_end'] = temp_mouse_view3d
        self.draw_context['line_end2'] = p + (base_mouse_view3d - p).normalized() * radius
        self.draw_context['p'] = p
        u = (base_mouse_view3d - p).normalized()
        self.draw_context['u'] = u
        self.draw_context['v'] = vec_pivot.normalized().cross(u)
        self.draw_context['radius'] = radius

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()