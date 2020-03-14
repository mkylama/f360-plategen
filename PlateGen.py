# -*- coding: utf-8 -*-
#Author-MigiBacon
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

import math
import re
import ast
from html import unescape
import json
from . import kle


debug = False


# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

_u = 0
_cw = 0
_ch = 0
_f = 0
_s = {}


# Event handler for the commandCreated event.
class PlateGenCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        
        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.            
        inputs = cmd.commandInputs

        # Dropdown for switch type
        switchType = inputs.addDropDownCommandInput('switchType', 'Switch type', adsk.core.DropDownStyles.LabeledIconDropDownStyle);
        switchTypeItems = switchType.listItems
        switchTypeItems.add('Cherry MX', True, '')
        switchTypeItems.add('Alps', False, '')
        # switchTypeItems.add('Choc', False, '')

        # Dropdown for stabilizer type
        switchType = inputs.addDropDownCommandInput('stabilizerType', 'Stabilizer type', adsk.core.DropDownStyles.LabeledIconDropDownStyle);
        switchTypeItems = switchType.listItems
        switchTypeItems.add('MX', True, '')
        switchTypeItems.add('MX - Large cutouts', False, '')
        switchTypeItems.add('Costar', False, '')
        switchTypeItems.add('Alps - AEK', False, '')
        switchTypeItems.add('Alps - AT101', False, '')
        # switchTypeItems.add('Choc', False, '')

        # Slider to select radius between 0 to 2 mm 
        floatValueList = []
        for i in range(41):
            floatValueList.append(i/200)
        radius = inputs.addFloatSliderListCommandInput('cornerRadius', 
                                                       'Cutout fillets', 
                                                       'mm',
                                                       floatValueList)

        # Outline
        switchType = inputs.addDropDownCommandInput('outlineType', 'Outline', adsk.core.DropDownStyles.LabeledIconDropDownStyle);
        switchTypeItems = switchType.listItems
        switchTypeItems.add('Box (beta)', True, '')
        switchTypeItems.add('Around clusters (beta)', False, '')
        switchTypeItems.add('No', False, '')

        # KLE raw data
        rawDataDefault = ''
        if debug:
            # rawDataDefault = '[{x:0.25,a:7,w:1.25},""],[{y:-0.75,x:1.75,h:1.25},""],[{h:1.5},""],[{y:-0.25,x:1.25,w:1.25},""]'
            # rawDataDefault = '[{a:7},"","","","","","","","","","","","","",{w:2},""],[{w:1.5},"","","","","","","","","","","","","",{x:0.25,w:1.25,h:2,w2:1.5,h2:1,x2:-0.25},""],[{w:1.75},"","","","","","","","","","","","",""],[{w:1.25},"","","","","","","","","","","","",{w:2.75},""],[{w:1.25},"",{w:1.25},"",{w:1.25},"",{w:6.25},"",{w:1.25},"",{w:1.25},"",{w:1.25},"",{w:1.25},""]'
            # rawDataDefault = '[{a:7,w:2.75},"",{w:1.25},"",{w:2},"",{x:0.25,w:1.25,h:2,w2:1.5,h2:1,x2:-0.25},""],[{w:6.25},""]'
            # rawDataDefault = '[{y:0.5,x:4,a:7},""],[{r:15,y:-2,x:1,w:2},"1","3"],[{x:1},"4","5","6"],[{r:-15,rx:9,x:-4},"7",{w:2},"8"],[{x:-4},"10","11","12"]' # tilt test
            # rawDataDefault = '[{a:7},"",""],["",{x:1},""],[{x:1},"",""],[{r:30,rx:0.5,ry:2.5,y:-0.5,x:-0.5},""],[{r:45,rx:1.5,ry:1.5,y:-0.5,x:-0.5},""],[{r:60,rx:2.5,ry:0.5,y:-0.5,x:-0.5},""]' # 3x3
            rawDataDefault = '[{a:7},"",{x:7},""],[{x:4},""],[{r:15,y:-2,x:1,w:2},"1","3"],[{x:1},"4","5","6"],[{r:-15,rx:9,x:-4},"7",{w:2},"8"],[{x:-4},"10","11","12"]' # wings
            # rawDataDefault = '[{a:7},"",""],["",""]' # 2x2
        inputs.addTextBoxCommandInput('rawData', 'KLE raw data', rawDataDefault, 20, False)

        # Connect to the execute event.
        onExecute = PlateGenExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler for the execute event.
class PlateGenExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            inputs = eventArgs.command.commandInputs

            # Code to react to the event.
            app = adsk.core.Application.get()
            ui  = app.userInterface
            generate_plate(
                inputs.itemById('switchType').selectedItem.name,
                inputs.itemById('stabilizerType').selectedItem.name,
                inputs.itemById('cornerRadius').valueOne,
                unescape(inputs.itemById('rawData').text),
                inputs.itemById('outlineType').selectedItem.name
            )
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def generate_plate(switchType, stabilizerType, cornerRadius, rawData, generateOutline):
    global _u, _cw, _ch, _f, _s

    app = adsk.core.Application.get()
    ui  = app.userInterface

    _u = 19.05 / 10
    _f = cornerRadius
    if switchType == 'Alps':
        _cw = 15.5 / 10
        _ch = 12.8 / 10
    else:
        _cw = 14 / 10
        _ch = 14 / 10

    # Select dimension for correct stabilizer type
    if stabilizerType == 'Alps - AEK':
        _s = {
            'w': 2.67 / 10,
            'd2': 14 / 10,
            'd625': 41.86 / 10,
            'd7': 45.30 / 10,
            'h-': 9.085 / 10,
            'h+': -3.875 / 10
        }
    elif stabilizerType == 'Alps - AT101':
        _s = {
            'w': 2.67 / 10,
            'd2': 14 / 10,
            'd275': 20.5 / 10,
            'd625': 41.86 / 10,
            'd7': 45.30 / 10,
            'h-': 9.085 / 10,
            'h+': -3.875 / 10
        }
    elif stabilizerType == 'Costar':
        _s = {
            'w': 3.3 / 10,
            'd2': 11.938 / 10,
            'd625': 50 / 10,
            'd7': 57.15 / 10,
            'h-': 7.75 / 10,
            'h+': 6.45 / 10
        }
    elif stabilizerType == 'MX - Large cutouts':
        _s = {
            'w': 7 / 10,
            'd2': 11.938 / 10,
            'd625': 50 / 10,
            'd7': 57.15 / 10,
            'h-': 9 / 10,
            'h+': 6 / 10
        }
    else:
        _s = {
            'w': 6.75 / 10,
            'd2': 11.938 / 10,
            'd625': 50 / 10,
            'd7': 57.15 / 10,
            'h-': 8 / 10,
            'h+': 6 / 10
        }

    layout = layoutparser('['+rawData+']')

    # Create process dialog
    progressDialog = ui.createProgressDialog()
    progressDialog.cancelButtonText = 'Cancel'
    progressDialog.isBackgroundTranslucent = False
    progressDialog.isCancelButtonShown = True

    # Get active design
    design = app.activeProduct

    # Get the root component of the active design.
    rootComp = design.rootComponent

    # Create a new sketch on the xy plane.
    sketches = rootComp.sketches;
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.name = 'Plate'

    # Create drawing tools
    lines = sketch.sketchCurves.sketchLines;
    arcs = sketch.sketchCurves.sketchArcs;

    # draw single cutout and save it as collection
    draw_rect(sketch, lines, arcs, _u / 2, -_u / 2, _cw, _ch)
    coll = adsk.core.ObjectCollection.create()
    for crv in sketch.sketchCurves:
        coll.add(crv)

    # get keys from leayout
    keys = kle.deserialize(layout)

    # Initialize progress bar
    current = 0
    total = len(keys)
    progressDialog.show('PlateGen', 'Generating plate: %p%', 0, total, 1)

    x_min = 9999
    x_max = 0
    y_min = 9999
    y_max = 0

    # Iterate all the keys
    for key in keys:
        copy_cutout(sketch, coll, key)

        if max(key['width'], key['height']) >= 2:
            draw_stab(sketch, lines, arcs, key)

        if key['x'] + key['width'] > x_max:
            x_max = key['x'] + key['width']
        if key['y'] + key['height'] > y_max:
            y_max = key['y'] + key['height']


        if key['x'] < x_min:
            x_min = key['x']
        if key['y'] < y_min:
            y_min = key['y']

        # process dialog
        if progressDialog.wasCancelled:
            break
        current += 1
        progressDialog.progressValue = current

    # Delete model cutout
    for i in range(coll.count):
        coll.item(i).deleteMe()

    # Create Box outline
    if generateOutline.startswith('Box'):
        lines.addTwoPointRectangle(adsk.core.Point3D.create(x_min * _u, y_min * -_u), adsk.core.Point3D.create(x_max * _u, y_max * -_u, 0))


