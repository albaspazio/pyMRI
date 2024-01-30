class BayesSubjectsEncoder:

    encoder = {"a":"01", "b":"02", "c":"03", "d":"04", "e":"05", "f":"06", "g":"07", "h":"08", "i":"09", "j":"10", "k":"11", "l":"12", "m":"13",
               "n":"14", "o":"15", "p":"16", "q":"17", "r":"18", "s":"19", "t":"20", "u":"21", "v":"22", "w":"23", "x":"24", "y":"25", "z":"26" }

    def name2code(self, surname, name, month, birth_year):

        name    = name[0:2].lower()
        sname   = surname[0:2].lower()

        if surname[0:3].lower() in ["d'"]:
            sname = "d" + surname[2:3].lower()
        elif surname[0:3].lower() in ["di ", "de ", "da ", "do "]:
            sname = "d" + surname[3:4].lower()
        elif surname[0:4].lower() in ["del ", "dal "]:
            sname = "d" + surname[4:5].lower()
        elif surname[0:5].lower() in ["dall'"]:
            sname = "d" + surname[5:6].lower()
        else:
            sname = surname[0:2].lower()

        if month < 10:
            month = "0" + str(month)
        else:
            month = str(month)

        birth_year = str(birth_year)[2:]

        return self.encoder[sname[0]] + self.encoder[sname[1]] + month + birth_year + self.encoder[name[0]] + self.encoder[name[1]]

    def code2name(self, code:str):

        surname = [code[0:2], code[2:4]]
        name    = [code[8:10], code[10:]]

        month   = code[4:6]
        year    = code[6:8]

        return self.value2key(surname[0]) + self.value2key(surname[1]) + self.value2key(name[0]) + self.value2key(name[1]) + month + year

    def value2key(self, value) -> str:

        for i,v in enumerate(list(self.encoder.values())):
            if v == value:
                return list(self.encoder.keys())[i]

