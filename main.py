from kivy.config import Config
Config.set('graphics', 'resizable', 0)

from kivy.app import App
from mainwidget import Mainwidget
from kivy.lang.builder import Builder
from kivy.core.window import Window

Window.size = (800,600)


class MainApp(App):
    """
    Classe com o aplicativo
    
    """
    def build(self):
        """
        Método que gera o aplicativo no widget principal
        """
        
        
        """
        modbus_addrs:
            tag: Endereço | Multiplicador | Tabela | Unidade
                                             
                                            0: Coil -               Valores Discretos (1 bit On/Off)
                                                                    Leitura/Escrita
                                             
                                            1: Discrete Inputs -    Valores Discretos (1bit On/Off)
                                                                    Apenas Leitura 
                                             
                                            2: Input Registers -    Valores Númericos (16 bits Valores Númericos)
                                                                    Apenas Leitura         
                                             
                                            3: Holding Registers -  Valores Númericos (16 bits)
                                                                    Leitura/Escrita
        """
        modbus_addrs = {
                        'estado_mot'    : [800,  None,  0, None],
                        'freq_des'      : [799,  1,     3, 'Hz'],
                        't_part'        : [798,  10  ,  3, 's'],
                        'freq_mot'      : [800,  10,    2, 'Hz'],
                        'tensao'        : [801,  1,     2, 'V'],
                        'rotacao'       : [803,  1,     2, 'RPM'],
                        'pot_entrada'   : [804,  10,    2, 'W'],
                        'corrente'      : [805,  100,   2, 'A'],
                        'temp_estator'  : [806,  10,    2, '°C'],
                        'vz_entrada'    : [807,  100,   2, 'L/s'],
                        'nivel'         : [808,  10,    2, 'L'],
                        'nivel_h'       : [809,  None,  1, None],
                        'nivel_l'       : [810,  None,  1, None],
                        'solenoide_1'   : [801,  None,  0, None],
                        'solenoide_2'   : [802,  None,  0, None],
                        'solenoide_3'   : [803,  None,  0, None]
                       }
        
        self._widget = Mainwidget(scan_time = 1000, server_ip='127.0.0.1',server_port=502, freqmot = 60, modbus_addrs=modbus_addrs, setpoint = 500, banda = 10, db_path = "C:\\Users\\Administrator\\Documents\\InformaticaIndustrialUFJF-main\\Python\\TrabalhoFinalSupervisorio\\db\\scada.db")
        return self._widget
    
    def on_stop(self):
        """
        Executado qnd a app é fechada
        """
        self._widget.stopRefresh()
        
if __name__ == '__main__':
    Builder.load_string(open("mainwidget.kv",encoding="utf-8").read(),rulesonly=True)
    Builder.load_string(open("popups.kv",encoding="utf-8").read(),rulesonly=True)
    MainApp().run()