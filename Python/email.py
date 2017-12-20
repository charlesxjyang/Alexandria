    
def send_email(fromaddr,toaddr,name,graph,csv):    
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    fromaddr = "061099021866mlwgscalucb@gmail.com"
    toaddr = "061099021866mlwgscalucb@gmail.com"
     
    msg = MIMEMultipart()
     
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "SUBJECT OF THE EMAIL"
     
    body = ""
    firstline = "Hi "+name+','
    secondline = ("Thank you for using our app. "
                  "We have attached the data visualization you requested for the given queries and the csv for the underlying data."
                  "Please let us know if you have any issues or questions about where this data came from or how the visualization was made."
                  "Finally, if you have any questions, feedback, suggestions, or new ideas for how our service can be improved, please contact us!\n"
                  "Any inquiry can be made at this email.")
    closer = "We wish you the best of luck on all your future research endeavours and hope"
    signature = "Sincerely, \nCharles Yang \n Founder of Alexandria"
    body+=firstline + '\n\n' + secondline + '\n\n' + closer + '\n\n' + signature
    msg.attach(MIMEText(body, 'plain'))
    #first attachment
    filename=graph
    attachment = open(filename,'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)
    #second attachment
    filename=csv
    attachment = open(filename,'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)

    
#    for file in files:
#        filename = "NAME OF THE FILE WITH ITS EXTENSION"
#        attachment = open("PATH OF THE FILE", "rb")
#         
#        part = MIMEBase('application', 'octet-stream')
#        part.set_payload((attachment).read())
#        encoders.encode_base64(part)
#        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
#         
#        msg.attach(part)
    print('start query server')
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, 'passwiord')
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    
send_email()