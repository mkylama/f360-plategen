#Author-MigiBacon
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

import math
import re
import ast
from html import unescape


debug = False


# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

_u = 0
_cw = 0
_ch = 0
_r = 0
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
        switchTypeItems.add('Alps - AEK', False, '')
        switchTypeItems.add('Alps - AT101', False, '')
        # switchTypeItems.add('Choc', False, '')

        # Slider to select radius between 0 to 2 mm 
        floatValueList = []
        for i in range(41):
            floatValueList.append(i/200)
        radius = inputs.addFloatSliderListCommandInput('cornerRadius', 
                                                       'Corner radius', 
                                                       'mm',
                                                       floatValueList)

        # KLE raw data
        rawDataDefault = ''
        if debug:
            rawDataDefault = '[{x:0.25,a:7,w:1.25},""],[{y:-0.75,x:1.75,h:1.25},""],[{h:1.5},""],[{y:-0.25,x:1.25,w:1.25},""]'
            rawDataDefault = '[{a:7},"",{x:1},"","","","",{x:0.5},"","","","",{x:0.5},"","","","",{x:1.5},"","","",""],[{y:0.5},"","","","","","","","","","","","","",{w:2},"",{x:0.25},"",{x:0.25},"","","",""],[{w:1.5},"","","","","","","","","","","","","",{x:0.25,w:1.25,h:2,w2:1.5,h2:1,x2:-0.25},"",{x:0.25},"",{x:0.25},"","","",{h:2},""],[{w:1.75},"","","","","","","","","","","","","",{x:2.75},"","",""],[{w:1.25},"","","","","","","","","","","","",{w:2.75},"",{x:1.5},"","","",{h:2},""],[{y:-0.75,x:15.25},""],[{y:-0.25,w:1.5},"","",{w:1.5},"",{w:7},"",{w:1.5},"",{w:1.5},"",{x:3.5},"",""],[{y:-0.75,x:14.25},"","",""]'
            rawDataDefault = '[{a:7,w:2.75},"",{w:1.25},"",{w:2},"",{x:0.25,w:1.25,h:2,w2:1.5,h2:1,x2:-0.25},""],[{w:6.25},""]'
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
                unescape(inputs.itemById('rawData').text)
            )
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def generate_plate(switchType, stabilizerType, cornerRadius, rawData):
    global _u, _cw, _ch, _r, _s

    app = adsk.core.Application.get()
    ui  = app.userInterface

    _u = 19.05 / 10
    _r = cornerRadius
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
    total = 0
    current = 0

    for row in layout:
        total += len(row)

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

    lines = sketch.sketchCurves.sketchLines;
    arcs = sketch.sketchCurves.sketchArcs;

    x = 0
    y = 0
    w = 1
    h = 1

    x_max = 0

    progressDialog.show('PlateGen', 'Generating plate: %p%', 0, total, 1)

    # draw single cutout and save it as collection
    draw_rect(lines, arcs, _u / 2, -_u / 2, _cw, _ch)
    coll = adsk.core.ObjectCollection.create()
    for crv in sketch.sketchCurves:
        coll.add(crv)

    for row in layout:
        for item in row:
            if isinstance(item, str):
                copy_cutout(sketch, coll, x, y, w, h)
                if w >= 2 or h >= 2:
                    draw_stab(lines, arcs, x, y, h, w)
                x += w
                w = 1
                h = 1
            elif isinstance(item, dict):
                if 'x' in item:
                    x += item['x']
                if 'y' in item:
                    y -= item['y']
                if 'w' in item:
                    w = item['w']
                if 'h' in item:
                    h = item['h']

            current += 1
            progressDialog.progressValue = current
        if x > x_max:
            x_max = x
        x = 0
        y -= 1

    # Delete model cutout
    for i in range(coll.count):
        coll.item(i).deleteMe()

    # Create outline
    lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(x_max * _u, y * _u, 0))



def layoutparser(layout):
    layout = re.sub(r'(\w+):', r'"\1":', layout)
    layout = layout.replace('true', 'True')
    layout = layout.replace('false', 'False')


    return ast.literal_eval(layout)


def draw_rect(lines, arcs, cx, cy, w, h):
    angle = 90*(math.pi/180)

    if _r > 0:
        rect = lines.addCenterPointRectangle(adsk.core.Point3D.create(cx, cy, 0), adsk.core.Point3D.create(cx + w / 2, cy + h / 2, 0))
        for i in range(4):
            arcs.addFillet(rect.item(i), rect.item(i).endSketchPoint.geometry, rect.item((i+1)%4), rect.item((i+1)%4).startSketchPoint.geometry, _r)
    else:
        lines.addCenterPointRectangle(adsk.core.Point3D.create(cx, cy, 0), adsk.core.Point3D.create(cx + w / 2, cy + h / 2, 0))


def draw_stab(lines, arcs, x, y, h, w):
    # calculate switch center 
    cx = x * _u + (w - 1) * _u / 2 + _u / 2
    cy = y * _u - _u / 2 - (h - 1) * _u / 2

    # select correct stab size
    if (h >= 7 or w >= 7) and 'd7' in _s:
        d = _s['d7']
    elif (h >= 6 or w >= 6) and 'd625' in _s:
        d = _s['d625']
    elif (h >= 2.75 or w >= 2.75) and 'd275' in _s:
        d = _s['d275']
    else:
        d = _s['d2']

    if h > w:
        draw_rect(
            lines,
            arcs,
            cx + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
            cy + d,
            _s['h-'] + _s['h+'],
            _s['w']
        )
        draw_rect(
            lines,
            arcs,
            cx + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
            cy - d,
            _s['h-'] + _s['h+'],
            _s['w']
        )
    else:
        draw_rect(
            lines,
            arcs,
            cx + d,
            cy + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
            _s['w'],
            _s['h-'] + _s['h+']
        )
        draw_rect(
            lines,
            arcs,
            cx - d,
            cy + _s['h+'] - (_s['h+'] + _s['h-']) / 2,
            _s['w'],
            _s['h-'] + _s['h+']
        )


def copy_cutout(sketch, coll, x, y, w, h,):
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(x * _u + (w - 1) * _u / 2, y * _u - (h - 1) * _u / 2, 0)
    new = sketch.copy(coll, transform)
    if h > w and _cw != _ch:
        rotX = adsk.core.Matrix3D.create()
        rotX.setToRotation(90*(math.pi/180), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(x * _u + (w - 1) * _u / 2 + _u / 2, y * _u - (h - 1) * _u / 2 - _u / 2, 0))
        transform.transformBy(rotX)
        sketch.move(new, rotX)


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