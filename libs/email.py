import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from string import Template


class Email:
    @classmethod
    def send(cls, account, receivers, message, attachment=None):
        successfull = False
        try:
            if attachment:
                successfull = False
                print('attachment is not supported yet!')
                pass
            else:
                message['From'] = account['lid']
                message['To'] = ','.join(receivers)
                client = smtplib.SMTP()
                client.connect('smtp.glittergroupcn.com')
                client.login(account['lid'], account['lpwd'])
                client.sendmail(account['lid'], receivers, message.as_string())
                successfull = True
            print('邮件发送成功！')
        except smtplib.SMTPRecipientsRefused:
            print('邮件发送失败，收件人被拒绝')
        except smtplib.SMTPAuthenticationError:
            print('邮件发送失败，认证错误')
        except smtplib.SMTPSenderRefused:
            print('邮件发送失败，发件人被拒绝')
        except smtplib.SMTPException as e:
            print('邮件发送失败, ', e.message)
        finally:
            client.quit()
        return successfull

    @classmethod
    def message_of_product_catalog(cls, market, account, buyer):
        catalog_href = "https://drive.google.com/open?id=1k4FpNqe9Klg0lQt77iNRdBDKGuaWtelv"
        file = market['directory'] + '_config//templates//email_template_product_catalog.html'
        with open(file, 'r') as f:
            text = f.read()
        t = Template(text)
        params = {'buyer': buyer, 'sender': account['lname'], 'catalog_href':catalog_href, 'homepage': market['homepage'], 'email': account['lid'], 'whatsapp': account['mobile']}
        content = t.substitute(params)
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] = '2019 Glitter Eyelash Product Catalog'
        return msg