from PyQt5 import QtCore, QtGui, QtWidgets


class BlockD:
    def __init__(self, name, geometry, alias=None):
        self.name = name
        self.geometry = geometry
        if alias is None:
            alias = self.name
        self.alias = alias


class ConnectionD:
    def __init__(self, name, path, color, visible=False):
        self.name = name
        self.path = path
        self.color = color
        self.visible = visible


class SystemDiagram(QtWidgets.QGraphicsView):
    def __init__(self, parent, system, blocks_d, connections_d):
        super().__init__(parent)
        self.parent = parent
        self.system = system
        self.blocks_d = blocks_d
        self.connections_d = connections_d

        self.K = 30

        self.initUI()

    def initUI(self):
        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setBackgroundBrush(QtGui.QColor('white'))
        self.setScene(self.scene)

        for j, c in enumerate(self.connections_d):
            self.addConnection(j, c)

        for i, b in enumerate(self.blocks_d):
            self.addBlock(i, b)

        self.setFixedHeight (int(self.scene.height() + 1.5*self.K))
        self.setMinimumWidth(int(self.scene.width() + 1.5*self.K))

    def addBlock(self, idx, block):
        left, top, width, height = list(x * self.K for x in block.geometry)

        rect_item = MyGraphicsRectItem(left, top, width, height)
        rect_item.setToolTip(block.name)
        rect_item.setMousePressEvent(lambda x=idx: self.parent.showBlockOption(x))
        self.scene.addItem(rect_item)

        text = self.scene.addText(None)
        text.setAcceptHoverEvents(False)
        text.setHtml('<center>{}</center>'.format(block.alias))
        text.setTextWidth(width)
        text.setPos(left, top + 2.5)

    def addConnection(self, idx, connection):
        path_coords = []
        for coord in connection.path:
            path_coords.append((self.K*coord[0], self.K*coord[1]))

        path = QtGui.QPainterPath()
        path0 = QtGui.QPainterPath()
        coord = path_coords[0]
        path.moveTo(*coord)
        path0.moveTo(*coord)
        for coord in path_coords:
            path.lineTo(*coord)
            path0.lineTo(*coord)

        path_item = MyGraphicsPathItem(connection.color, connection.visible, path)
        path_item.setToolTip(connection.name)
        path_item.setMousePressEvent(lambda x=idx: self.parent.toggleSignal(x))

        self.scene.addItem(QtWidgets.QGraphicsPathItem(path0))
        self.scene.addItem(path_item)


class MyGraphicsRectItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)

        self.pen = QtGui.QPen(QtCore.Qt.SolidLine)
        self.pen.setWidth(2)

        self.enter_brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
        self.enter_brush.setColor(QtGui.QColor(0xFF, 0xFF, 0x00))

        self.leave_brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
        self.leave_brush.setColor(QtGui.QColor('white'))

        self.setBrush(self.leave_brush)
        self.setPen(self.pen)

    def setMousePressEvent(self, fn):
        self.mousePressEventFn = fn

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.mousePressEventFn()

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setBrush(self.enter_brush)

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.setBrush(self.leave_brush)


class MyGraphicsPathItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, color, visible, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)

        self.pen_colored = QtGui.QPen(QtCore.Qt.SolidLine)
        self.pen_colored.setColor(QtGui.QColor(*color, alpha=0x64))
        self.pen_colored.setWidth(20)

        self.pen_blank = QtGui.QPen(QtCore.Qt.SolidLine)
        self.pen_blank.setWidth(20)
        self.pen_blank.setColor(QtGui.QColor(0xFF, 0xFF, 0xFF, alpha=0x00))
        self.pen_blank.setCosmetic(False)

        self.clicked = visible
        self.updateColor()

    def setMousePressEvent(self, fn):
        self.mousePressEventFn = fn

    def mousePressEvent(self, event):
        if self == self.scene().itemAt(event.scenePos(), QtGui.QTransform()):
            super().mousePressEvent(event)
            self.mousePressEventFn()
            self.clicked ^= True
            self.updateColor()

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setPen(self.pen_colored)

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.updateColor()

    def updateColor(self):
        if self.clicked:
            self.setPen(self.pen_colored)
        else:
            self.setPen(self.pen_blank)
