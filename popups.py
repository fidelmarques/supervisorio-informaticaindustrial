from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy_garden.graph import LinePlot
from kivy.uix.boxlayout import BoxLayout

class ModbusPopup(Popup):
    """
    Popup de configurações do MODBUS
    """
    _info_lb = None
    def __init__(self, server_ip,server_port,**kwargs):
        """
        Construtor da classe MODBUS
        """
        super().__init__(**kwargs)
        self.ids.txt_ip.text = str(server_ip)
        self.ids.txt_port.text = str(server_port)
        
    def setInfo(self, message):
        self._info_lb = Label(text=message)
        self.ids.layout_mb.add_widget(self._info_lb)
        
    def clearInfo(self):
        if self._info_lb is not None:
            self.ids.layout_mb.remove_widget(self._info_lb)
              

class ScanPopup(Popup):
    """
    Popup para configuração do tempo de varredura
    """
    def __init__(self, scantime, **kwargs):
        """
        Construtor da classe ScanPopup
        """
        super().__init__(**kwargs)
        self.ids.txt_st.text = str(scantime)


class MotorPopup(Popup):
    def __init__ (self,freqmot,**kwargs):
        """
        Construtor da classe MotorPopup
        """
        super().__init__(**kwargs)
        self.ids.txt_freq.text = str(freqmot)

class SolenoidesPopup(Popup):
    pass 

class ControlePopup(Popup):
    def __init__(self, setpoint, banda, **kwargs):
        """
        Construtor da classe ControlePopup
        """
        super().__init__(**kwargs)
        self.ids.txt_sp.text = str(setpoint)
        self.ids.txt_banda.text = str(banda)
        
class GraficosPopup(Popup):
    pass

class VazaoPopup(Popup):
    def __init__(self, xmax, plot_color, **kwargs):
        super().__init__(**kwargs)
        self.plot = LinePlot(line_width=1.5, color=plot_color)
        self.ids.vazao_graph.add_plot(self.plot)
        self.ids.vazao_graph.xmax = xmax

class LabeledCheckBoxVazaoGraph(BoxLayout):
    pass

class NivelPopup(Popup):
     def __init__(self, xmax, plot_color, **kwargs):
        super().__init__(**kwargs)
        self.plot = LinePlot(line_width=1.5, color=plot_color)
        self.ids.nivel_graph.add_plot(self.plot)
        self.ids.nivel_graph.xmax = xmax

class LabeledCheckBoxNivelGraph(BoxLayout):
    pass

class HistGraphPopup(Popup):
    def __init__(self,**kwargs):
        super().__init__()
        for key,value in kwargs.get('tags').items():
            if key == 'freq_des':
                continue
            cb = LabeledCheckBoxHistGraph()
            cb.ids.label.text = key
            cb.ids.label.color = value['color']
            cb.id  = key
            cb.orientation = 'vertical'
            self.ids.sensores.add_widget(cb)

class LabeledCheckBoxHistGraph(BoxLayout):
    pass

class MotorIconPopup(Popup):
    pass

class InversorIconPopup(Popup):
    pass
