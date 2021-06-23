import struct
import ipaddress
import iCOMOX_messages
import helpers

cMEMMAP_VERSION = 1
cMEMMAP_USED_PAGES = 20
cMEMMAP_SIZE = iCOMOX_messages.M24C64_PAGE_BYTE_SIZE * cMEMMAP_USED_PAGES

list_iCOMOX_PartNumber = ["SRT-COMOX-SM", "SRT-iCOMOX-NBIOT-SEC", "SRT-ICOMOX-POE-SEC"]

CipherSuitsArr = [
    0x0035,  # "TLS_RSA_WITH_AES_256_CBC_SHA",
    0x002F,  # "TLS_RSA_WITH_AES_128_CBC_SHA",
    0x0005,  # "TLS_RSA_WITH_RC4_128_SHA",
    0x0004,  # "TLS_RSA_WITH_RC4_128_MD5",
    0x000A,  # "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
    0x003D,  # "TLS_RSA_WITH_AES_256_CBC_SHA256",
    0xC011,  # "TLS_ECDHE_RSA_WITH_RC4_128_SHA",
    0xC012,  # "TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA",
    0xC013,  # "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
    0xC014,  # "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
    0xC027,  # "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
    0xC028,  # "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
    0xC02F,  # "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    0xFFFF  # "Support all"
]

def ValidPositiveInteger(string):
    return (len(string) > 0) and all(c in "0123456789" for c in string)

def ValidPLMNString(PLMN_string):
    return (len(PLMN_string) >= 5) and (len(PLMN_string) <= 6) and ValidPositiveInteger(PLMN_string)