def layoutparser(layout):
    layout = layout.replace('\\\\', '')
    layout = layout.replace('\\\"', '')
    layout = layout.replace('\n', '')
    layout = re.sub(r'\".*?\"', '\"\"', layout)
    layout = re.sub(r'(\w+):', r'"\1":', layout)
    layout = layout.replace('true', 'True')
    layout = layout.replace('false', 'False')
    
    return ast.literal_eval(layout)


def draw_rect(sketch, lines, arcs, cx, cy, w, h):

    if _f > 0:
        rect = lines.addCenterPointRectangle(adsk.core.Point3D.create(cx, cy, 0), adsk.core.Point3D.create(cx + w / 2, cy + h / 2, 0))
        for i in range(4):
            arcs.addFillet(rect.item(i), rect.item(i).endSketchPoint.geometry, rect.item((i+1)%4), rect.item((i+1)%4).startSketchPoint.geometry, _f)
    else:
        rect = lines.addCenterPointRectangle(adsk.core.Point3D.create(cx, cy, 0), adsk.core.Point3D.create(cx + w / 2, cy + h / 2, 0))

    return rect


def draw_stab(sketch, lines, arcs, key):
    # calculate switch center 
    cx = (key['x'] + key['width'] / 2) * _u
    cy = (key['y'] + key['height'] / 2) * -_u

    # select correct stab size
    if max(key['width'], key['height']) >= 7 and 'd7' in _s:
        d = _s['d7']
    elif max(key['width'], key['height']) >= 6 and 'd625' in _s:
        d = _s['d625']
    elif max(key['width'], key['height']) >= 2.75 and 'd275' in _s:
        d = _s['d275']
    else:
        d = _s['d2']

    # shapes
    left = draw_rect(
        sketch, lines, arcs,
        cx + d,
        cy + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
        _s['w'],
        _s['h-'] + _s['h+']
    )

    right = draw_rect(
        sketch, lines, arcs,
        cx - d,
        cy + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
        _s['w'],
        _s['h-'] + _s['h+']
    )

    # make collection of created lines
    rcoll = adsk.core.ObjectCollection.create()

    for line in left:
        rcoll.add(line)

    for line in right:
        rcoll.add(line)

    # Stabilizer rotation
    if key['height'] > key['width']:
        rotate(sketch, rcoll, (key['x'] + key['width'] / 2) * _u, (key['y'] + key['height'] / 2) * -_u, 90)

    # Positional rotation
    if key['rotation_angle'] != 0:
        rotate(sketch, rcoll, key['rotation_x'] * _u, key['rotation_y'] * -_u, key['rotation_angle'])



def copy_cutout(sketch, coll, key):
    # copy and move cutout
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        (key['x'] + (key['width'] - 1) / 2) * _u,
        (key['y'] + (key['height'] - 1) / 2) * -_u,
        0
    )
    new = sketch.copy(coll, transform)

    # handle cutout rotation
    if key['height'] > key['width']:
        rotate(sketch, new, (key['x'] + key['width'] / 2) * _u, (key['y'] + key['height'] / 2) * -_u, 90)

    # handle positioning rotation
    if key['rotation_angle'] != 0:
        rotate(sketch, new, key['rotation_x'] * _u, key['rotation_y'] * -_u, key['rotation_angle'])


def rotate(sketch, coll, cx, cy, angle):
    rotate = adsk.core.Matrix3D.create()
    rotate.setToRotation(
        rad(angle),
        adsk.core.Vector3D.create(0, 0, 1),
        adsk.core.Point3D.create(
            cx,
            cy,
            0
        )
    )
    sketch.move(coll, rotate)


def rad(degree):
    return -degree*(math.pi/180)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        buttonPlateGen = cmdDefs.itemById('PlateGenButton')

        if buttonPlateGen:
            buttonPlateGen.deleteMe()
        
        # Create a button command definition.
        buttonPlateGen = cmdDefs.addButtonDefinition('PlateGenButton', 
                                                   'PlateGen', 
                                                   'Generate sketch from KLE raw data',
                                                   './resources')
        
        # Connect to the command created event.
        PlateGenCreated = PlateGenCreatedEventHandler()
        buttonPlateGen.commandCreated.add(PlateGenCreated)
        handlers.append(PlateGenCreated)
        
        # Get the Create panel in the model workspace. 
        panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        
        # Add the button to the bottom of the panel.
        panel.controls.addSeparator()
        buttonControl = panel.controls.addCommand(buttonPlateGen)

        # Make the button available in the panel.
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Clean up the UI.
        cmdDef = ui.commandDefinitions.itemById('PlateGenButton')
        if cmdDef:
            cmdDef.deleteMe()
            
        panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        cntrl = panel.controls.itemById('PlateGenButton')
        if cntrl:
            cntrl.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))