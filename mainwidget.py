from kivy.uix.boxlayout import BoxLayout
from popups import ModbusPopup, ScanPopup, MotorPopup, SolenoidesPopup, ControlePopup, GraficosPopup, NivelPopup, VazaoPopup, HistGraphPopup, MotorIconPopup, InversorIconPopup
from pyModbusTCP.client import ModbusClient
from kivy.core.window import Window
from threading import Thread
from time import sleep
from datetime import datetime
import random
from timeseriesgraph import TimeSeriesGraph
from kivy_garden.graph import LinePlot
from bdhandler import BDHandler

class Mainwidget(BoxLayout):
    """
    Widget principal da aplicação
    """
    _updateThread = None
    _updateWidgets = True
    _tags = {}
    _max_points = 20
    _controle = False
    
    def __init__(self, **kwargs):
        """
        Construtor do widget principal
        """
        super().__init__()
        
        self._scan_time = kwargs.get('scan_time')
        self._serverIP = kwargs.get('server_ip')
        self._serverPort = kwargs.get('server_port')
        self._freqmot = kwargs.get('freqmot')
        self._sp = kwargs.get('setpoint')
        self._banda = kwargs.get('banda')
        
        self._modbusPopup = ModbusPopup(self._serverIP, self._serverPort)
        self._scanPopup = ScanPopup(self._scan_time)
        self._motorPopup = MotorPopup(self._freqmot)
        self._solenoidesPopup = SolenoidesPopup()
        self._controlePopup = ControlePopup(self._sp, self._banda)
        self._graficosPopup = GraficosPopup()
        self._inversorIconPopup = InversorIconPopup()
        self._motorIconPopup = MotorIconPopup()
        
        self._freqAtual = 60
        
        self._modbusClient = ModbusClient(host=self._serverIP,port=self._serverPort)

        self._meas = {'timestamp': None, 'values':{}}
        
        for key,value in kwargs.get('modbus_addrs').items():
            plot_color = (random.random(), random.random(), random.random(), 1)
            self._tags[key] = {'addr': value[0], 'mult': value[1], 'table': value[2], 'un': value[3], 'color': plot_color}
            
        self._nivelGraph = NivelPopup(self._max_points, self._tags['nivel']['color'])
        self._vazaoGraph = VazaoPopup(self._max_points, self._tags['vz_entrada']['color'])
        self._hgraph = HistGraphPopup(tags=self._tags)
        self._db = BDHandler(kwargs.get('db_path'), self._tags)        
        
    def startDataRead(self, ip, port):
        """
        Método utilizado para a configuração do IP e PORTA do servidor MODBUS e
        inicializar uma thread para a leitura dos dados e atualização da interface gráfica
        """
        self._serverIP = ip
        self._serverPort = port
        self._modbusClient.host = self._serverIP
        self._modbusClient.port = self._serverPort
        self.ids.img_sol1.source = 'imgs/solenoide_desligado.png'
        self.ids.img_sol2.source = 'imgs/solenoide_desligado.png'
        self.ids.img_sol3.source = 'imgs/solenoide_desligado.png'
        self.ids.img_engine.source = 'imgs/Engine_desligado.png'
        try:
            Window.set_system_cursor("wait")
            self._modbusClient.open()
            Window.set_system_cursor("arrow")
            if self._modbusClient.is_open:
                self._updateThread = Thread(target=self.updater)
                self._updateThread.start()
                self.ids.img_con.source = 'imgs/conectado.png'
                self._modbusPopup.dismiss()
            else:
                self._modbusPopup.setInfo("Falha na conexão com o servidor")
        except Exception as e:
            print("Erro -readData- : ", e.args)
        
    def updater(self):
        """
        Método que invoca as rotinas de leitura dos dados,
        atualização da interface e inserção dos dados no
        banco de dados
        """
        try:
            while self._updateWidgets:
                #ler os dados MODBUS
                try:
                    self.readData()
                except Exception as e:
                    print("Erro -readData|updater- : ",e.args)
                #Atualizar a GUI
                try:
                    self.updateGUI()
                except Exception as e:
                    print("Erro -updateGUI|updater- : ",e.args)
                #inserir os dados no BD
                try:
                    self._db.insertData(self._meas)
                except Exception as e:
                    print("Erro -insertData|updater- : ",e.args)
                #controle por histerese
                try:
                    if self._controle:
                        self.controleHisterese()
                except Exception as e:
                    print("Erro -controleHisterese|updater- : ",e.args)
                try:
                    self.alarmes()
                except Exception as e:
                    print("Erro -alarmes|updater- : ",e.args)
                sleep(self._scan_time/1000)
        except Exception as e:
            self._modbusClient.close()
            print("Erro -updater- :",e.args)
        
    def readData(self):
        """
        Leitura dos dados MODBUS
        """
        self._meas['timestamp'] = datetime.now()
        for key,value in self._tags.items():
            if key == 'freq_des':
                self._meas['values'][key] = self._freqAtual                
            elif value['table'] == 0:
                self._meas['values'][key] = (self._modbusClient.read_coils(value['addr'],1)[0])                 
            elif value['table'] == 1:
                self._meas['values'][key] = (self._modbusClient.read_discrete_inputs(value['addr'],1)[0])
            elif value['table'] == 2:
                self._meas['values'][key] = (self._modbusClient.read_input_registers(value['addr'],1)[0])/value['mult']
            else:
                self._meas['values'][key] = (self._modbusClient.read_holding_registers(value['addr'],1)[0])/value['mult']
                
    def updateGUI(self):
        """
        Atualização da GUI
        """

        for key,value in self._tags.items():
            if value['mult'] is not None:
                if key == 'nivel':
                    self.ids[key].text = 'Nível do Reservatório: ' + str(self._meas['values'][key]) + value['un']
                elif key == 'vz_entrada':
                    self.ids[key].text = 'Vazão de Entrada: ' + str(self._meas['values'][key]) + value['un']
                else:
                    self.ids[key].text = key + ': ' + str(self._meas['values'][key]) + value['un']
            else:
                self.ids[key].text = ': ' + str(self._meas['values'][key])

        self.ids.lb_water.size = (self.ids.lb_water.size[0],(self._meas['values']['nivel']/1000)*self.ids.water.size[1]*0.355)
        self.ids.lb_vazao.size = (24.5,(self._meas['values']['vz_entrada']*9))
        self._nivelGraph.ids.nivel_graph.updateGraph((self._meas['timestamp'], self._meas['values']['nivel']),0)
        self._vazaoGraph.ids.vazao_graph.updateGraph((self._meas['timestamp'], self._meas['values']['vz_entrada']),0)
        
        self.infoMotor()
        self.infoInverter()
    
    def stopRefresh(self):
        self._updateWidgets = False
        self._controle = False
        self.desSol1()
        self.desSol2()
        self.desSol3()
        self.desMotor()        
    
    def getDataDB(self):
        """
        Método pra coletar as informações da interface e requisita a busca
        no BD para apresentação no gráfico de dados históricos
        """
        try:
            init_t  = self.parseDTString(self._hgraph.ids.txt_init_time.text) 
            final_t = self.parseDTString(self._hgraph.ids.txt_final_time.text)
            cols = []
            for sensor in self._hgraph.ids.sensores.children:
                if sensor.ids.checkbox.active:
                    cols.append(sensor.id)
            if init_t is None or final_t is None or len(cols)==0:
                return

            cols.append('timestamp')

            dados = self._db.selectData(cols, init_t, final_t)
            if dados is None or len(dados['timestamp']) == 0:
                return

            self._hgraph.ids.graph.clearPlots()
            for key,value in dados.items():
                if key == 'timestamp':
                    continue
                p = LinePlot(line_width=1.5, color=self._tags[key]['color'])
                p.points = [(x, (value[x]/self._tags[key]['mult'])) for x in range(0, len(value))] if self._tags[key]['mult'] is not None else [(x, value[x]) for x in range(0, len(value))]
                        
            self._hgraph.ids.graph.add_plot(p)
            self._hgraph.ids.graph.xmax = len(dados[cols[0]])
            self._hgraph.ids.graph.update_x_labels([datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f") for x in dados['timestamp']])
        except Exception as e:
            print ("Erro -getDataDB- : ", e.args)
    
    def parseDTString(self, datetime_str):
        """
        Converter string de data do usuário para o padrao do sql
        """
        try:
            d = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
            return d.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print ("Erro -parseDTString- : ", e.args)

        
    def ligMotor(self):
        """
        Ligar Motor
        """
        self._meas['values']['estado_mot'] = 1
        self._modbusClient.write_single_coil(self._tags['estado_mot']['addr'],self._meas['values']['estado_mot'])
        self.ids.img_engine.source = 'imgs/Engine_ligado.png'
    
    def desMotor(self):
        """
        Desligar Motor
        """
        self._meas['values']['estado_mot'] = 0
        self._modbusClient.write_single_coil(self._tags['estado_mot']['addr'], self._meas['values']['estado_mot'])
        self.ids.img_engine.source = 'imgs/Engine_desligado.png'
        
    def ligSol1(self):
        """
        Liga Solenoide 1
        """
        self._meas['values']['solenoide_1'] = 1
        self._modbusClient.write_single_coil(self._tags['solenoide_1']['addr'], self._meas['values']['solenoide_1'])
        self.ids.img_sol1.source = 'imgs/solenoide_ligado.png'
    
    def desSol1(self):
        """
        Desliga Solenoide 1
        """
        self._meas['values']['solenoide_1'] = 0
        self._modbusClient.write_single_coil(self._tags['solenoide_1']['addr'], self._meas['values']['solenoide_1'])
        self.ids.img_sol1.source = 'imgs/solenoide_desligado.png'
        
    def ligSol2(self):
        """
        Liga Solenoide 2
        """
        self._meas['values']['solenoide_2'] = 1
        self._modbusClient.write_single_coil(self._tags['solenoide_2']['addr'], self._meas['values']['solenoide_2'])
        self.ids.img_sol2.source = 'imgs/solenoide_ligado.png'
        
    def desSol2(self):
        """
        Desliga Solenoide 2
        """
        self._meas['values']['solenoide_2'] = 0
        self._modbusClient.write_single_coil(self._tags['solenoide_2']['addr'], self._meas['values']['solenoide_2'])
        self.ids.img_sol2.source = 'imgs/solenoide_desligado.png'
        
    def ligSol3(self):
        """
        Liga Solenoide 3
        """
        self._meas['values']['solenoide_3'] = 1
        self._modbusClient.write_single_coil(self._tags['solenoide_3']['addr'], self._meas['values']['solenoide_3'])
        self.ids.img_sol3.source = 'imgs/solenoide_ligado.png'
        
    def desSol3(self):
        """
        Desliga Solenoide 3
        """
        self._meas['values']['solenoide_3'] = 0
        self._modbusClient.write_single_coil(self._tags['solenoide_3']['addr'], self._meas['values']['solenoide_3'])
        self.ids.img_sol3.source = 'imgs/solenoide_desligado.png'
        
    def defFreq(self):
        """
        Definir Frequencia Motor
        """
        self._meas['values']['freq_des'] = self._freqmot
        self._freqAtual = self._meas['values']['freq_des']
        self._modbusClient.write_single_register(self._tags['freq_des']['addr'], self._meas['values']['freq_des'])
    

    def controleHisterese (self):
        """
        Controle de Nivel por Histerese
        """
        if self._meas['values']['nivel'] >= (self._sp+(self._banda/2)):
            self.desMotor()

        elif self._meas['values']['nivel'] <= (self._sp-(self._banda/2)):
            self.ligMotor()
            
        else:
            return
        
    def infoMotor (self):
        """
        Informções para o popup do motor
        """
        self._motorIconPopup.ids.estado_mot.text = 'Estado: ' +  str(self._meas['values']['estado_mot']) 
        self._motorIconPopup.ids.freq_mot.text = 'Frequência: ' +  str(self._meas['values']['freq_mot']) + ' Hz'
        self._motorIconPopup.ids.t_part.text = 'Tempo de Partida: ' +  str(self._meas['values']['t_part']) + ' s'
        self._motorIconPopup.ids.rotacao.text = 'Rotação: ' +  str(self._meas['values']['rotacao']) + ' RPM'
        self._motorIconPopup.ids.temp_estator.text = 'Temperatura do Estator: ' +  str(self._meas['values']['temp_estator']) + ' °C'
        
        
    def infoInverter(self):
        """
        Informações para o popup do inversor
        """
        self._inversorIconPopup.ids.freq_des.text = 'Frequência Desjeada: ' + str(self._meas['values']['freq_des']) + ' Hz'
        self._inversorIconPopup.ids.tensao.text = 'Tensão: ' + str(self._meas['values']['tensao']) + ' V'
        self._inversorIconPopup.ids.corrente.text = 'Corrente: ' + str(self._meas['values']['corrente']) + ' A (RMS)'
        self._inversorIconPopup.ids.pot_entrada.text = 'Potência de Entrada: ' + str(self._meas['values']['pot_entrada']) + ' W'
        
    def alarmes(self):
        if self._meas['values']['nivel_h']:
            self.ids.alerta_high.source = 'imgs/alerta_high.png'
            self.ids.alerta_maximo.text = 'Nível Máximo Atingido'
        else:
            self.ids.alerta_high.source = 'imgs/sem_alerta.png'
            self.ids.alerta_maximo.text = ''