class cMemMap():
    def __init__(self):
        self.memmap = None
        self.Clear()

    def Clear(self):
        self.memmap = bytearray(b"\xFF") * cMEMMAP_SIZE

    def AssignStringToMemMap(self, position, data, maxlen, fillchar=None):
        if len(data) > maxlen:
            data = data[:maxlen]
        if type(data) is str:
            data = bytearray(data, "utf-8", errors="ignore")
        self.memmap[position:position+len(data)] = data
        if fillchar is not None:
            self.memmap[position+len(data):position + maxlen] = fillchar * (maxlen - len(data))

    def StringFromMemMap(self, position, maxlen, fillchar):
        data = self.memmap[position:position+maxlen]
        index = data.find(fillchar)
        if index >= 0:
            data = data[:index]
        return str(data, "utf-8", errors="ignore")

    def WinToMemMap_Common(self, MemMapVersion, BoardType, BoardVersionMajor, BoardVersionMinor, PartNumber, SerialNumber, Name, ProductionSupport=False):
        if ProductionSupport:
            if len(SerialNumber) != 11:
                raise Exception("Serial number should be 11 characters")
            self.memmap[0] = MemMapVersion
            self.memmap[1] = int(BoardType)
            self.memmap[2] = int(BoardVersionMajor)
            self.memmap[3] = int(BoardVersionMinor)
            self.memmap[4:32] = b"\xFF" * 28

            self.AssignStringToMemMap(position=32, data=PartNumber, maxlen=32, fillchar=b"\xFF")
            self.AssignStringToMemMap(position=64, data=SerialNumber, maxlen=32, fillchar=b"\xFF")
        else:
            self.memmap[0:96] = b"\xFF" * 96
        self.AssignStringToMemMap(position=96, data=Name, maxlen=32, fillchar=b"\xFF")

    def MemMapToWin_Common(self):
        MemMapVersion = int(self.memmap[0])
        BoardType = int(self.memmap[1])
        BoardVersionMajor = int(self.memmap[2])
        BoardVersionMinor = int(self.memmap[3])
        PartNumber = self.StringFromMemMap(position=32, maxlen=32, fillchar=b"\xFF")
        SerialNumber = self.StringFromMemMap(position=64, maxlen=32, fillchar=b"\xFF")
        Name = self.StringFromMemMap(position=96, maxlen=32, fillchar=b"\xFF")
        return MemMapVersion, BoardType, BoardVersionMajor, BoardVersionMinor, PartNumber, SerialNumber, Name

    def WinToMemMap_SSL(self, addr_in_memmap, SSL_Enable, SSL_version, SSL_SecLevel, SSL_CipherSuite, SSL_NegotiateTimeout, SSL_IgnoreLocalTime):
        self.memmap[addr_in_memmap:addr_in_memmap+32] = b"\xFF" * 32
        # self.AssignStringToMemMap(position=addr_in_memmap,    data=SSL_CACertFile,      maxlen=32, fillchar=b"\xFF")
        # self.AssignStringToMemMap(position=addr_in_memmap+32, data=SSL_ClientCertFile,  maxlen=32, fillchar=b"\xFF")
        # self.AssignStringToMemMap(position=addr_in_memmap+64, data=SSL_ClientKeyFile,   maxlen=32, fillchar=b"\xFF")
        self.memmap[addr_in_memmap] = CipherSuitsArr[SSL_CipherSuite] & 0xFF
        self.memmap[addr_in_memmap+1] = CipherSuitsArr[SSL_CipherSuite] >> 8
        self.memmap[addr_in_memmap+2] = SSL_NegotiateTimeout & 0xFF
        self.memmap[addr_in_memmap+3] = SSL_NegotiateTimeout >> 8
        self.memmap[addr_in_memmap+4] = (SSL_version & 0x07) + ((SSL_SecLevel & 0x03) << 4) + ((SSL_IgnoreLocalTime & 0x01) << 6) + ((SSL_Enable & 0x01) << 7)
        self.memmap[addr_in_memmap+5:addr_in_memmap+31] = b"\xFF" * 127

    def MemMapToWin_SSL(self, addr_in_memmap):
        # SSL_CACertFile      = str(self.StringFromMemMap(position=addr_in_memmap,    maxlen=32, fillchar=b"\xFF"), "utf8")
        # SSL_ClientCertFile  = str(self.StringFromMemMap(position=addr_in_memmap+32, maxlen=32, fillchar=b"\xFF"), "utf8")
        # SSL_ClientKeyFile   = str(self.StringFromMemMap(position=addr_in_memmap+64, maxlen=32, fillchar=b"\xFF"), "utf8")
        try:
            SSL_CipherSuite = CipherSuitsArr.index((self.memmap[addr_in_memmap+1] << 8) + self.memmap[addr_in_memmap])
        except:
            SSL_CipherSuite = len(CipherSuitsArr)-1
        finally:
            pass
        SSL_NegotiateTimeout = (self.memmap[addr_in_memmap+3] << 8) + self.memmap[addr_in_memmap+2]
        if SSL_NegotiateTimeout < 10:
            SSL_NegotiateTimeout = 10
        elif SSL_NegotiateTimeout > 300:
            SSL_NegotiateTimeout = 300
        SSL_version = self.memmap[addr_in_memmap+4] & 0x07
        if SSL_version > 4:
            SSL_version = 0
        SSL_SecLevel = (self.memmap[addr_in_memmap+4] >> 4) & 0x03
        if SSL_SecLevel > 2:
            SSL_SecLevel = 0
        SSL_IgnoreLocalTime = 0 != (self.memmap[addr_in_memmap+4] & 0x40)
        SSL_Enable = 0 != (self.memmap[addr_in_memmap+4] & 0x80)
        return SSL_Enable, SSL_version, SSL_SecLevel, SSL_CipherSuite, SSL_NegotiateTimeout, SSL_IgnoreLocalTime

    def WinToMemMap_MQTT(self, addr_in_memmap, MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud):
        self.AssignStringToMemMap(position=addr_in_memmap,      data=MQTT_ServerURL,    maxlen=128, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=addr_in_memmap+32*4, data=MQTT_UserName,     maxlen=32,  fillchar=b"\xFF")
        self.AssignStringToMemMap(position=addr_in_memmap+32*5, data=MQTT_Password,     maxlen=32,  fillchar=b"\xFF")
        self.AssignStringToMemMap(position=addr_in_memmap+32*6, data=MQTT_ClientID,     maxlen=32,  fillchar=b"\xFF")
        self.memmap[addr_in_memmap+32*7] = MQTT_ServerPort & 0xFF
        self.memmap[addr_in_memmap+32*7+1] = (MQTT_ServerPort >> 8) & 0xFF
        self.memmap[addr_in_memmap+32*7+2] = MQTT_Cloud
        self.memmap[addr_in_memmap+32*7+3] = ((MQTT_ProvideUserName & 0x01) << 7) +((MQTT_ProvidePassword & 0x01) << 6)    # flags
        self.memmap[addr_in_memmap+32*7+4] = MQTT_Keepalive & 0xFF
        self.memmap[addr_in_memmap+32*7+5] = (MQTT_Keepalive >> 8) & 0xFF
        self.memmap[addr_in_memmap+32*7+6:addr_in_memmap+32*7+32] = b"\xFF" * 28

    def MemMapToWin_MQTT(self, addr_in_memmap):
        MQTT_ServerURL      = self.StringFromMemMap(position=addr_in_memmap,        maxlen=128, fillchar=b"\xFF")
        MQTT_UserName       = self.StringFromMemMap(position=addr_in_memmap+32*4,   maxlen=32,  fillchar=b"\xFF")
        MQTT_Password       = self.StringFromMemMap(position=addr_in_memmap+32*5,   maxlen=32,  fillchar=b"\xFF")
        MQTT_ClientID       = self.StringFromMemMap(position=addr_in_memmap+32*6,   maxlen=32,  fillchar=b"\xFF")
        MQTT_ServerPort     = (self.memmap[addr_in_memmap+32*7+1] << 8) + self.memmap[addr_in_memmap+32*7]
        MQTT_Cloud          = self.memmap[addr_in_memmap+32*7+2] & 0x01
        MQTT_ProvideUserName = 0 != (self.memmap[addr_in_memmap+32*7+3] & 0x80)
        MQTT_ProvidePassword = 0 != (self.memmap[addr_in_memmap + 32 * 7 + 3] & 0x40)
        MQTT_Keepalive      = (self.memmap[addr_in_memmap+32*7+5] << 8) + self.memmap[addr_in_memmap+32*7+4]
        if MQTT_Cloud > 0:
            MQTT_Cloud = 0
        return MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud

    def WinToMemMap_TCP(self, addr_in_memmap, TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec):
        # Listen IP address
        # if TCP_IPv6:
        #     ip = ipaddress.IPv6Address(TCP_ServerURL).packed
        # else:
        #     ip = ipaddress.IPv4Address(TCP_ServerURL).packed
        # self.AssignStringToMemMap(position=addr_in_memmap, data=ip, maxlen=16, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=addr_in_memmap, data=TCP_ServerURL, maxlen=128, fillchar=b"\xFF")
        self.memmap[addr_in_memmap+128] = TCP_ServerPort & 0xFF
        self.memmap[addr_in_memmap+129] = ((TCP_ServerPort >> 8) & 0xFF)
        self.memmap[addr_in_memmap+130] = TCP_delayBeforeReconnectingSec & 0xFF
        # self.memmap[addr_in_memmap+131] = TCP_connectAttemptsCount & 0xFF
        # self.memmap[addr_in_memmap+132] = 0 #TCP_IPv6 & 0x01

    def MemMapToWin_TCP(self, addr_in_memmap):
        TCP_ServerURL = self.StringFromMemMap(position=addr_in_memmap, maxlen=128, fillchar=b"\xFF")
        TCP_ServerPort = (self.memmap[addr_in_memmap+129] << 8) + self.memmap[addr_in_memmap+128]
        TCP_delayBeforeReconnectingSec = self.memmap[addr_in_memmap+130]
        # TCP_connectAttemptsCount = self.memmap[addr_in_memmap+131]
        # TCP_Flags = self.memmap[addr_in_memmap+132]
        return TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec

    def WinToMemMap_Backbone(self, addr_in_memmap, BackboneProtocol, TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud):
        self.memmap[addr_in_memmap:addr_in_memmap+9*32] = b"\xFF" * (9*32)
        if BackboneProtocol == iCOMOX_messages.cBACKBONE_PROTOCOL_TCP:
            self.WinToMemMap_TCP(addr_in_memmap=addr_in_memmap, TCP_ServerURL=TCP_ServerURL, TCP_ServerPort=TCP_ServerPort, TCP_delayBeforeReconnectingSec=TCP_delayBeforeReconnectingSec)
        elif BackboneProtocol == iCOMOX_messages.cBACKBONE_PROTOCOL_MQTT:
            self.WinToMemMap_MQTT(addr_in_memmap=addr_in_memmap, MQTT_ServerURL=MQTT_ServerURL, MQTT_UserName=MQTT_UserName, MQTT_Password=MQTT_Password, MQTT_ClientID=MQTT_ClientID, MQTT_ServerPort=MQTT_ServerPort, MQTT_ProvideUserName=MQTT_ProvideUserName, MQTT_ProvidePassword=MQTT_ProvidePassword, MQTT_Keepalive=MQTT_Keepalive, MQTT_Cloud=MQTT_Cloud)

    def MemMapToWin_Backbone(self, addr_in_memmap, BackboneProtocol):
        TCP_ServerURL = TCP_ServerPort = TCP_delayBeforeReconnectingSec = MQTT_ServerURL = MQTT_UserName = MQTT_Password = MQTT_ClientID = MQTT_ServerPort = MQTT_ProvideUserName = MQTT_ProvidePassword = MQTT_Keepalive = MQTT_Cloud = None
        if BackboneProtocol == iCOMOX_messages.cBACKBONE_PROTOCOL_TCP:
            TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec = self.MemMapToWin_TCP(addr_in_memmap=addr_in_memmap)
        elif BackboneProtocol == iCOMOX_messages.cBACKBONE_PROTOCOL_MQTT:
            MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud = self.MemMapToWin_MQTT(addr_in_memmap=addr_in_memmap)
        return TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud

    def WinToMemMap_NBIOT(self, \
          UseDefSimConfiguration, AccessTechnologiesBitmask, GsmBandsBitmask, LteCatM1BandsBitmask, LteCatNB1BandsBitmask, ScanOrder, ServiceDomain, \
          ManualOperatorSelection, PLMN, \
          EnableRoaming, ContextType, Authentication, ApnAccessName, ApnUser, ApnPassword, \
          SSL_Enable, SSL_version, SSL_SecLevel, SSL_CipherSuite, SSL_NegotiateTimeout, SSL_IgnoreLocalTime, \
          BackboneProtocol, \
          TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
          MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud
          ):
        self.memmap[32*4:32*(cMEMMAP_USED_PAGES)] = b"\xFF" * (32*(cMEMMAP_USED_PAGES-4))
        # flags
        self.memmap[32*4] = (UseDefSimConfiguration & 0x01) + ((ManualOperatorSelection & 0x01) << 1) + ((EnableRoaming & 0x01) << 2) + ((ServiceDomain & 0x01) << 3)   # flags.flags
        self.memmap[32*4+1] = (AccessTechnologiesBitmask & 0x07) + ((ScanOrder & 0x07) << 3)                                                                            # flags.Access
        self.memmap[32*4+2] = (Authentication & 0x03) + ((ContextType & 0x03) << 2)                                                                                     # flags.Context
        self.memmap[32*4+3] = BackboneProtocol & 0x01                                                                                                                   # flags.protocols

        # PLMN
        if not ValidPLMNString(PLMN):
            PLMN = ""
        self.AssignStringToMemMap(position=32*4+4, data=PLMN, maxlen=6, fillchar=b"\xFF")

        # GSM bands bitmask
        self.memmap[32*4+10] = GsmBandsBitmask & 0xFF
        self.memmap[32*4+11] = (GsmBandsBitmask >> 8) & 0xFF

        # LTE cat M1 bands bitmask
        self.memmap[32*4+12] = LteCatM1BandsBitmask & 0xFF
        self.memmap[32*4+13] = (LteCatM1BandsBitmask >> 8) & 0xFF

        # LTE cat NB1 bands bitmask
        self.memmap[32*4+14] = LteCatNB1BandsBitmask & 0xFF
        self.memmap[32*4+15] = (LteCatNB1BandsBitmask >> 8) & 0xFF

        # Dummy
        # self.memmap[32*4+16:32*4+32] = b"\xFF" * 18

        self.AssignStringToMemMap(position=32*5, data=ApnAccessName, maxlen=32, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=32*6, data=ApnUser, maxlen=32, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=32*7, data=ApnPassword, maxlen=32, fillchar=b"\xFF")

        self.WinToMemMap_SSL(addr_in_memmap=32*8, SSL_Enable=SSL_Enable, SSL_version=SSL_version, SSL_SecLevel=SSL_SecLevel, SSL_CipherSuite=SSL_CipherSuite, SSL_NegotiateTimeout=SSL_NegotiateTimeout, SSL_IgnoreLocalTime=SSL_IgnoreLocalTime)

        self.WinToMemMap_Backbone(addr_in_memmap=32*9, BackboneProtocol=BackboneProtocol, \
              TCP_ServerURL=TCP_ServerURL, TCP_ServerPort=TCP_ServerPort, TCP_delayBeforeReconnectingSec=TCP_delayBeforeReconnectingSec, \
              MQTT_ServerURL=MQTT_ServerURL, MQTT_UserName=MQTT_UserName, MQTT_Password=MQTT_Password, MQTT_ClientID=MQTT_ClientID, MQTT_ServerPort=MQTT_ServerPort, MQTT_ProvideUserName=MQTT_ProvideUserName, MQTT_ProvidePassword=MQTT_ProvidePassword, MQTT_Keepalive=MQTT_Keepalive, MQTT_Cloud=MQTT_Cloud)

    def MemMapToWin_NBIOT(self):
        # flags.flags
        UseDefSimConfiguration = 0 != (self.memmap[32*4] & 0x01)
        ManualOperatorSelection = 0 != (self.memmap[32*4] & 0x02)
        EnableRoaming = 0 != (self.memmap[32*4] & 0x04)
        ServiceDomain = (self.memmap[32*4] >> 3) & 0x01
        # flags.Access
        AccessTechnologiesBitmask = self.memmap[32*4+1] & 0x07
        ScanOrder = (self.memmap[32*4+1] >> 3) & 0x07
        if ScanOrder > 5:
            ScanOrder = 0

        # flags.Context
        Authentication = self.memmap[32*4+2] & 0x03
        ContextType = (self.memmap[32*4+2] >> 2) & 0x03
        if ContextType > 2:
            ContextType = 0

        # flags.protocols
        BackboneProtocol = self.memmap[32*4+3] & 0x01
        if BackboneProtocol > 0:
            BackboneProtocol = 0

        # PLMN
        PLMN = self.StringFromMemMap(position=32*4+4, maxlen=6, fillchar=b"\xFF")
        if not ValidPLMNString(PLMN_string=PLMN):
            PLMN = ""
        # MNC = ((self.memmap[32*4+5] & 0x7F) << 8) + self.memmap[32*4+4]
        # MNCHas3Digits = 0 != (self.memmap[32*4+5] & 0x80)
        # MCC = (self.memmap[32*4+7] << 8) + self.memmap[32*4+6]

        # Bands bitmask
        GsmBandsBitmask = (self.memmap[32*4+11] << 8) + self.memmap[32*4+10]
        LteCatM1BandsBitmask = (self.memmap[32*4+13] << 8) + self.memmap[32*4+12]
        LteCatNB1BandsBitmask = (self.memmap[32*4+15] << 8) + self.memmap[32*4+14]

        ApnAccessName   = self.StringFromMemMap(position=32*5, maxlen=32, fillchar=b"\xFF")
        ApnUser         = self.StringFromMemMap(position=32*6, maxlen=32, fillchar=b"\xFF")
        ApnPassword     = self.StringFromMemMap(position=32*7, maxlen=32, fillchar=b"\xFF")

        SSL_Enable, SSL_version, SSL_SecLevel, SSL_CipherSuite, SSL_NegotiateTimeout, SSL_IgnoreLocalTime = self.MemMapToWin_SSL(addr_in_memmap=32*8)

        TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
        MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud = self.MemMapToWin_Backbone(addr_in_memmap=32*9, BackboneProtocol=BackboneProtocol)

        return  UseDefSimConfiguration, AccessTechnologiesBitmask, GsmBandsBitmask, LteCatM1BandsBitmask, LteCatNB1BandsBitmask, ScanOrder, ServiceDomain, \
                ManualOperatorSelection, PLMN,  \
                EnableRoaming, ContextType, Authentication, ApnAccessName, ApnUser, ApnPassword, \
                SSL_Enable, SSL_version, SSL_SecLevel, SSL_CipherSuite, SSL_NegotiateTimeout, SSL_IgnoreLocalTime, \
                BackboneProtocol, \
                TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
                MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud

    # def MemMapToWin_NBIOT(self):
    #     IPv6 = 0 != (self.memmap[148] & 1)
    #     TLS = 0 != (self.memmap[148] & 2)
    #     if IPv6:
    #         TcpServerIpAddr = ipaddress.IPv6Address(bytes(self.memmap[128:128+16])).exploded
    #     else:
    #         TcpServerIpAddr = ipaddress.IPv4Address(bytes(self.memmap[128:128+4])).exploded
    #     [TcpServerPort] = struct.unpack_from("<H", self.memmap, 144)
    #     connectAttemptsCount = self.memmap[146]
    #     delayBeforeConnectingSec = self.memmap[147]
    #     ApnAccessName = self.StringFromMemMap(position=32*5, maxlen=32, fillchar=b"\xFF")
    #     ApnUser = self.StringFromMemMap(position=32*6, maxlen=32, fillchar=b"\xFF")
    #     ApnPassword = self.StringFromMemMap(position=32*7, maxlen=32, fillchar=b"\xFF")
    #     return TcpServerIpAddr, TcpServerPort, connectAttemptsCount, delayBeforeConnectingSec, IPv6, TLS, ApnAccessName, ApnUser, ApnPassword

    def WinToMemMap_POE(self, \
                        StaticIpAddr, StaticMaskAddr, StaticDnsServerAddr, StaticGatewayAddr, IPv6, IPv6LocalLinkOnly, DHCP,  \
                        BackboneProtocol, \
                        TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
                        MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud):
        # TCP/IP interface
        clientIP = helpers.stringToIpAddress(StaticIpAddr)
        clientIP = bytearray() if clientIP is None else clientIP.packed
        Mask = helpers.stringToIpAddress(StaticMaskAddr)
        Mask = bytearray() if Mask is None else Mask.packed
        DnsServerAddr = helpers.stringToIpAddress(StaticDnsServerAddr)
        DnsServerAddr = bytearray() if DnsServerAddr is None else DnsServerAddr.packed
        GatewayIP = helpers.stringToIpAddress(StaticGatewayAddr)
        GatewayIP = bytearray() if GatewayIP is None else GatewayIP.packed
        self.AssignStringToMemMap(position=128, data=clientIP, maxlen=16, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=144, data=Mask, maxlen=16, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=160, data=DnsServerAddr, maxlen=16, fillchar=b"\xFF")
        self.AssignStringToMemMap(position=176, data=GatewayIP, maxlen=4, fillchar=b"\xFF")

        # Flags
        self.memmap[192] = 0
        if IPv6:
            self.memmap[192] |= 1
        if IPv6LocalLinkOnly:
            self.memmap[192] |= 2
        # if TLS:
        #     self.memmap[192] |= 4
        if DHCP:
            self.memmap[192] |= 8
        self.memmap[193] = BackboneProtocol & 0x01

        self.WinToMemMap_Backbone(addr_in_memmap=256, BackboneProtocol=BackboneProtocol, \
              TCP_ServerURL=TCP_ServerURL, TCP_ServerPort=TCP_ServerPort, TCP_delayBeforeReconnectingSec=TCP_delayBeforeReconnectingSec, \
              MQTT_ServerURL=MQTT_ServerURL, MQTT_UserName=MQTT_UserName, MQTT_Password=MQTT_Password, MQTT_ClientID=MQTT_ClientID, MQTT_ServerPort=MQTT_ServerPort, MQTT_ProvideUserName=MQTT_ProvideUserName, MQTT_ProvidePassword=MQTT_ProvidePassword, MQTT_Keepalive=MQTT_Keepalive, MQTT_Cloud=MQTT_Cloud)

    def MemMapToWin_POE(self):
        IPv6 = 0 != (self.memmap[192] & 1)
        IPv6LocalLinkOnly = 0 != (self.memmap[192] & 2)
        # TLS = 0 != (self.memmap[192] & 4)
        DHCP = 0 != (self.memmap[192] & 8)

        if IPv6:
            StaticIpAddr = ipaddress.IPv6Address(bytes(self.memmap[128:144])).exploded
            StaticMaskAddr = ipaddress.IPv6Address(bytes(self.memmap[144:160])).exploded
            StaticDnsServerAddr = ipaddress.IPv6Address(bytes(self.memmap[160:176])).exploded
            StaticGatewayAddr = ipaddress.IPv6Address(bytes(self.memmap[176:192])).exploded
        else:
            StaticIpAddr = ipaddress.IPv4Address(bytes(self.memmap[128:132])).exploded
            StaticMaskAddr = ipaddress.IPv4Address(bytes(self.memmap[144:148])).exploded
            StaticDnsServerAddr = ipaddress.IPv4Address(bytes(self.memmap[160:164])).exploded
            StaticGatewayAddr = ipaddress.IPv4Address(bytes(self.memmap[176:180])).exploded

        BackboneProtocol = self.memmap[193] & 0x01
        BackboneProtocol = iCOMOX_messages.cBACKBONE_PROTOCOL_TCP   # Remove in 2.8.1

        TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
        MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud = self.MemMapToWin_Backbone(addr_in_memmap=256, BackboneProtocol=BackboneProtocol)

        return  StaticIpAddr, StaticMaskAddr, StaticDnsServerAddr, StaticGatewayAddr, IPv6, IPv6LocalLinkOnly, DHCP, \
                BackboneProtocol, \
                TCP_ServerURL, TCP_ServerPort, TCP_delayBeforeReconnectingSec, \
                MQTT_ServerURL, MQTT_UserName, MQTT_Password, MQTT_ClientID, MQTT_ServerPort, MQTT_ProvideUserName, MQTT_ProvidePassword, MQTT_Keepalive, MQTT_Cloud
