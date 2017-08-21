from BEEtec import connectNewPrinter

def alterSerialNumber(text):
    connNewPrinter = connectNewPrinter.Connection.getCmd()
    beeCmd = connNewPrinter.getCmd()
    beeCmd.setSerialNumber(text)