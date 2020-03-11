#Author-MigiBacon
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

import math
import re
import ast

def layoutparser(layout):
    layout = re.sub(r'(\w+):', r'"\1":', layout)

    return ast.literal_eval(layout)

def draw_rect(lines, arcs, x, y, w, h, u, r=0):
    cx = x * u + w * u / 2
    cy = (y - h + 1) * u + h * u / 2

    angle = 90*(math.pi/180)

    if r > 0:
        # lines.addByTwoPoints(adsk.core.Point3D.create(cx - 7 + r, cy - 7, 0), adsk.core.Point3D.create(cx + 7 - r, cy - 7, 0))
        # lines.addByTwoPoints(adsk.core.Point3D.create(cx - 7 + r, cy + 7, 0), adsk.core.Point3D.create(cx + 7 - r, cy + 7, 0))
        # lines.addByTwoPoints(adsk.core.Point3D.create(cx - 7, cy - 7 + r, 0), adsk.core.Point3D.create(cx - 7, cy + 7 - r, 0))
        # lines.addByTwoPoints(adsk.core.Point3D.create(cx + 7, cy - 7 + r, 0), adsk.core.Point3D.create(cx + 7, cy + 7 - r, 0))

        # arcs.addByCenterStartSweep(adsk.core.Point3D.create(cx - 7 + r, cy - 7 + r, 0), adsk.core.Point3D.create(cx - 7, cy - 7 + r, 0), angle)
        # arcs.addByCenterStartSweep(adsk.core.Point3D.create(cx - 7 + r, cy + 7 - r, 0), adsk.core.Point3D.create(cx - 7 + r, cy + 7, 0), angle)
        # arcs.addByCenterStartSweep(adsk.core.Point3D.create(cx + 7 - r, cy - 7 + r, 0), adsk.core.Point3D.create(cx + 7 - r, cy - 7, 0), angle)
        # arcs.addByCenterStartSweep(adsk.core.Point3D.create(cx + 7 - r, cy + 7 - r, 0), adsk.core.Point3D.create(cx + 7, cy + 7 - r, 0), angle)
        rect = lines.addTwoPointRectangle(adsk.core.Point3D.create(cx - 7, cy - 7, 0), adsk.core.Point3D.create(cx + 7, cy + 7, 0))
        for i in range(4):
            arcs.addFillet(rect.item(i), rect.item(i).endSketchPoint.geometry, rect.item((i+1)%4), rect.item((i+1)%4).startSketchPoint.geometry, r)
    else:
        rect = lines.addTwoPointRectangle(adsk.core.Point3D.create(cx - 7, cy - 7, 0), adsk.core.Point3D.create(cx + 7, cy + 7, 0))


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        debug = True

        if debug:
            layout = [
                ["Esc","!\n1","\"\n2","£\n3","$\n4","%\n5","^\n6","&\n7","*\n8","(\n9",")\n0","_\n-","+\n=",{"w":2},"Backspace"],
                [{"w":1.5},"Tab","Q","W","E","R","T","Y","U","I","O","P","{\n[","}\n]",{"x":0.25,"w":1.25,"h":2,"w2":1.5,"h2":1,"x2":-0.25},"Enter"],
                [{"w":1.75},"Caps Lock","A","S","D","F","G","H","J","K","L",":\n;","@\n'","~\n#"],
                [{"w":1.25},"Shift","|\n\\","Z","X","C","V","B","N","M","<\n,",">\n.","?\n/",{"w":2.75},"Shift"],
                [{"w":1.25},"Ctrl",{"w":1.25},"Win",{"w":1.25},"Alt",{"a":7,"w":6.25},"",{"a":4,"w":1.25},"AltGr",{"w":1.25},"Win",{"w":1.25},"Menu",{"w":1.25},"Ctrl"]
            ]

            alayout = [
                ["",""],
                ["",""]
            ]
            r = '3'
        else:
            returnValue, cancelled = ui.inputBox('Raw data from KLE:', 'PlateGen', '[{a:7},""]')
            layout = layoutparser('['+returnValue+']')
            r, r_cancelled = ui.inputBox('Enter corner radius', 'PlateGen', '0')
        r = float(r.replace(',','.'))
        if r > 7:
            r = 7

        ui.messageBox("Plate generation might take some time (especially if using corner radius).\n\nBe patient :)\n", 'PlateGen')

        # Create process dialog
        total = 0
        current = 0

        for row in layout:
            total += len(row)

        progressDialog = ui.createProgressDialog()
        progressDialog.cancelButtonText = 'Cancel'
        progressDialog.isBackgroundTranslucent = False
        progressDialog.isCancelButtonShown = True


        # layout.reverse()

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
        # line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3, 1, 0))
        # line2 = lines.addByTwoPoints(line1.endSketchPoint, adsk.core.Point3D.create(1, 4, 0))

        u = 19.05

        x = 0
        y = -1
        w = 1
        h = 1

        x_max = 0

        progressDialog.show('PlateGen', 'Generating plate: %p%', 0, total, 1)

        for row in layout:
            for item in row:
                if isinstance(item, str):
                    draw_rect(lines, arcs, x, y, w, h, u, r)
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

        # Create outline
        lines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(x_max * u, y * u + u, 0))

        # for row in layout:
        #     ui.messageBox('{}'.format(row))

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
