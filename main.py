import sys
from simulacion import Simulacion, id_generator
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QLabel, QApplication, QMessageBox, QPushButton,
                             QWidget, QVBoxLayout)


ides_gen = id_generator()

ventana_principal = uic.loadUiType("ventana.ui")
ventana_ingreso = uic.loadUiType("ventana_ingreso.ui")
ventana_estadisticas = uic.loadUiType("ventana_estadisticas.ui")


class Ventana(ventana_principal[0], ventana_principal[1]):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setup()

    def setup(self):
        self.cajas = [self.caja_1, self.caja_2, self.caja_3]
        self.clientes = []
        self.labels_eventos = []
        self.scroll_content = self.scrollAreaWidgetContent.layout()
        self.ingreso = VentanaIngreso()
        self.ingreso.boton_comenzar.clicked.connect(self.comenzar)
        self.ingreso.boton_manual.clicked.connect(self.activar_boton)
        self.ingreso.boton_auto.clicked.connect(self.activar_boton)
        self.velocimetro.valueChanged.connect(self.cambiar_velocidad)

    def activar_boton(self):
        self.ingreso.boton_comenzar.setEnabled(True)

    def comenzar(self):
        self.ingreso.close()
        auto = False
        if self.ingreso.boton_manual.isChecked():
            tipo_simulacion = "Manual"
            self.velocimetro.deleteLater()
            self.label_10.deleteLater()
        else:
            tipo_simulacion = "Automatica"
            self.boton.deleteLater()
            self.label.setText("Velocidad")
            auto = True

        tasa_llegada = self.ingreso.tasa_llegada.value()
        tiempo_max = self.ingreso.tiempo_max.value()
        self.simulacion = Simulacion(self, tiempo_max, tasa_llegada, tipo_simulacion)
        self.show()
        if auto:
            self.simulacion.run()
        else:
            self.boton.clicked.connect(self.simulacion.run)

    def cambiar_velocidad(self):
        self.simulacion.cambiar_velocidad(self.velocimetro.value())


    def act_tiempo(self, tiempo):
        self.label_tiempo_actual.setText(tiempo)

    def act_prox_evento(self, evento):
        pass

    def agregar_evento(self, evento, tiempo):
        for label in self.labels_eventos:
            label.setStyleSheet("")
        self.evento_actual.setText(evento)
        label = QLabel("[{}] ".format(tiempo) + evento, self)
        label.setStyleSheet("background-color: rgb(51, 138, 187);")
        self.labels_eventos.append(label)
        self.scroll_content.insertWidget(0, label)

    def agregar_nuevo_cliente(self, label_cliente):
        self.espera.addWidget(label_cliente)

    def agregar_cliente_cola(self, label_cliente, caja):
        self.espera.removeWidget(label_cliente)
        self.cajas[caja].insertWidget(0, label_cliente)

    def agregar_cliente_mesas(self, label_cliente, caja):
        self.cajas[caja].removeWidget(label_cliente)
        self.mesas.addWidget(label_cliente)

    def sacar_cliente(self, label_cliente):
        self.mesas.removeWidget(label_cliente)
        label_cliente.deleteLater()

    def terminar_simulacion(self, tipo_simulacion):
        if tipo_simulacion == "Manual":
            self.boton.setEnabled(False)
        mensaje = QMessageBox()
        mensaje.setText("Termino de la simulación")
        mensaje.setWindowTitle("DES")
        boton = QPushButton("Ver estadísticas")
        boton.clicked.connect(self.mostrar_estadisticas)
        mensaje.addButton(boton, QMessageBox.YesRole)
        mensaje.exec_()

    def mostrar_estadisticas(self):
        self.ventana_estadis = VentanaEstadisticas()
        layout = self.ventana_estadis.verticalWidget.layout()
        estadisticas = self.simulacion.generar_estadisticas()
        for text, valor in estadisticas:
            label = QLabel(text + str(valor), self.ventana_estadis)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

    def closeEvent(self, CloseEvent):
        self.simulacion.continuar = False
        super(ventana_principal[1], self).closeEvent(CloseEvent)


class VentanaIngreso(ventana_ingreso[0], ventana_ingreso[1]):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()


class VentanaEstadisticas(ventana_estadisticas[0], ventana_estadisticas[1]):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()


if __name__ == '__main__':
    def hook(type, value, traceback):
        print(type)
        print(traceback)
    sys.__excepthook__ = hook

    app = QApplication([])
    ventana = Ventana()
    app.exec()