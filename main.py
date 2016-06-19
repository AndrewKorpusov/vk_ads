# ---------------------------------------------------#
# -----------------GRAPHICS MANAGEMENT---------------#
# ---------------------------------------------------#
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import myVk
import userInfo
import urllib.parse
import re
import time

class Window(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.iconbitmap('clienticon.ico')
        self.title("Shum")
        self.geometry("250x100")
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame(StartPage)

    def show_frame(self, cont, *user):
        frame = cont(self.container, self, *user)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Авторизація")
        label.grid(row=1, column=1)
        tk.Label(self, text="Username:").grid(row=2, sticky="w")
        user = tk.Entry(self, width=15)
        user.grid(row=2, column=1)
        tk.Label(self, text="Password:").grid(row=3, sticky="w")
        password = tk.Entry(self, width=15, show="*")
        password.grid(row=3, column=1)
        b = ttk.Button(self, text="Увійти", width=10, command=lambda: self.login(user, password, controller))
        b.grid(row=4, column=1)

    def login(self, user, password, controller):
        username = user.get()
        passw = password.get()
        if len(username) > 0 and len(passw) > 0:
            token, user_id = myVk.auth(username, passw, "5113222", "wall")
            if (len(token) > 0 and len(user_id) > 0):
                model = userInfo.UserInfo(token, user_id)
                controller.show_frame(MainPage, model)


class MainPage(tk.Frame):
    def __init__(self, parent, controller, user):
        tk.Frame.__init__(self, parent)
        controller.geometry("600x400")
        label = tk.Label(self, text="Пошук груп")
        label.grid(row=1,sticky="ew")
        tk.Label(self, text="Введіть слова для пошуку").grid()
        search = tk.Entry(self, width=25)
        search.grid()

        tlabel = tk.Label(self, text="Тип")
        tlabel.grid()
        types = [("Усі", ""), ("Група", "group"), ("Сторінка", "page"), ("Зустріч", "event")]
        type_search = tk.StringVar()
        type_search.set("")
        for name, value in types:
            b1 = ttk.Radiobutton(self, text=name,
                                 variable=type_search, value=value)
            b1.grid(sticky="w")
        countries = myVk.get_countries(need_all=0, count=25)
        list = []
        for country in countries:
            for c in country:
                list.append(c)

        country = tk.StringVar()
        tk.Label(self, text="Виберіть країну").grid()

        ow = ttk.Combobox(self, textvariable=country, values=list)
        ow.current(0)
        ow.grid()
        c_label = tk.Label(self, text="Мін. кількість користувачів у групі")
        c_label.grid()
        cnt = tk.StringVar()
        cnt.set("0")
        user_count = tk.Entry(self, width=25, textvariable=cnt)
        user_count.grid()
        b = ttk.Button(self, text="Шукати", width=10,
                       command=lambda: self.findGroups(search, type_search, getCountryId(ow.get()), user, user_count))
        b.grid()

        tk.Label(self, text="Список груп", width=10).grid(row=2, column=3)

        def getCountryId(country):
            for temp in countries:
                for c in temp:
                    if c == country:
                        return temp[c]

    def findGroups(self, search, type, country, user, user_count):
        groups = myVk.searchGroups(access_token=user.token, q=urllib.parse.quote(search.get()), type=type.get(),
                                   country_id=country, v=5.37, count=1000, offset=0)
        self.listGroups(groups, user, user_count)

    def convert65536(self, s):
        #Converts a string with out-of-range characters in it into a string with codes in it.
        l=list(s)
        i=0
        while i<len(l):
            o=ord(l[i])
            if o>65535:
                l[i]="{"+str(o)+"ū}"
            i+=1
        return "".join(l)
    def parse65536(self, match):
        #This is a regular expression method used for substitutions in convert65536back()
        text=int(match.group()[1:-2])
        if text>65535:
            return chr(text)
        else:
            return "ᗍ"+str(text)+"ūᗍ"
    def convert65536back(self, s):
        #Converts a string with codes in it into a string with out-of-range characters in it
        while re.search(r"{\d\d\d\d\d+ū}", s)!=None:
            s=re.sub(r"{\d\d\d\d\d+ū}", self.parse65536, s)
        s=re.sub(r"ᗍ(\d\d\d\d\d+)ūᗍ", r"{\1ū}", s)
        return s

    def listGroups(self, groups, user, user_count):

        Lb1 = tk.Listbox(self, selectmode="extended", width=70)

        ids = []
        user_count = user_count.get()
        for group in groups:
            count = 0
            if int(user_count) > 0:
                count = myVk.get_user_count(group_id=group.get("id"))
            if int(user_count) <= count:
                Lb1.insert(group.get("id"), self.convert65536(group.get("name")))
                ids.append(group.get("id"))

        s = tk.Scrollbar(self, orient="vertical", command=Lb1.yview)
        Lb1.grid(row=4, column=3, rowspan=10, columnspan=70, sticky="w")

        selectAll = ttk.Button(self, text="Вибрати всі", command=lambda: Lb1.select_set(0, tk.END))
        selectAll.grid(row=3, column=3, sticky="w")

        deselect = ttk.Button(self, text="Прибрати виділення", command=lambda: Lb1.select_clear(0, tk.END))
        deselect.grid(row=3, column=3, sticky="e")

        Lb1.config(yscrollcommand=s.set)
        s.grid(row=4, column=4, rowspan=10, sticky="ns")
        
        def copyPaste(event):
            if (event.keycode == 88):
                self.clipboard_clear()
                self.clipboard_append(event.widget.get(tk.SEL_FIRST, tk.SEL_LAST))
                event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            if (event.keycode == 67):
                self.clipboard_clear()
                self.clipboard_append(event.widget.get(tk.SEL_FIRST, tk.SEL_LAST))
            elif (event.keycode == 86):
                event.widget.insert(tk.INSERT, self.clipboard_get())
                
        textarea = tk.Text(self, height=3, width=52)



        tk.Label(self,text="Текст").grid(row=15, column=3, sticky="w")
        textarea.grid(row=16, column=3, sticky="w")
        attachments = tk.Entry(self, width=70)
        tk.Label(self,text="Вкладення").grid(row=17, column=3, sticky="w")
        
        textarea.bind('<Control-KeyPress>', copyPaste)        
        attachments.bind('<Control-KeyPress>', copyPaste)
        
        attachments.grid(row=18, column=3, sticky="w")
        button = ttk.Button(self, text="Спамити;)", command=lambda: self.spam(Lb1, ids, textarea.get("1.0", tk.END), attachments.get(), user))
        button.grid(row=19, column=3, sticky="e")


    def spam(self, listbox, ids, message, attachments, user):
        selections = listbox.curselection()

        text = "Починаємо спамити у %s групах" % len(selections)
        self.show_spam_info(text)

        groups = []
        errors = 0
        i = 0
        for selection in selections:
            i = i+1
            id = "-%s" % ids[selection]

            response = myVk.spam(owner_id=id, message=urllib.parse.quote_plus(message), access_token=user.token,
                                    attachments=urllib.parse.quote(attachments))
            print(response)
            if (response.get('error')!=None):
                error = response.get('error')
                if (error.get('error_code') == 214):
                    text = "Перевищено ліміт повідомлень"
                    errors = 1
                    break
            else:
                groups.append(response)
            text = "Заспамлено %s груп (всього %s)" % (len(groups), i)
            self.show_spam_info(text)
            self.update()
            time.sleep(0.5)
        if (errors == 0 or len(groups)>0):
            text = "Заспамлено %s груп" % len(groups)
        self.show_spam_info(text)

    def show_spam_info(self, text):
        tk.Label(self, text=text).grid(row=20, column=3, sticky="ew")

root = Window()
root.mainloop()
