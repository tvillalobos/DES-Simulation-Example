from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtTest import QTest
from collections import deque
from random import choice
from random import expovariate, randint


def id_generator():
    n = 0
    while True:
        yield n
        n += 1

ides_gen = id_generator()



class Cliente():


    def __init__(self, parent):

        self._id = next(ides_gen)
        self.label = QLabel("", parent)
        self.label.setAlignment(Qt.AlignCenter)
        self.imagen_path = "cliente_1.png"
        self.pixmap = QPixmap(self.imagen_path).scaled(30, 30)
        self.painter = QPainter(self.pixmap)
        self.label.setPixmap(self.pixmap)
        self.caja = None
        self.pedido = None
        self.en_cola = False
        self.comiendo = False
        self.velocidad_en_comer = randint(1, 3)


        self.tiempo_decide = None
        self.tiempo_atencion = None
        self.tiempo_comer = None
        self.tiempo_abandono_cola = None

    def agregar_pedido(self):
        self.pedido = Comida()

    def generar_tiempo_decide(self, tiempo_actual):
        self.tiempo_decide = tiempo_actual + randint(3, 5)

    def generar_tiempo_atencion(self, tiempo_actual, n):
        self.tiempo_atencion = tiempo_actual + (n + 0.25) * 4

    def generar_tiempo_comer(self, tiempo_actual):
        factor = self.pedido.tiempo_en_comer - self.velocidad_en_comer
        self.tiempo_comer = tiempo_actual + factor


    def cambiar_sprite(self):
        if self.imagen_path == "cliente_1.png":
            self.imagen_path = "cliente_2.png"
        else:
            self.imagen_path = "cliente_1.png"
        self.imagen = QPixmap(self.imagen_path).scaled(30, 30)
        self.label.setGeometry(0, 0, 50, 50)
        self.label.setPixmap(self.imagen)

    def __repr__(self):
        return "Cliente {}".format(self._id)



class Comida:

    @staticmethod
    def elegir_comida():
        return choice(["Hamburguesa", "Papas Fritas", "Pizza", "Ensalada"])


    def __init__(self):

        self.tipo = Comida.elegir_comida()
        self.precio = randint(100, 200)
        self.tiempo_en_comer = randint(4, 8)



