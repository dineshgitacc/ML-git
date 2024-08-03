import mailparser, csv

def join_mail(mail):
    return " ".join(" ".join(i) for i in mail if i)

class EmailParser:
    def __init__(self, input_path):
        self.mail = mailparser.parse_from_file(input_path)        
        
    def check_plain_text(self):
        if self.mail.text_plain:
            return True
        else:
            return False
        
    def check_body(self):
        if self.mail.body:
            return True
        else:
            return False
        
    def check_reply_body(self):
        if "From: " in self.mail.body and "To: " in self.mail.body:
            return True
        else:
            return False
        
    def check_reply_plain_text(self):
        if "From: " in self.mail.text_plain[0] and "To: " in self.mail.text_plain[0]:
            return True
        else:
            return False
        
    def check_mail_boundary(self):
        if "--- mail_boundary ---" in self.mail.body:
            return True
        else:
            return False
        
    def return_split(self, text, sp):
        return text.split(sp)
        
    def split_message(self, text):
        from_, text = self.return_split(text, "Sent: ")
        date, text = self.return_split(text, "To: ")
        to, text = self.return_split(text, "Cc: ")
        _, text = self.return_split(text, "Subject: ")
        subject = text.split("\n")[0]
        body = "\n".join(text.split("\n")[1:])
        return [" ".join(i.split()) for i in [from_, to, date, subject, body]]
        
    
    def split_reply(self, text):
        return [self.split_message(i) for i in text]
    
    def get_parsed_text(self):
        tmp_mail = []
        if self.check_plain_text():
            if self.check_reply_plain_text():
                tmp_mail = [[join_mail(self.mail.from_), join_mail(self.mail.to), self.mail.date.strftime("%d %B, %Y %H:%M"), self.mail.subject, " ".join(self.mail.text_plain[0].split("From: ")[0].split())]]
                tmp_mail.extend(self.split_reply(self.mail.text_plain[0].split("From: ")[1:]))
            else:
                tmp_mail = [[join_mail(self.mail.from_), join_mail(self.mail.to), self.mail.date.strftime("%d %B, %Y %H:%M"), self.mail.subject, " ".join(self.mail.text_plain[0].split())]]
        elif self.check_body():
            if self.check_reply_body():
                if self.check_mail_boundary():
                    tmp = self.mail.body.split("--- mail_boundary ---")[0]                    
                    tmp_mail = [[join_mail(self.mail.from_), join_mail(self.mail.to), self.mail.date.strftime("%d %B, %Y %H:%M"), self.mail.subject, " ".join(tmp.split("From: ")[0].split())]]
                    tmp_mail.extend(self.split_reply(tmp.split("From: ")[1:]))
                else:                    
                    tmp_mail = [[join_mail(self.mail.from_), join_mail(self.mail.to), self.mail.date.strftime("%d %B, %Y %H:%M"), self.mail.subject, " ".join(self.mail.body.split("From: ")[0].split())]]
                    tmp_mail.extend(self.split_reply(self.mail.body.split("From: ")[1:]))
            else:
                tmp_mail = [[join_mail(self.mail.from_), join_mail(self.mail.to), self.mail.date.strftime("%d %B, %Y %H:%M"), self.mail.subject, " ".join(self.mail.body.split())]]
        return tmp_mail
        # if tmp_mail:
            # print(tmp_mail)
            # with open(output_path, mode='w') as mail_details:
            #     mail_writer = csv.writer(mail_details, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            #     [mail_writer.writerow(i) for i in tmp_mail]



# check = EmailParser("/home/iopex/Downloads/sample.eml")
# check.get_csv("sample.csv")