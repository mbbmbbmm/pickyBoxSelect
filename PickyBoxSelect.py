### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Basis code for border selection by Chebhou!

bl_info = {
    "name": "Picky Box Select",  
    "author": "Jan Ahrens (mbbmbbmm)",
    "version": (0, 0, 1),
    "blender": (2, 77, 0),
    "location": "Space Bar Menu, or assign hotkey for 'mesh.picky_box_select'",
    "description": "Invoke a border selection that selects edges or faces if all their vertices are within the border",
    "wiki_url" : "",
    "category": "Mesh"}



import bpy
import bgl
from mathutils import Vector
from bpy.props import IntProperty, BoolProperty

selectModeAtStart = 0
faceindices = []
edgeindices = []

def draw_callback_px(self, context):

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    bgl.glLineWidth(2)

    if self.selecting :
        # when selecting draw dashed line box
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glLineStipple(2, 0x3333)
        bgl.glBegin(bgl.GL_LINE_LOOP)

        bgl.glVertex2i(self.min_x, self.min_y)
        bgl.glVertex2i(self.min_x, self.max_y)
        bgl.glVertex2i(self.max_x, self.max_y)
        bgl.glVertex2i(self.max_x, self.min_y)

        bgl.glEnd()

        bgl.glDisable(bgl.GL_LINE_STIPPLE)
    else :
        # before selection starts draw infinite cross
        bgl.glBegin(bgl.GL_LINES)

        bgl.glVertex2i(0, self.max_y)
        bgl.glVertex2i(context.area.width, self.max_y)        

        bgl.glVertex2i(self.max_x, 0)
        bgl.glVertex2i(self.max_x, context.area.height)

        bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class SelectOperator(bpy.types.Operator):
    """picky box selection """
    bl_idname = "mesh.picky_box_select"
    bl_label = "Picky Box Select"
    bl_options = {'REGISTER', 'UNDO'}

    min_x = IntProperty(default = 0)
    min_y = IntProperty(default = 0)
    max_x = IntProperty()
    max_y = IntProperty()

    selecting = BoolProperty(default = False) # just for drawing in bgl
    

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE': # just for drawing the box
            self.max_x = event.mouse_region_x
            self.max_y = event.mouse_region_y

        elif event.type == 'LEFTMOUSE':
            if event.value == 'PRESS': # start selection
                
                # cache start select mode, append existing selection to list, deselect all, switch to vert select mode
                if bpy.context.tool_settings.mesh_select_mode[2]:
                    global selectModeAtStart
                    selectModeAtStart= 2
                    bpy.ops.object.mode_set(mode='OBJECT')
                    current_object = bpy.context.active_object
                    global faceindices
                    faceindices = [f.index for f in current_object.data.polygons if f.select]
                    bpy.ops.object.mode_set(mode='EDIT')
                
                if bpy.context.tool_settings.mesh_select_mode[1]:
                    global selectModeAtStart
                    selectModeAtStart= 1
                    bpy.ops.object.mode_set(mode='OBJECT')
                    current_object = bpy.context.active_object
                    global edgeindices
                    edgeindices = [e.index for e in current_object.data.edges if e.select]
                    bpy.ops.object.mode_set(mode='EDIT')
                                
                self.selecting = True
                self.min_x = event.mouse_region_x
                self.min_y = event.mouse_region_y

            if event.value == 'RELEASE': # end of selection
                # if not in vertex select mode switch to it and make a clean sweep
                if not bpy.context.tool_settings.mesh_select_mode[0]:
                    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                    bpy.ops.mesh.select_all(action='DESELECT')
                
                # we have to sort the coordinates before passing them to select_border()
                self.max_x = max(event.mouse_region_x, self.min_x)
                self.max_y = max(event.mouse_region_y, self.min_y)
                self.min_x = min(event.mouse_region_x, self.min_x)
                self.min_y = min(event.mouse_region_y, self.min_y)

                bpy.ops.view3d.select_border(gesture_mode=3, xmin=self.min_x, xmax=self.max_x, ymin=self.min_y, ymax=self.max_y, extend=True)
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                
                # switch to face select mode, select faces aus face index list
                if selectModeAtStart == 2:
                    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    current_object = bpy.context.active_object
        
                    for fidx in faceindices:
                        current_object.data.polygons[fidx].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    selectModeAtStart = 0
                        
                    
                # same for edge select mode
                if selectModeAtStart == 1:
                    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    current_object = bpy.context.active_object
        
                    for eidx in edgeindices:
                        current_object.data.edges[eidx].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    selectModeAtStart = 0
                                
                return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        if context.space_data.type == 'VIEW_3D' and context.active_object.mode == 'EDIT':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d, mode must be Edit Mode!")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(SelectOperator)


def unregister():
    bpy.utils.unregister_class(SelectOperator)


if __name__ == "__main__":
    register()
