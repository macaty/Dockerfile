#!/bin/env python
#encoding: utf-8
from pysnmp.entity import engine, config
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
from miscellaneous.SMS import SMS_Send
from miscellaneous.SMTP import Async_smtp
from miscellaneous.Config_Reader import yconfig_read
import logging
import logging.config
import os
import argparse

parser = argparse.ArgumentParser(description='SNMP carrier')
parser.add_argument('-f', '--configure', type=str,required=True,help='specify a config file path')
args = parser.parse_args()

Configure = args.configure

logging.config.fileConfig("%s/logger.conf"%(Configure))
logger = logging.getLogger("snmp")

# Create SNMP engine with autogenernated engineID and pre-bound
# to socket transport dispatcher
snmpEngine = engine.SnmpEngine()
try:
  config_file = "%s/config.yml" %(Configure)
  user_file = "%s/user.yml" %(Configure)
  conf = yconfig_read(config_file)
  api = conf.get('SMS').get('api')
  mail_host = conf.get('SMTP').get('host')
  oid = conf.get('SNMP').get('oid')
  snmp_user = conf.get('SNMP').get('SNMPUSER').get('NAME')
  snmp_pwd = conf.get('SNMP').get('SNMPUSER').get('PASSWORD')
except Exception as e:
  logger.error('Some error in configfile %s'%(e))

SENDER = os.environ.get('SENDER')
SENDER_PWD = os.environ.get('SENDER_PWD')

if not SENDER or not SENDER_PWD:
  logger.warn('Either smtp env not set ')

Send_mail = Async_smtp(mail_host=mail_host,sender=SENDER,sender_pwd=SENDER_PWD)
# Transport setup

# UDP over IPv4
config.addSocketTransport(
    snmpEngine,
    udp.domainName,
    udp.UdpTransport().openServerMode(('0.0.0.0', 162))
)

# SNMPv3/USM setup

# user: usr-sha-aes128, auth: SHA, priv AES
config.addV3User(
    #snmpEngine, 'usr-sha-aes128',
    snmpEngine, snmp_user,
    #Add snmpv3 user
    config.usmHMACSHAAuthProtocol, snmp_pwd,
    #Auth SHA			    #password
    config.usmAesCfb128Protocol, snmp_pwd
    #Use Aes 			    #password
)

# Callback function for receiving notifications
def cbFun(snmpEngine,
          stateReference,
          contextEngineId, contextName,
          varBinds,
          cbCtx):
  logger.info('Notification received, ContextEngineId "%s", ContextName "%s"' % (
        contextEngineId.prettyPrint(), contextName.prettyPrint()
        )
    )
  subject = "stateReference {} TransportInfo {}".format(stateReference,snmpEngine.msgAndPduDsp.getTransportInfo(stateReference))
  logger.info(subject)
    #get remote address
  users = yconfig_read(user_file)
  emaillist = users.get('alertobj').get('mail')
  smslist = users.get('alertobj').get('sms') 
  for name, val in varBinds:
    if name.prettyPrint() == oid:
      msg=val.prettyPrint()
      logger.info(msg)
      if not msg.__cotains__('Patrol'):
        logger.info("send alert message".center(50,"#"))
        for phone_number in smslist:
          response = SMS_Send(api,phone_number,"%s\n%s"%(subject,msg),timeout=5)
          sms_result = response.get('msg')
          if sms_result == 'ok':
            logger.info("%s send ok" %(phone_number))
          else:
            logger.warn("%s send error,msg:%s" %(phone_number,sms_result))
        smtp_result = Send_mail.Send_txt_mail(emaillist, msg, subject)
        if smtp_result.get('status'):
          logger.info("send email ok")
        else:
          logger.warn("send email error %s"%(smtp_result.get('error')))
      else:
        logger.info("ingore msg: %s") %(msg,)
# Register SNMP Application at the SNMP engine
ntfrcv.NotificationReceiver(snmpEngine, cbFun)

snmpEngine.transportDispatcher.jobStarted(1) # this job would never finish

# Run I/O dispatcher which would receive queries and send confirmations
try:
    logger.info('Service start')
    snmpEngine.transportDispatcher.runDispatcher()
except Exception as e:
    logger.warn('Service Error %s' %(e))
    snmpEngine.transportDispatcher.closeDispatcher()
