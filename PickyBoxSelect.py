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
newfaceindices = []
edgeindices = []
newedgeindices = []
vertindices = []
newvertindices = []

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


#press
def cacheselection():
    # cache start select mode, append existing selection to list
    if bpy.context.tool_settings.mesh_select_mode[2]:
        global selectModeAtStart
        selectModeAtStart = 2
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global faceindices
        faceindices = [f.index for f in current_object.data.polygons if f.select]
        bpy.ops.object.mode_set(mode='EDIT')
    
    elif bpy.context.tool_settings.mesh_select_mode[1]:
        global selectModeAtStart
        selectModeAtStart = 1
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global edgeindices
        edgeindices = [e.index for e in current_object.data.edges if e.select]
        bpy.ops.object.mode_set(mode='EDIT')
    
    elif bpy.context.tool_settings.mesh_select_mode[0]:
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global vertindices
        vertindices = [v.index for v in current_object.data.vertices if v.select]
        bpy.ops.object.mode_set(mode='EDIT')
                    
    return

def cachenewselection():
    global selectModeAtStart
    if selectModeAtStart == 2:
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global newfaceindices
        newfaceindices = [f.index for f in current_object.data.polygons if f.select]
        bpy.ops.object.mode_set(mode='EDIT')
    elif selectModeAtStart == 1:
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global newedgeindices
        newedgeindices = [e.index for e in current_object.data.edges if e.select]
        bpy.ops.object.mode_set(mode='EDIT')
    elif selectModeAtStart == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global newvertindices
        newvertindices = [v.index for v in current_object.data.vertices if v.select]
        bpy.ops.object.mode_set(mode='EDIT')


#release
def prepareendselection():
    # if not in vertex select mode switch to it and make a clean sweep
    if not bpy.context.tool_settings.mesh_select_mode[0]:
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.mesh.select_all(action='DESELECT')
    return
    
def endselection(middle):
    # switch to face select mode, select faces from face index list
    global selectModeAtStart
    if selectModeAtStart == 2:
        if middle:#if middle mouse cache selection and clean sweep again
            cachenewselection()
            bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global faceindices
        for fidx in faceindices:
            current_object.data.polygons[fidx].select = True
        if middle:
            for nfidx in newfaceindices:
                current_object.data.polygons[nfidx].select = False
        bpy.ops.object.mode_set(mode='EDIT')
        selectModeAtStart = 0

    # similarly if in edge select mode
    elif selectModeAtStart == 1:
        if middle:#if middle mouse cache selection and clean sweep again
            cachenewselection()
            bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global edgeindices
        for eidx in edgeindices:
            current_object.data.edges[eidx].select = True
        if middle:
            for neidx in newedgeindices:
                current_object.data.edges[neidx].select = False
        bpy.ops.object.mode_set(mode='EDIT')
        selectModeAtStart = 0

    # and even vert select mode
    elif selectModeAtStart == 0:
        if middle:
            cachenewselection()
            bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        current_object = bpy.context.active_object
        global vertindices
        for vidx in vertindices:
            current_object.data.vertices[vidx].select = True
        if middle:
            for nvidx in newvertindices:
                current_object.data.vertices[nvidx].select = False
        bpy.ops.object.mode_set(mode='EDIT')
        selectModeAtStart = 0
    return


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
                cacheselection()
                self.selecting = True
                self.min_x = event.mouse_region_x
                self.min_y = event.mouse_region_y

            if event.value == 'RELEASE': # end of selection
                prepareendselection()

                # we have to sort the coordinates before passing them to select_border()
                self.max_x = max(event.mouse_region_x, self.min_x)
                self.max_y = max(event.mouse_region_y, self.min_y)
                self.min_x = min(event.mouse_region_x, self.min_x)
                self.min_y = min(event.mouse_region_y, self.min_y)

                bpy.ops.view3d.select_border(gesture_mode=3, xmin=self.min_x, xmax=self.max_x, ymin=self.min_y, ymax=self.max_y, extend=True)
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

                endselection(False)
                return {'FINISHED'}

        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'PRESS':
                cacheselection()
                self.selecting = True
                self.min_x = event.mouse_region_x
                self.min_y = event.mouse_region_y

            if event.value == 'RELEASE': # end of selection
                bpy.ops.mesh.select_all(action='INVERT')
                prepareendselection()

                # we have to sort the coordinates before passing them to select_border()
                self.max_x = max(event.mouse_region_x, self.min_x)
                self.max_y = max(event.mouse_region_y, self.min_y)
                self.min_x = min(event.mouse_region_x, self.min_x)
                self.min_y = min(event.mouse_region_y, self.min_y)

                bpy.ops.view3d.select_border(gesture_mode=3, xmin=self.min_x, xmax=self.max_x, ymin=self.min_y, ymax=self.max_y, extend=True)
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

                endselection(True)
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
