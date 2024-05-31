class BayesSubjectsEncoder:
    """
    This class provides methods for encoding and decoding subject names into a compact representation using a lookup table.

    - The encoding process involves converting each character in the subject name into a numeric value based on its position in a lookup table.
    takes four parameters: surname, name, month, and birth_year. It converts each character in the subject name into a numeric value based on its position in the lookup table, and then combines the values into a single code.
    - The decoding method takes a single parameter: code. It splits the code into its components (surname, name, month, and birth_year), and then converts each component back into its original character representation.

    The value2key method takes a single parameter: value. It searches the lookup table for the key that corresponds to the specified value.
    The decode_list method takes a single parameter: encoded_list. It converts a list of codes into a list of subject names by calling the code2name method for each code in the list.
    """

    encoder = {"a":"01", "b":"02", "c":"03", "d":"04", "e":"05", "f":"06", "g":"07", "h":"08", "i":"09", "j":"10", "k":"11", "l":"12", "m":"13",
               "n":"14", "o":"15", "p":"16", "q":"17", "r":"18", "s":"19", "t":"20", "u":"21", "v":"22", "w":"23", "x":"24", "y":"25", "z":"26" }

    def __init__(self):
        """
        Initialize the encoder with a set of common characters that are likely to be used in subject names.
        """
        self.encoder = {"a":"01", "b":"02", "c":"03", "d":"04", "e":"05", "f":"06", "g":"07", "h":"08", "i":"09", "j":"10", "k":"11", "l":"12", "m":"13",
               "n":"14", "o":"15", "p":"16", "q":"17", "r":"18", "s":"19", "t":"20", "u":"21", "v":"22", "w":"23", "x":"24", "y":"25", "z":"26" }

    # Rossi, Mario, 11, 1972  => ros, mar, 11, 72 =>  18 15 19    11     72     13 01 18 => 1815191172130118
    def name2code(self, surname, name, month, birth_year):
        """
        Encode a subject name into a compact representation.

        Args:
            surname (str): Surname of the subject
            name (str): Given name of the subject
            month (int): Month of birth
            birth_year (int): Year of birth

        Returns:
            str: Compact representation of the subject name

        """
        name    = name[0:3].lower()
        sname   = surname[0:3].lower()

        if surname[0:2].lower() in ["d\'", "d'"]:
            sname = "d" + surname[2:4].lower()
        elif surname[0:2].lower() in ["l'", "l\'"]:
            sname = "d" + surname[2:4].lower()
        elif surname[0:3].lower() in ["di ", "de ", "da ", "do "]:
            sname = "d" + surname[3:5].lower()
        elif surname[0:3].lower() in ["la ", "lo ", "le ", "li "]:
            sname = "l" + surname[3:5].lower()
        elif surname[0:3].lower() in ["il "]:
            sname = "i" + surname[3:5].lower()
        elif surname[0:4].lower() in ["del ", "dal "]:
            sname = "d" + surname[4:6].lower()
        elif surname[0:5].lower() in ["dall'", "dell'", "dall\'", "dell\'"]:
            sname = "d" + surname[5:7].lower()
        else:
            sname = surname[0:3].lower()

        if month < 10:
            month = "0" + str(month)
        else:
            month = str(month)

        birth_year = str(birth_year)[2:]
        try:
            return self.encoder[sname[0]] + self.encoder[sname[1]] + self.encoder[sname[2]] + month + birth_year + self.encoder[name[0]] + self.encoder[name[1]] + self.encoder[name[2]]
        except:
            a=1

    # 1815191172130118 =>  18 15 19    11     72     13 01 18   Rossi, Mario, 11, 1972  => ros, mar, 11, 72 =>

    def code2name(self, code:str):
        """
        Decode a compact representation of a subject name.

        Args:
            code (str): Compact representation of the subject name

        Returns:
            str: Decoded subject name

        """
        surname = [code[0:2], code[2:4], code[4:6]]
        name    = [code[10:12], code[12:14], code[14:16]]

        month   = code[6:8]
        year    = code[8:10]

        return self.value2key(surname[0]) + self.value2key(surname[1]) + self.value2key(surname[2]) + "|" + self.value2key(name[0]) + self.value2key(name[1]) + self.value2key(name[2]) + "|" + month + year

    def value2key(self, value) -> str:
        """
        Convert a numeric value to a character key.

        Args:
            value (str): Numeric value

        Returns:
            str: Corresponding character key
        """
        for i,v in enumerate(list(self.encoder.values())):
            if v == value:
                return list(self.encoder.keys())[i]

    def decode_list(self, encoded_list):
        """
        Decode a list of compact representations of subject names.

        Args:
            encoded_list (list): List of compact representations of subject names

        Returns:
            list: List of decoded subject names

        """
        return [self.code2name(code) for code in encoded_list]