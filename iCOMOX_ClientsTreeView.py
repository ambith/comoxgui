import TCP_connectivity
import iCOMOX_datahandling
import tkinter as tk
from tkinter import ttk
import iCOMOX_messages
import messages_utils
import common
import helpers
import datetime
import iCOMOX_list

class cClientsTreeView():
    def __init__(self, parent, on_select_client_command, clientsType, namewidth_arr):
        self.parent = parent

        self.clientsType = clientsType
        self.on_select_client_command = on_select_client_command

        self.tree_clients = ttk.Treeview(self.parent, selectmode="browse", columns=tuple(range(1, len(namewidth_arr)+1)))
        self.tree_clients.grid(row=0, column=0, padx=5, pady=0)
        self.tree_clients.bind("<Button-1>", self.on_treeview_click)
        self.tree_clients.bind("<Motion>", self.on_treeview_click)
        self.tree_clients.bind("<<TreeviewSelect>>", self.on_treeview_select)

        self.tree_clients.column(column="#0", width=40, minwidth=40, stretch=tk.NO)   # index
        self.tree_clients.heading(column="#0", text="", anchor=tk.CENTER)
        for col in range(1, len(namewidth_arr)+1):
            self.tree_clients.column(column=col, width=namewidth_arr[col-1][0], minwidth=namewidth_arr[col-1][0], anchor=tk.CENTER, stretch=tk.NO)
            self.tree_clients.heading(column=col, text=namewidth_arr[col-1][1], anchor=tk.CENTER)

    # disabling resizing of the treeview columns
    def on_treeview_click(self, event):
        if self.tree_clients.identify_region(event.x, event.y) == "separator":
            return "break"

    def on_treeview_select(self, event):
        IDs = self.tree_clients.selection()
        if len(IDs) == 0:
            common.iCOMOXs.current = None
        else:
            iComox = self.ItemID_to_iComox(IDs[0])
            common.iCOMOXs.current = iComox
            if callable(self.on_select_client_command):
                self.on_select_client_command(iComox=iComox)

    def deselect_items(self):
        for item_id in self.tree_clients.selection():
            self.tree_clients.selection_remove(item_id)
            if common.iCOMOXs.current == self.ItemID_to_iComox(ID_str=item_id):
                common.iCOMOXs.current = None
                return True
        return False

    def ItemID_to_iComox(self, ID_str):
        UniqueID = bytearray.fromhex(ID_str)
        return common.iCOMOXs.find_by_UniuqeID(UniqueID=UniqueID, TypesBitmask=self.clientsType)

    def insert(self, iComox, index=tk.END):
        if (iComox is None) or (iComox.Hello is None) or (iComox.Type != self.clientsType):
            return None
        UniqueID = iComox.UniqueID()
        if iComox.Type == iCOMOX_list.cCLIENT_TYPE_USB:
            return None
        elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
            columns = (messages_utils.iCOMOX_BoardType_to_Str(iComox.board_type()), helpers.bytearrayToString(iComox.Name()), UniqueID.hex().upper(), helpers.u8s_to_str(iComox.macAddress, ":", ""), str(iComox.moteID))
        elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
            if iComox.socket is None:
                return None
            columns = (messages_utils.iCOMOX_BoardType_to_Str(iComox.board_type()), helpers.bytearrayToString(iComox.Name()), UniqueID.hex().upper(), str(iComox.remoteAddress), str(iComox.remotePort))
        else:
            return None
        item_id = ''.join(format(x, '02x') for x in UniqueID)
        if self.tree_clients.exists(item_id):
            self.tree_clients.item(item_id)
        else:
            self.tree_clients.item(self.tree_clients.insert(parent="", id=item_id, index=index, values=columns))
        # iComox = self.ItemID_to_iComox(ID_str=item_id)
        iComox.ConnectionTime = datetime.datetime.now()

    def delete(self, iComox):
        if common.iCOMOXs.current == iComox:
            common.iCOMOXs.current = None
        for item_id in self.tree_clients.get_children():
            if item_id is not None:
                iCmx = self.ItemID_to_iComox(ID_str=item_id)
                if iCmx is not None and (iCmx == iComox):
                    self.tree_clients.delete(item_id)
                    return

    def deleteZombieClients(self):
        selected_items = self.tree_clients.selection()
        for item_id in self.tree_clients.get_children():
            if item_id is not None:
                iCmx = self.ItemID_to_iComox(ID_str=item_id)
                if iCmx is None:
                    if item_id in selected_items:
                        common.iCOMOXs.current = None
                    self.tree_clients.delete(item_id)

    def delete_all(self):
        items_id = self.tree_clients.get_children()
        for item_id in items_id:
            self.tree_clients.delete(item_id)
        common.iCOMOXs.current = None