class Simulacion(QObject):

    trigger_act_tiempo = pyqtSignal(str)
    trigger_act_prox_evento = pyqtSignal(str)
    trigger_agregar_evento = pyqtSignal(str, float)
    trigger_nuevo_cliente = pyqtSignal(QLabel)
    trigger_cliente_cola = pyqtSignal(QLabel, int)
    trigger_cliente_atencion = pyqtSignal(QLabel, int)
    trigger_sacar_cliente = pyqtSignal(QLabel)
    trigger_termino_simulacion = pyqtSignal(str)

    def __init__(self, parent, tiempo_maximo, tasa_llegada, tipo):
        super().__init__()
        self._parent = parent
        self._tiempo_actual = 0
        self.tiempo_maximo = tiempo_maximo
        self.tasa_llegada = tasa_llegada
        self.tipo_simulacion = tipo
        self.velocidad_inicial = 3000
        self.velocidad = self.velocidad_inicial

        self.clientes = []
        self.caja_1, self.caja_2, self.caja_3 = deque(), deque(), deque()
        self.cajas = [self.caja_1, self.caja_2, self.caja_3]


        self.proximo_cliente_llega = expovariate(tasa_llegada)
        self.conectar_triggers()

        self.dinero = [0, 0, 0]
        self.pedidos = []





    def conectar_triggers(self):
        self.trigger_act_tiempo.connect(self._parent.act_tiempo)
        self.trigger_agregar_evento.connect(self._parent.agregar_evento)
        self.trigger_nuevo_cliente.connect(self._parent.agregar_nuevo_cliente)
        self.trigger_cliente_cola.connect(self._parent.agregar_cliente_cola)
        self.trigger_cliente_atencion.connect(self._parent.agregar_cliente_mesas)
        self.trigger_sacar_cliente.connect(self._parent.sacar_cliente)
        self.trigger_termino_simulacion.connect(self._parent.terminar_simulacion)

    def cambiar_velocidad(self, valor):
        nueva_velocidad = self.velocidad_inicial / valor
        self.velocidad = nueva_velocidad



    @property
    def tiempo_actual(self):
        return self._tiempo_actual

    @tiempo_actual.setter
    def tiempo_actual(self, nuevo_tiempo):
        self._tiempo_actual = nuevo_tiempo
        self.trigger_act_tiempo.emit(str(round(nuevo_tiempo,2)))

    @property
    def clientes_en_cola(self):
        return list(filter(lambda c: c.en_cola, self.clientes))

    @property
    def clientes_comiendo(self):
        return list(filter(lambda c: c.comiendo, self.clientes))

    @property
    def proximo_cliente_decide(self):
        if len(self.clientes):
            cliente = sorted(self.clientes, key=lambda x: x.tiempo_decide)[0]
            return cliente, cliente.tiempo_decide
        return (None, float("Inf"))

    @property
    def proximo_cliente_atendido(self):
        if len(self.clientes_en_cola):
            cliente = sorted(self.clientes_en_cola, key=lambda x: x.tiempo_atencion)[0]
            return cliente, cliente.tiempo_atencion
        return (None, float("Inf"))

    @property
    def proximo_cliente_come(self):
        if len(self.clientes_comiendo):
            cliente = sorted(self.clientes_comiendo,
                             key=lambda x: x.tiempo_comer)[0]
            return cliente, cliente.tiempo_comer
        return (None, float("Inf"))


    @property
    def proximo_evento(self):
        tiempos = [self.proximo_cliente_llega, self.proximo_cliente_decide[1],
                   self.proximo_cliente_atendido[1], self.proximo_cliente_come[1]]

        tiempo_prox_evento = min(tiempos)

        if tiempo_prox_evento >= self.tiempo_maximo:
            return "fin"

        eventos = ["llegada_cliente", "cliente_decide", "cliente_atendido",
                   "cliente_come"]
        evento = eventos[tiempos.index(tiempo_prox_evento)]
        return evento


    def llegada_cliente(self):
        self.tiempo_actual = self.proximo_cliente_llega
        self.proximo_cliente_llega = self.tiempo_actual + expovariate(self.tasa_llegada)
        cliente = Cliente(self._parent)
        self.clientes.append(cliente)
        cliente.generar_tiempo_decide(self.tiempo_actual)
        self.trigger_nuevo_cliente.emit(cliente.label)
        self.actualizar_eventos("Llegada Cliente {}".format(cliente._id),
                                self.tiempo_actual)

    def cliente_decide(self):
        cliente, tiempo_decide = self.proximo_cliente_decide
        self.tiempo_actual = tiempo_decide
        caja = randint(0, 2)
        cliente.cambiar_sprite()
        cliente.en_cola, cliente.caja = True, caja
        cliente.tiempo_decide = float("Inf")
        cliente.generar_tiempo_atencion(self.tiempo_actual, len(self.cajas[caja]))
        self.cajas[caja].append(cliente)
        self.trigger_cliente_cola.emit(cliente.label, caja)
        self.actualizar_eventos("Cliente {} decide".format(cliente._id),
                                self.tiempo_actual)

    def cliente_atendido(self):
        cliente, tiempo_atencion = self.proximo_cliente_atendido

        self.tiempo_actual = tiempo_atencion
        cliente.tiempo_atencion = float("Inf")
        cliente.en_cola = False
        cliente.cambiar_sprite()
        pedido = Comida()
        cliente.pedido = pedido
        cliente.comiendo = True
        cliente.generar_tiempo_comer(self.tiempo_actual)
        self.pedidos.append(pedido)
        self.dinero[cliente.caja] += cliente.pedido.precio
        self.cajas[cliente.caja].popleft()
        self.trigger_cliente_atencion.emit(cliente.label, cliente.caja)
        self.actualizar_eventos("Cliente {} Atendido".format(cliente._id),
                                self.tiempo_actual)

    def cliente_come(self):
        cliente, tiempo_comer = self.proximo_cliente_come
        self.tiempo_actual = tiempo_comer
        cliente.tiempo_comer = float("Inf")
        self.trigger_sacar_cliente.emit(cliente.label)
        self.actualizar_eventos("Cliente {} come".format(cliente._id),
                                self.tiempo_actual)

    def actualizar_eventos(self, evento, tiempo):
        self.trigger_agregar_evento.emit(evento, round(tiempo, 2))



    def run(self):

        while True:

            evento = self.proximo_evento


            if evento == "fin":
                print("Termino de la simulación")
                self.tiempo_actual = self.tiempo_maximo
                QTest.qWait(1.5)
                self.trigger_termino_simulacion.emit(self.tipo_simulacion)
                break

            elif evento == "llegada_cliente":
                self.llegada_cliente()

            elif evento == "cliente_decide":
                self.cliente_decide()

            elif evento == "cliente_atendido":
                self.cliente_atendido()

            elif evento == "cliente_come":
                self.cliente_come()

            if self.tipo_simulacion == "Manual":
                break
            else:
                QTest.qWait(self.velocidad)

    def numero_de(self, tipo_comida):
        return len(list(filter(lambda x: x.tipo == tipo_comida, self.pedidos)))

    def generar_estadisticas(self):
        total_clientes = len(self.clientes)
        clientes_atendidos = len(self.clientes_comiendo)
        dinero_recaudado = sum(self.dinero)
        dinero_caja_1 = self.dinero[0]
        dinero_caja_2 = self.dinero[1]
        dinero_caja_3 = self.dinero[2]
        n_papas_fritas = self.numero_de("Papas Fritas")
        n_hamburguesa = self.numero_de("Hamburguesa")
        n_ensaladas = self.numero_de("Ensalada")
        n_pizzas = self.numero_de("Pizza")
        estadis = ["Total Clientes: ", "Clientes atendidos: ", "Dinero recaudado: ",
                   "Dinero caja 1: ", "Dinero caja 2: ", "Dinero caja 3: ", "Nº Papas Fritas: ",
                   "Nº Hamburguesas: ", "Nº Ensaladas: ", "Nº Pizzas: "]
        var = [total_clientes, clientes_atendidos, dinero_recaudado, dinero_caja_1,
               dinero_caja_2, dinero_caja_3, n_papas_fritas, n_hamburguesa, n_ensaladas,
               n_pizzas]
        return zip(estadis, var)


















if __name__ == '__main__':

    pass