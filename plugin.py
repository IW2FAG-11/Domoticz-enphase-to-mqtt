"""
    <plugin key="EnphasetoMQTT" name="Enphase-to-MQTT" author="Wizzard72" version="0.0.1" wikilink="https://github.com/Wizzard72/D">
    <description>
        <h2>Enphase to MQTT plugin</h2><br/>
        This plugin reads the Enphase envoy and publish the json output to MQTT.
    </description>
    <params>
        <param field="Mode1" label="Enphase Envoy IP Address" width="200px" required="true" default="Enphase IP Address"/>
        <param field="Mode2" label="Enphase Envoy Password" width="200px" required="true" default="password" password="true"/>
        <param field="Address" label="IP Address or DNS name of the MQTT broker" width="200px" required="true" default="default"/>
        <param field="Port" label="Port" width="30px" required="true" default="1883"/>
        <param field="Username" label="MQTT Username" width="200px" required="false" default="Username"/>
        <param field="Password" label="MQTT Password" width="200px" required="false" default="password"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import requests
import threading
import time
from requests.auth import HTTPDigestAuth
from datetime import datetime
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("paho-mqtt module is missing.")



class BasePlugin:
    _VERSION_CHECK = None
    _MQTT_TOPIC = None
    _MQTT_USERNAME = None
    _MQTT_CONN = None
    _MQTT_HOST = None
    _MQTT_PORT = None
    _MQTT_PASSWORD = None
    _ENPHASE_USER = None
    _ENPHASE_AUTH = None
    _MARKER = None

    def __init__(self):
        return

    def onStart(self):
        self._MQTT_HOST = Parameters["Address"]
        self._MQTT_PORT = Parameters["Port"]
        self._MQTT_TOPIC = "/envoy/json"
        self._MQTT_USERNAME = Parameters["Username"]
        self._MQTT_PASSWORD = Parameters["Password"]
        self._ENPHASE_USER = "installer"
        self._ENPHASE_AUTH = HTTPDigestAuth(self._ENPHASE_USER, Parameters["Mode2"])
        self._MARKER = b'data: '
        _STRNAME = "onStart: "
        Domoticz.Debug(_STRNAME+"called")

        if (Parameters["Mode6"] != "0"):
            Domoticz.Debugging(int(Parameters["Mode6"]))
        else:
            Domoticz.Debugging(0)

        # check if version of domoticz is 2020.2 or higher
        try:
            if int(Parameters["DomoticzVersion"].split('.')[0]) < 2020:  # check domoticz major version
                Domoticz.Error(
                    "Domoticz version required by this plugin is 2020.2 (you are running version {}).".format(
                        Parameters["DomoticzVersion"]))
                Domoticz.Error("Plugin is therefore disabled")
                self.setVersionCheck(False, "onStart")
            else:
                self.setVersionCheck(True, "onStart")
        except Exception as err:
            Domoticz.Error("Domoticz version check returned an error: {}. Plugin is therefore disabled".format(err))
            self.setVersionCheck(False, "onStart")
        if not self._VERSION_CHECK:
            return

        self.mqtt_conn()
        Domoticz.Heartbeat(10)

    def onStop(self):
        _STRNAME = "onStop: "
        Domoticz.Debug(_STRNAME+"Pluggin is stopping.")

    def onConnect(self, Connection, Status, Description):
        _STRNAME = "onConnect: "
        Domoticz.Debug(_STRNAME+"called")
        Domoticz.Debug(_STRNAME+"Connection = "+str(Connection))
        Domoticz.Debug(_STRNAME+"Status = "+str(Status))
        Domoticz.Debug(_STRNAME+"Description = "+str(Description))

    def onMessage(self, Connection, Data):
        _STRNAME = "onMessage: "
        Domoticz.Debug(strName+"called")
        DumpHTTPResponseToLog(Data)
        Domoticz.Debug(_STRNAME+"Data = " +str(Data))
        strData = Data["Data"].decode("utf-8", "ignore")
        status = int(Data["Status"])


    def onCommand(self, Unit, Command, Level, Hue):
        _STRNAME = "onCommand: "
        Domoticz.Log(_STRNAME+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        #if self.versionCheck is True:

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        _STRNAME = "onNotification: "
        Domoticz.Debug(_STRNAME+"called")
        Domoticz.Log(_STRNAME+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        _STRNAME = "onDisconnect: "
        Domoticz.Debug(_STRNAME+"called")

    def onHeartbeat(self):
        _STRNAME = "onHeartbeat: "
        Domoticz.Debug(_STRNAME+"called")
        self.enphase_stream()
        #if self._VERSION_CHECK is True:


    def setVersionCheck(self, value, note):
        _STRNAME = "setVersionCheck - "
        if value is True:
            if self._VERSION_CHECK is not False:
                self._VERSION_CHECK = True
                Domoticz.Log("Plugin allowed to start (triggered by: "+note+")")
        elif value is False:
            self._VERSION_CHECK = False
            Domoticz.Error("Plugin NOT allowed to start (triggered by: "+note+")")

    def mqtt_conn(self):
        _STRNAME = "mqtt_conn :"
        self._MQTT_CONN = mqtt.Client()
        self._MQTT_CONN.username_pw_set(self._MQTT_USERNAME, self._MQTT_PASSWORD)
        self._MQTT_CONN.connect(self._MQTT_HOST, int(self._MQTT_PORT), 30)
        self._MQTT_CONN.loop_start()

    def enphase_stream(self):
        _STRNAME = "enphase_stream: "
        _URL = "http://%s/stream/meter" % Parameters["Mode1"]
        Domoticz.Log("URL = "+_URL)
        stream_meter = requests.get(_URL, auth=self._ENPHASE_AUTH, stream=True, timeout=5)
        for item in stream_meter.iter_lines():
            if item.startswith(self._MARKER):
                json_data = json.loads(item.replace(self._MARKER, b''))
                json_string= json.dumps(json_data)
                #Domoticz.Log(_STRNAME+"JSON: "+json_string)
                self._MQTT_CONN.publish(topic=self._MQTT_TOPIC, payload=json_string, qos=0)


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def LogMessage(Message):
    _STRNAME = "LogMessage: "
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Debug(_STRNAME+"File written")

def DumpHTTPResponseToLog(httpResp, level=0):
    _STRNAME = "DumpHTTPResponseToLog: "
    if (level==0): Domoticz.Debug(_STRNAME+"HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(_STRNAME+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(_STRNAME+indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(_STRNAME+indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(_STRNAME+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")

def is_whole(n):
    return n % 1 == 0

def UpdateDevice(Unit, nValue, sValue, Image=None):
    _STRNAME = "UpdateDevice: "
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or ((Image != None) and (Image != Devices[Unit].Image)):
            if (Image != None) and (Image != Devices[Unit].Image):
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue), Image=Image)
                Domoticz.Log(_STRNAME+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
            else:
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Log(_STRNAME+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")

    # Generic helper functions
def DumpConfigToLog():
    _STRNAME = "DumpConfigToLog: "
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug(_STRNAME+"'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug(_STRNAME+"Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug(_STRNAME+"Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug(_STRNAME+"Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug(_STRNAME+"Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug(_STRNAME+"Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug(_STRNAME+"Device LastLevel: " + str(Devices[x].LastLevel))
    return
