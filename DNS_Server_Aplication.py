import tkinter as tk
import os
import sqlite3
from tkinter import messagebox
import dns.message
import dns.query
import dns.resolver
import socket
import threading
import tkinter.ttk as ttk


DNS_PORT = 53
DNS_RECORD_DB_PATH = os.path.join(os.getcwd(), 'DNS_Record.db')
FONT = "Arial"
FONT_SIZE = "10"
FONT_SIZE_HEADER = "12"

class DNSServer:
    #def __init__(self):
        #self.run_dns_server()
        
    def get_local_ip_address(self) -> str:
        """ローカルホストのIPアドレスを取得する"""
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def create_dns_socket(self, ip_address: str) -> socket.socket:
        """DNS用のUDPソケットを作成する"""
        dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_socket.bind((ip_address, DNS_PORT))
        return dns_socket

    def search_dns_record(self, hostname: str) -> str:
        """指定されたホスト名に対応するIPアドレスを検索する"""
        try:
            with sqlite3.connect(DNS_RECORD_DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM DNS_Record WHERE hostname=?", (hostname,))
                data = cur.fetchone()
                if data is not None:
                    return data[3]
                else:
                    return None
        except Exception as e:
            print(f"Error while searching DNS record for hostname {hostname}: {e}")
            return None

    def create_dns_response(self, request: dns.message.Message) -> dns.message.Message:
        """DNSリクエストに対するDNS応答を生成する"""
        response = dns.message.make_response(request)
        for question in request.question:
            print(f"question      : {question}")
            print(f"question.name : {question.name}")
            if question.rdtype == dns.rdatatype.A:
                print(f"type          : {question.name}")
                hostname = str(question.name).replace(".home.ne.jp.", "")
                ip_address = self.search_dns_record(hostname)
                if ip_address:
                    rr = dns.rrset.from_text(question.name, 300, dns.rdataclass.IN, dns.rdatatype.A, ip_address)
                    response.answer.append(rr)
        return response

    def handle_dns_request(self, dns_socket: socket.socket) -> None:
        """DNSリクエストを受信して、DNS応答を送信する"""
        while True:
            data, client_address = dns_socket.recvfrom(1024)
            request = dns.message.from_wire(data)
            response = self.create_dns_response(request)
            dns_socket.sendto(response.to_wire(), client_address)
        
    def run_dns_server(self) -> None:
        """DNSサーバーを実行する"""
        ip_address = self.get_local_ip_address()
        self.dns_socket = self.create_dns_socket(ip_address)
        self.handle_dns_request(self.dns_socket)
        

class DNSApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.geometry('600x600')
        self.master.resizable(False, False)
        self.master.title('DNS Server')
        self.pack()
        self.create_menubar()
        self.create_frame()
        self.create_treeview()
        self.create_scrollbar()
        self.create_button()
        self.create_dropdown()
        self.create_entrybox()
    
    def create_frame(self) -> None:
        """フレームを作成するメソッド"""
        self.frame = tk.Frame(self.master, width=600, height=140)#, bg='red')
        self.frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.frame.propagate(False)
        self.frame_edit = tk.LabelFrame(self.frame, width=400, height=140, text="Edit Record")#, bg='red')
        self.frame_edit.pack(side = tk.LEFT, padx=(10,5),pady=(10,5), expand=True, fill=tk.BOTH)
        self.frame_edit.propagate(False)
        self.frame_onoff = tk.LabelFrame(self.frame, width=200, height=140, text="DNS Service")#, bg='blue')
        self.frame_onoff.pack(side = tk.LEFT, padx=(5,10),pady=(10,5), expand=True, fill=tk.BOTH)
        self.frame_onoff.propagate(False)
        self.frame_tree = tk.LabelFrame(self.master, width=600, height=460, text="DNS Record")#, bg='green')
        self.frame_tree.pack(side = tk.TOP, padx=(10,10),pady=(5,10), expand=True, fill=tk.BOTH)
        self.frame_tree.propagate(False)
        
    def create_scrollbar(self) -> None:
        """スクロールバーを作成するメソッド"""
        self.scrollbar_y = tk.Scrollbar(self.frame_tree, orient=tk.VERTICAL, width=25, command=self.tree.yview, bg='blue')
        self.scrollbar_y.grid(row=0, column=1, sticky=tk.N + tk.S, padx=(0,5),pady=(5,5))#.pack(side=tk.RIGHT, fill="y")#expand=True, fill=tk.BOTH)
        self.tree.configure(yscrollcommand=self.scrollbar_y.set)
        #self.scrollbar_x = tk.Scrollbar(self.frame_tree, orient=tk.HORIZONTAL, width=20, command=self.tree.yview)
        #self.scrollbar_x.grid(row=1, column=0, sticky=tk.W + tk.E)#.pack(side=tk.BOTTOM, fill="x")#expand=True, fill=tk.BOTH)
        #self.tree.configure(xscrollcommand=self.scrollbar_x.set)
        
    def create_treeview(self) -> None:
        """treeviewを作成するメソッド"""
        self.tree = ttk.Treeview(self.frame_tree, columns=("No","type", "hostname", "ip"), show='headings', height=17)
        self.tree.propagate(False)
        self.tree.grid(row=0, column=0, padx=(10,5),pady=(5,5), sticky = tk.N+tk.S+tk.E+tk.W)
        # フォント設定
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=(FONT, FONT_SIZE, "bold"), background='midnight blue', foreground='white')
        style.configure("Treeview", font=(FONT, FONT_SIZE))
        # 列
        self.tree.column('No',width=0, stretch='no')
        self.tree.column('type', anchor='center', width=100)
        self.tree.column('hostname',anchor='center', width=215)
        self.tree.column('ip', anchor='center', width=210)
        # ヘッダ
        self.tree.heading('No',text='No',anchor='center')
        self.tree.heading("type", text="type", anchor="center")
        self.tree.heading("hostname", text="hostname", anchor="center")
        self.tree.heading("ip", text="ip", anchor="center")
        # databaseから値取り出し
        data = self.get_db()
        for record in data:
            if record is not None:
                self.tree.insert("",tk.END, values=record)
                
    def create_entrybox(self) -> None:
        """DNSレコード編集用のウィジェットを作成するメソッド"""
        # hostnameを入力するボックス
        label_hostname = tk.Label(self.frame_edit, text='Hostname', font=(FONT,FONT_SIZE))
        label_hostname.grid(row=0, column=0, padx=(10,15),pady=(0,0))#pack(side = tk.TOP, padx=(10,10),pady=(0,0)) 
        self.txt_hostname = tk.Entry(self.frame_edit, width=30, font=(FONT,FONT_SIZE))
        self.txt_hostname.grid(row=1, column=0, padx=(10,15),pady=(0,0))#pack(side = tk.TOP, padx=(10,10),pady=(0,0))
        # ip adressを入力するボックス
        label_ip = tk.Label(self.frame_edit, text='IP Adress', font=(FONT,FONT_SIZE))
        label_ip.grid(row=2, column=0, padx=(10,15),pady=(0,0))#pack(side = tk.TOP, padx=(10,10),pady=(10,0))
        self.txt_ip = tk.Entry(self.frame_edit, width=30, font=(FONT,FONT_SIZE))
        self.txt_ip.grid(row=3, column=0, padx=(10,15),pady=(0,10))#pack(side = tk.TOP, padx=(10,10),pady=(0,0))
        # 入力したレコードをデータベースに追加するボタン
        self.add_button = tk.Button(self.frame_edit, text='add', width=8, font=(FONT,FONT_SIZE), default="active", command=self.add_record)
        self.add_button.grid(row=3, column=1, padx=(10,10),pady=(0,10))#pack(padx=(10,10), pady=(30,0), side = tk.TOP)
        # 選択したレコードをデータベースから削除するボタン
        self.delete_button = tk.Button(self.frame_tree, text='delete', width=10, font=(FONT,FONT_SIZE), default="active", command=self.delete_record)
        self.delete_button.grid(row=1, column=0, padx=(0,0),pady=(2,0))#pack(padx=(10,10), pady=(0,20), side = tk.TOP)
        
    def create_button(self) -> None:
        """DNS機能のon/offボタンを作成するメソッド"""
        # DNS機能をonにするボタン
        self.on_button = tk.Button(self.frame_onoff, text='on', height = 5, width=9, font=(FONT,FONT_SIZE), default="active", command=self.enable_dns)
        self.on_button.grid(row=0, column=0, padx=(15,10),pady=(10,10))#.pack(padx=(10,5), pady=(10,10), side = tk.LEFT)
        self.on_button.propagate(False)
        # DNS機能をoffにするボタン(ソケットを削除)
        self.off_button = tk.Button(self.frame_onoff, text='off',height = 5, width=9, font=(FONT,FONT_SIZE), default="active", command=self.disable_dns, state="disable")
        self.off_button.grid(row=0, column=1, padx=(10,10),pady=(10,10))#.pack(padx=(5,10), pady=(10,10), side = tk.LEFT)
        self.off_button.propagate(False)
        
    def create_dropdown(self) -> None:
        """レコードタイプのドロップダウンを作成するメソッド"""
        label_type = tk.Label(self.frame_edit, text='type', font=(FONT,FONT_SIZE))
        label_type.grid(row=0, column=1, padx=(12,10),pady=(0,0))
        module = ('A', 'AAAA', 'CNAME')
        self.dropdown = ttk.Combobox(self.frame_edit, height=3, width=8, font=(FONT,FONT_SIZE), justify="center", values=module)
        self.dropdown.grid(row=1, column=1, padx=(12,10),pady=(0,0))

    def create_menubar(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        menu_a = tk.Menu(
            menubar,
            tearoff=False,
        )
        # [MenuA] - [CommandA-1]
        menu_a.add_command(
            label="END",
            command=self.stop_aplication,
        )
        menubar.add_cascade(label="file", menu=menu_a)

    def get_db(self) -> list:
        """レコードを取得するメソッド"""
        # データベースに接続
        conn = sqlite3.connect(DNS_RECORD_DB_PATH)
        # カーソルを取得
        cur = conn.cursor()
        # レコードを取得
        cur.execute("SELECT * FROM DNS_Record")
        result = cur.fetchall()
        return result
    
    def add_record(self) -> None:
        """レコードを追加するメソッド"""
        hostname = self.txt_hostname.get()
        ip = self.txt_ip.get()
        type = self.dropdown.get()
        # hostname, ip, typeの全てに値が入っている時
        if hostname and ip and type:
            # データベースに接続
            conn = sqlite3.connect(DNS_RECORD_DB_PATH)
            # カーソルを取得
            cur = conn.cursor()
            # hostnameが既に登録されているか確認
            cur.execute("SELECT * FROM DNS_Record WHERE hostname = (?) LIMIT 1", (hostname,))
            x = cur.fetchone()
            if x :
                messagebox.showinfo('登録エラー',f'hostname : {hostname}は既に登録されています.')
            else:
                # insert文を実行
                cur.execute("INSERT INTO DNS_Record (type, hostname, ip) VALUES (?, ?, ?)", (type, hostname, ip))
                # 変更を保存
                conn.commit()
                # 接続を閉じる
                conn.close()
                # box内の文字消去
                self.txt_hostname.delete(0, tk.END)
                self.txt_ip.delete(0, tk.END)
                # レコードを追加
                text = (0, type, hostname, ip)
                self.tree.insert("", tk.END, values=text)
                messagebox.showinfo('確認', f'レコードを追加しました。\nhostname : {hostname}\nip : {ip}')
    
    def delete_record(self) -> None:
        """選択されたレコードを削除するメソッド"""
        selected_item = self.tree.selection()
        # 選択されている場合
        if selected_item:
            text = self.tree.item(selected_item[0])
            id = text["values"][0]
            ret = messagebox.askyesno('確認', '選択したレコードを削除しますか？')
            # 確認ダイアログで"はい"を押した場合
            if ret == True:
                # データベースに接続する
                conn = sqlite3.connect(DNS_RECORD_DB_PATH)
                # カーソルを取得する
                cur = conn.cursor()
                # delete文を実行
                cur.execute("DELETE FROM DNS_Record WHERE id=?", (id,))
                # 変更を保存する
                conn.commit()
                # 接続を閉じる
                conn.close()
                # 選択したレコードを削除
                self.tree.delete(selected_item)
    
    def enable_dns(self) -> None:
        """DNS機能を有効化するメソッド"""
        ret = messagebox.askyesno('確認', 'DNS機能を有効にしますか？')
        if ret == True:
            self.dns_server = DNSServer()
            self.resolver_thread = threading.Thread(target=self.dns_server.run_dns_server)
            self.resolver_thread.start()
            # ボタンの状態変化
            self.on_button["state"] = "disable"
            #self.on_button["bg"] = "gray"
            self.off_button["state"] = "normal"
        
    def disable_dns(self) -> None:
        """DNS機能を無効化するメソッド"""
        self.dns_server.dns_socket.close()
        messagebox.showinfo('確認', 'DNS機能を無効にしました。')
        self.off_button["state"] = "disable"
        self.on_button["state"] = "normal" 
        
    def stop_aplication(self):
        """アプリを終了するメソッド"""
        # 終了確認のメッセージ表示
        ret = messagebox.askyesno(
            title = "終了確認",
            message = "プログラムを終了しますか？")

        if ret == True:
            self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = DNSApplication(master=root)
    app.mainloop()