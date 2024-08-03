import extract_msg


def join_mail(mail):
    return " ".join(" ".join(i) for i in mail if i)


class MsgParser:
    def __init__(self, input_path):
        self.msg = extract_msg.Message(input_path)

    def check_body(self):
        if self.msg.body:
            return True
        else:
            return False
        
    def check_reply_body(self):
        if "From: " in self.msg.body and "To: " in self.msg.body:
            return True
        else:
            return False

    def return_split(self, text, sp):
        if sp in text:
            return text.split(sp)
        else:
            return ["", text]
        
    def split_message(self, text):
        from_, text = self.return_split(text, "Sent: ")
        date, text = self.return_split(text, "To: ")
        to, text = self.return_split(text, "Cc: ")
        cc, text = self.return_split(text, "Subject: ")
        subject = text.split("\n")[0]
        body = "\n".join(text.split("\n")[1:])
        return [" ".join(i.split()) for i in [from_, to, date, subject, body]]

    def split_reply(self, text):
        return [self.split_message(i) for i in text]

    def get_parsed_text(self):
        tmp_mail = []

        if self.check_body():
            if self.check_reply_body():
                tmp_mail = [[join_mail(self.msg.sender), join_mail(self.msg.to),
                             self.msg.date, self.msg.subject, " ".join(self.msg.body.split("From: ")[0].split())]]
                tmp_mail.extend(self.split_reply(self.msg.body.split("From: ")[1:]))
            else:
                tmp_mail = [[join_mail(self.msg.sender), join_mail(self.msg.to), self.msg.date,
                             self.msg.subject, " ".join(self.msg.body.split())]]
        return tmp_mail
