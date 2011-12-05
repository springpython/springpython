# -*- coding: utf-8 -*-

"""
   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

# stdlib
import os
import sys
import random
import signal
import logging
import unittest
from struct import pack
from random import choice
from string import letters
from time import time, sleep
from binascii import hexlify, unhexlify
from xml.sax.saxutils import escape, unescape

try:
    import cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        from elementtree import ElementTree as etree

# Python 2.4 compat
try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

# pmock
from pmock import *

# ThreadPool
from threadpool import ThreadPool

# pymqi
import pymqi as mq
from pymqi import CMQC

# Spring Python
from springpython.config import XMLConfig
from springpython.context import ApplicationContext

from springpython.jms.factory import *
from springpython.jms import JMSException, WebSphereMQJMSException, NoMessageAvailableException
from springpython.jms.factory import _WMQ_MAX_EXPIRY_TIME, _WMQ_MQRFH_VERSION_2, \
    _WMQ_MQFMT_RF_HEADER_2, _WMQ_DEFAULT_CCSID, _WMQ_DEFAULT_ENCODING, MQRFH2JMS, \
    _WMQ_DEFAULT_ENCODING_WIRE_FORMAT, _WMQ_DEFAULT_CCSID_WIRE_FORMAT, \
    _WMQ_MQRFH_NO_FLAGS_WIRE_FORMAT, _mcd, unhexlify_wmq_id, _WMQ_ID_PREFIX
from springpython.jms.core import JmsTemplate, TextMessage, MessageConverter
from springpython.jms import DELIVERY_MODE_NON_PERSISTENT, \
    DELIVERY_MODE_PERSISTENT, DEFAULT_DELIVERY_MODE, RECEIVE_TIMEOUT_INDEFINITE_WAIT, \
    RECEIVE_TIMEOUT_NO_WAIT, DEFAULT_TIME_TO_LIVE
from springpython.jms.listener import MessageHandler, SimpleMessageListenerContainer, \
    WebSphereMQListener

random.seed()

logger = logging.getLogger("springpythontest.jms_websphere_mq_test_cases")

QUEUE_MANAGER = "SPRINGPYTHON1"
CHANNEL = "SPR.PY.TO.JAVA.1"
HOST = "localhost"
LISTENER_PORT = "1434"
DESTINATION = "SPRING.PYTHON.TO.JAVA.REQ.1"
PAYLOAD = "Hello from Spring Python and JMS!"

conn_info = "%s(%s)" % (HOST, LISTENER_PORT)

# A bit of gimmick, we can't use .eq, because timestamp will be different.
timestamp = "1247950158160"
raw_message = 'RFH \x00\x00\x00\x02\x00\x00\x00\xd8\x00\x00\x01\x11\x00\x00\x04\xb8MQSTR   \x00\x00\x00\x00\x00\x00\x04\xb8\x00\x00\x00L<mcd><Msd>jms_text</Msd><msgbody xmlns:xsi="dummy" xsi:nil="true" /></mcd>  \x00\x00\x00`<jms><Dst>queue:///SPRING.PYTHON.TO.JAVA.REQ.1</Dst><Tms>%s</Tms><Dlv>2</Dlv></jms>  %s' % (timestamp, PAYLOAD)
raw_message_before_timestamp = raw_message[:raw_message.find(timestamp)]
raw_message_after_timestamp = raw_message[raw_message.find(timestamp) + len(timestamp):len(raw_message)]

# Used in tests of message consumers
raw_message_for_get = 'RFH \x00\x00\x00\x02\x00\x00\x01d\x00\x00\x01\x11\x00\x00\x04\xb8MQSTR   \x00\x00\x00\x00\x00\x00\x04\xb8\x00\x00\x00 <mcd><Msd>jms_text</Msd></mcd>  \x00\x00\x00\xa8<jms><Dst>queue:///TEST</Dst><Rto>queue:///TEST</Rto><Tms>1252094680519</Tms><Exp>1252094803975</Exp><Cid>6026ff99-c249-40aa-9f9e-62a7c0a00403</Cid><Dlv>2</Dlv></jms>  \x00\x00\x00l<usr><abc>7b9be165-1151-4dec-be06-b7f876b2703b</abc><ZqC3>ed493e59-392c-45dd-9862-07847fd202b5</ZqC3></usr> b0f32f11-b531-4bbf-b985-77e795d77024'

# Queue name may be up to 48 characters (MQCHAR48 in cmqc.h)
queue_name_length = range(1,49)

class DummyController(object):
    def shutdown(self):
        pass

def get_rand_string(length):
    return "".join(choice(letters) for idx in range(length))

def condition_ignored(ignored):
    return True

def get_default_md():
    md = mq.md()
    md.PutDate = "20091023"
    md.PutTime = "19261676"

    return md

def get_simple_message_and_jms_template(mock):

    message = TextMessage()
    message.text = "Hi there."

    queue = mock()
    mgr = mock()
    cd = mock()
    sco = mock()
    md = get_default_md()
    opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

    sys.modules["pymqi"] = mock()
    sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
    sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
    sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
    sys.modules["pymqi"].expects(at_least_once()).md().will(return_value(md))
    sys.modules["pymqi"].expects(once()).Queue(same(mgr),
        eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

    sys.modules["pymqi"].MQMIError = mq.MQMIError

    mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
    queue.expects(at_least_once()).put(functor(condition_ignored), functor(condition_ignored))

    factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
    jms_template = JmsTemplate(factory)

    return message, jms_template

class WebSphereMQTestCase(MockTestCase):

    def _get_random_data(self):

        text = get_rand_string(101)
        jms_correlation_id = get_rand_string(36)
        jms_delivery_mode = choice((DELIVERY_MODE_NON_PERSISTENT, DELIVERY_MODE_PERSISTENT))
        jms_destination = get_rand_string(choice(queue_name_length))
        jms_expiration = random.randrange(int(_WMQ_MAX_EXPIRY_TIME - 2), int(_WMQ_MAX_EXPIRY_TIME + 2))
        jms_priority = choice(range(1,9))
        jms_redelivered = choice((True, False))
        jms_reply_to = get_rand_string(choice(queue_name_length))

        return(text, jms_correlation_id, jms_delivery_mode, jms_destination,
            jms_expiration, jms_priority, jms_redelivered, jms_reply_to)

    def testSendingMessagesToWebSphereMQ(self):

        # For whatever reason, pmock can't handle the following assertions on
        # the same mock object though it works fine when the assertions are
        # executed in isolation. That's why we need a loop below.
        #
        # queue.expects(once()).put(string_contains(raw_message_after_timestamp), eq(md))
        # queue.expects(once()).put(string_contains(raw_message_before_timestamp), eq(md))

        queue1 = Mock("queue_raw_message_before_timestamp")
        queue2 = Mock("queue_raw_message_after_timestamp")

        for queue in (queue1, queue2):

            mgr = self.mock()
            cd = self.mock()
            sco = self.mock()
            md = get_default_md()
            opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

            sys.modules["pymqi"] = self.mock()
            sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
            sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
            sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
            sys.modules["pymqi"].expects(once()).md().will(return_value(md))
            sys.modules["pymqi"].expects(once()).Queue(same(mgr),
                eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

            mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

            if queue.get_name() == "queue_raw_message_before_timestamp":
                queue.expects(once()).put(string_contains(raw_message_before_timestamp), eq(md))
            else:
                queue.expects(once()).put(string_contains(raw_message_after_timestamp), eq(md))

            queue.expects(once()).close()

            factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
            jms_template = JmsTemplate(factory)

            text_message = TextMessage()
            text_message.text = PAYLOAD

            jms_template.send(text_message, DESTINATION)

            del(sys.modules["pymqi"])

    def testCreatingDefaultMQRFH2JMS(self):

        now = long(time() * 1000)
        sleep(1.0)

        # Each folder is prepended by a 4-bytes header
        folder_header_length = 4

        destination_length = choice(queue_name_length)
        destination = get_rand_string(destination_length)
        message = TextMessage()

        # mcd folder is constant
        mcd = """<mcd><Msd>jms_text</Msd><msgbody xmlns:xsi="dummy" xsi:nil="true" /></mcd>  """
        mcd_len = len(mcd)
        mcd_len_wire_format = pack("!l", mcd_len)

        jms = "<jms><Dst>queue:///%s</Dst><Tms>1247950158160</Tms><Dlv>2</Dlv></jms>" % destination
        current_jms_len = len(jms)

        # Pad to a multiple of 4.
        if current_jms_len % 4 == 0:
            jms_len = current_jms_len
        else:
            padding = 4 - (current_jms_len % 4)
            jms += " " * padding
            jms_len = len(jms)

        jms_len_wire_format = pack("!l", jms_len)

        total_header_length = MQRFH2JMS.FIXED_PART_LENGTH + folder_header_length + mcd_len + folder_header_length + jms_len
        total_header_length_wire_format = pack("!l", total_header_length)

        mqrfh2jms = MQRFH2JMS()
        header = mqrfh2jms.build_header(message, destination, CMQC, now)

        header_mqrfh_struc_id = header[:4]
        header_WMQ_mqrfh_version_2 = header[4:8]
        header_total_header_length = header[8:12]
        header_WMQ_default_encoding_wire_format = header[12:16]
        header_WMQ_default_ccsid_wire_format = header[16:20]
        header_mqfmt_string = header[20:28]
        header_WMQ_mqrfh_no_flags_wire_format = header[28:32]
        header_WMQ_default_ccsid_wire_format = header[32:36]
        header_mcd_len = header[36:40]
        header_mcd = header[40:40+mcd_len]
        header_jms_len = header[40+mcd_len:40+mcd_len+folder_header_length]
        header_jms = header[40+mcd_len+folder_header_length:40+mcd_len+folder_header_length+jms_len]

        self.assertEqual(header_mqrfh_struc_id, CMQC.MQRFH_STRUC_ID)
        self.assertEqual(header_WMQ_mqrfh_version_2, _WMQ_MQRFH_VERSION_2)
        self.assertEqual(header_total_header_length, total_header_length_wire_format)
        self.assertEqual(header_WMQ_default_encoding_wire_format, _WMQ_DEFAULT_ENCODING_WIRE_FORMAT)
        self.assertEqual(header_WMQ_default_ccsid_wire_format, _WMQ_DEFAULT_CCSID_WIRE_FORMAT)
        self.assertEqual(header_mqfmt_string, CMQC.MQFMT_STRING)
        self.assertEqual(header_WMQ_mqrfh_no_flags_wire_format, _WMQ_MQRFH_NO_FLAGS_WIRE_FORMAT)
        self.assertEqual(header_WMQ_default_ccsid_wire_format, _WMQ_DEFAULT_CCSID_WIRE_FORMAT)
        self.assertEqual(header_mcd_len, mcd_len_wire_format)
        self.assertEqual(header_mcd, mcd)
        self.assertEqual(header_jms_len, jms_len_wire_format)

        # Don't compare the jms folder here - timestamps will differ, will check it below.
        # self.assertEqual(header_jms, jms)

        jms = etree.fromstring(header_jms)

        self.assertEqual(jms.find("Dst").text, "queue:///" + destination)
        self.assertTrue(bool((long(str(jms.find("Tms").text)) < long(time() * 1000)) is True))
        self.assertEqual(int(str(jms.find("Dlv").text)), DELIVERY_MODE_PERSISTENT)

    def testJMSAndWebSphereMQConstants(self):
        self.assertEqual(_WMQ_MQRFH_VERSION_2, "\x00\x00\x00\x02")
        self.assertEqual(_WMQ_DEFAULT_ENCODING, 273)
        self.assertEqual(_WMQ_DEFAULT_ENCODING_WIRE_FORMAT, pack("!l", 273))
        self.assertEqual(_WMQ_DEFAULT_CCSID, 1208)
        self.assertEqual(_WMQ_DEFAULT_CCSID_WIRE_FORMAT, pack("!l", 1208))
        self.assertEqual(_WMQ_MQFMT_RF_HEADER_2, "MQHRF2  ")
        self.assertEqual(_WMQ_MQRFH_NO_FLAGS_WIRE_FORMAT, "\x00\x00\x00\x00")
        self.assertEqual(MQRFH2JMS.FIXED_PART_LENGTH, 36)
        self.assertEqual(MQRFH2JMS.FOLDER_LENGTH_MULTIPLE, 4)
        self.assertEqual(_WMQ_MAX_EXPIRY_TIME, 214748364.7)
        self.assertEqual(_WMQ_ID_PREFIX, "ID:")
        self.assertEqual(etree.tostring(_mcd), """<mcd><Msd>jms_text</Msd><msgbody xmlns:xsi="dummy" xsi:nil="true" /></mcd>""")

    def testJMSConstants(self):
        self.assertEqual(DELIVERY_MODE_NON_PERSISTENT, 1)
        self.assertEqual(DELIVERY_MODE_PERSISTENT, 2)
        self.assertEqual(DEFAULT_DELIVERY_MODE, DELIVERY_MODE_PERSISTENT)
        self.assertEqual(DEFAULT_TIME_TO_LIVE, 0)
        self.assertEqual(RECEIVE_TIMEOUT_INDEFINITE_WAIT, 0)
        self.assertEqual(RECEIVE_TIMEOUT_NO_WAIT, -1)

    def testJmsTemplateSettingAndGettingJMSAttributes(self):

        (text, jms_correlation_id, jms_delivery_mode, jms_destination,
         jms_expiration, jms_priority, jms_redelivered,
         jms_reply_to) = self._get_random_data()

        message = TextMessage()
        message.text = text
        message.jms_correlation_id = jms_correlation_id
        message.jms_delivery_mode = jms_delivery_mode
        message.jms_destination = jms_destination
        message.jms_expiration = jms_expiration
        message.jms_priority = jms_priority
        message.jms_redelivered = jms_redelivered
        message.jms_reply_to = jms_reply_to

        self.assertEqual(message.text, text)
        self.assertEqual(message.jms_correlation_id, jms_correlation_id)
        self.assertEqual(message.jms_delivery_mode, jms_delivery_mode)
        self.assertEqual(message.jms_destination, jms_destination)
        self.assertEqual(message.jms_expiration, jms_expiration)
        self.assertEqual(message.jms_priority, jms_priority)
        self.assertEqual(message.jms_redelivered, jms_redelivered)
        self.assertEqual(message.jms_reply_to, jms_reply_to)

    def testWebSphereMQJMSHeadersMappingsToMQMDAndMQRFH2ForOutgoingMessages(self):

        (text, jms_correlation_id, jms_delivery_mode, jms_destination,
         jms_expiration, jms_priority, jms_redelivered,
         jms_reply_to) = self._get_random_data()

        message = TextMessage()

        # Message body and standard JMS headers
        message.text = text
        message.jms_correlation_id = jms_correlation_id
        message.jms_delivery_mode = jms_delivery_mode
        message.jms_destination = jms_destination
        message.jms_expiration = jms_expiration
        message.jms_priority = jms_priority
        message.jms_redelivered = jms_redelivered
        message.jms_reply_to = jms_reply_to

        # WebSphere MQ extended JMS headers
        jmsxgroupseq = 90 # Fudged.
        jmsxgroupid = get_rand_string(12)
        feedback = CMQC.MQFB_EXPIRATION
        jms_ibm_report_exception = CMQC.MQRO_EXCEPTION_WITH_DATA
        jms_ibm_report_expiration = CMQC.MQRO_EXPIRATION_WITH_FULL_DATA
        jms_ibm_report_coa = CMQC.MQRO_COA
        jms_ibm_report_cod = CMQC.MQRO_COD_WITH_DATA
        jms_ibm_report_pan = CMQC.MQRO_PAN
        jms_ibm_report_nan = CMQC.MQRO_NAN
        jms_ibm_report_pass_msg_id = CMQC.MQRO_PASS_MSG_ID
        jms_ibm_report_pass_correl_id = CMQC.MQRO_PASS_CORREL_ID
        jms_ibm_report_discard_msg = CMQC.MQRO_DISCARD_MSG

        message.JMSXGroupSeq = jmsxgroupseq
        message.JMSXGroupID = jmsxgroupid
        message.JMS_IBM_Report_Exception = jms_ibm_report_exception
        message.JMS_IBM_Report_Expiration = jms_ibm_report_expiration
        message.JMS_IBM_Report_COA = jms_ibm_report_coa
        message.JMS_IBM_Report_COD = jms_ibm_report_cod
        message.JMS_IBM_Report_PAN = jms_ibm_report_pan
        message.JMS_IBM_Report_NAN = jms_ibm_report_nan
        message.JMS_IBM_Report_Pass_Msg_ID = jms_ibm_report_pass_msg_id
        message.JMS_IBM_Report_Pass_Correl_ID = jms_ibm_report_pass_correl_id
        message.JMS_IBM_Report_Discard_Msg = jms_ibm_report_discard_msg
        message.JMS_IBM_Feedback = feedback
        message.JMS_IBM_Last_Msg_In_Group = True

        expected_mqmd_jms_correlation_id = jms_correlation_id.ljust(24)[:24]

        def _check_md(md):
            """ Verify MQMD attributes on their way to queue.put(body, md).
            """

            # DELIVERY_MODE_NON_PERSISTENT -> MQPER_NOT_PERSISTENT in cmqc.h
            # DELIVERY_MODE_PERSISTENT -> MQPER_PERSISTENT in cmqc.h

            if jms_delivery_mode == DELIVERY_MODE_NON_PERSISTENT:
                expected_md_persistence = CMQC.MQPER_NOT_PERSISTENT
            elif jms_delivery_mode == DELIVERY_MODE_PERSISTENT:
                expected_md_persistence = CMQC.MQPER_PERSISTENT

            if jms_expiration / 1000 > _WMQ_MAX_EXPIRY_TIME:
                expected_md_expiry = CMQC.MQEI_UNLIMITED
            else:
                # JMS header is in milliseconds, MQMD one is in centiseconds.
                expected_md_expiry = jms_expiration / 10

            # Truncated or padded to 24 characters.
            expected_jmsxgroupid = jmsxgroupid.ljust(24)[:24]

            expected_report = sum((jms_ibm_report_exception,jms_ibm_report_expiration,
                jms_ibm_report_coa, jms_ibm_report_cod, jms_ibm_report_pan,
                jms_ibm_report_nan, jms_ibm_report_pass_msg_id,
                jms_ibm_report_pass_correl_id, jms_ibm_report_discard_msg))

            # Standard MQMD headers
            self.assertEqual(md.Format, _WMQ_MQFMT_RF_HEADER_2)
            self.assertEqual(md.CodedCharSetId, _WMQ_DEFAULT_CCSID)
            self.assertEqual(md.Encoding, _WMQ_DEFAULT_ENCODING)

            # Mapped from standard JMS headers to MQMD
            self.assertEqual(md.CorrelId, expected_mqmd_jms_correlation_id, "md.CorrelId mismatch [%s] [%s]" % (md.CorrelId, expected_mqmd_jms_correlation_id))
            self.assertEqual(md.Persistence, expected_md_persistence, " md.Persistence [%s] [%s]" % (md.Persistence, expected_md_persistence))
            self.assertEqual(md.Expiry, expected_md_expiry, "md.Expiry mismatch [%s] [%s]" % (md.Expiry, expected_md_expiry))
            self.assertEqual(md.Priority, jms_priority, "md.Priority mismatch [%s] [%s]" % (md.Priority, jms_priority))
            self.assertEqual(md.ReplyToQ, jms_reply_to)

            # Extended Webpshere MQ JMS headers
            self.assertEqual(md.MsgSeqNumber, jmsxgroupseq, "md.MsgSeqNumber mismatch [%s] [%s]" % (md.MsgSeqNumber, jmsxgroupseq))
            self.assertEqual(md.GroupId, expected_jmsxgroupid, "md.GroupId mismatch [%s] [%s]" % (md.GroupId, expected_jmsxgroupid))
            self.assertEqual(md.Feedback, feedback, "md.Feedback mismatch [%s] [%s]" % (md.Feedback, feedback))
            self.assertEqual(md.Report, expected_report, "md.Report mismatch [%s] [%s]" % (md.Report, expected_report))

            self.assertTrue(((md.MsgFlags & (CMQC.MQMF_MSG_IN_GROUP) == CMQC.MQMF_MSG_IN_GROUP) is True),
                "md.Flags (JMSXGroupSeq) mismatch [%s] [%s]" % (md.MsgFlags, CMQC.MQMF_MSG_IN_GROUP))

            self.assertTrue(((md.MsgFlags & (CMQC.MQMF_LAST_MSG_IN_GROUP) == CMQC.MQMF_LAST_MSG_IN_GROUP) is True),
                "md.Flags (JMS_IBM_Last_Msg_In_Group) mismatch [%s] [%s]" % (md.MsgSeqNumber, CMQC.MQMF_LAST_MSG_IN_GROUP))

            return True

        def _check_mqrfh2(mqrfh2):

            mqrfh2_jms_start = mqrfh2.find("<jms>")
            mqrfh2_jmd_end = mqrfh2.find("</jms>") + 6

            mqrfh2_jms = str(mqrfh2[mqrfh2_jms_start:mqrfh2_jmd_end])
            jms = etree.fromstring(mqrfh2_jms)

            now = long(time() * 1000)

            self.assertEqual(str(jms.find("Pri").text), str(jms_priority))

            # The message has been already put onto queue so its timestamp
            # should be equal or earlier than now.
            jms_tms = long(str(jms.find("Tms").text))
            self.assertTrue(jms_tms <= now, "jms.Tms error [%s] [%s]" % (jms_tms, now))

            # Same as Webpshere MQ JMS Java API, jms.Dst cannnot be set manually
            # by user, though docs don't mention that.
            self.assertEqual(str(jms.find("Dst").text), "queue:///" + DESTINATION)

            # MQMD CorrelId is truncated to 24 characters, but MQRFH2's one isn't.
            self.assertEqual(str(jms.find("Cid").text), jms_correlation_id)

            # Message has been sent already sent a couple of milliseconds ago.
            jms_exp = long(str(jms.find("Exp").text))
            self.assertTrue(jms_exp - now <= jms_expiration, "jms.Exp error [%s] [%s]" % (jms_exp - now, jms_expiration))

            return True

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        mgr.expects(at_least_once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
        queue.expects(once()).put(functor(_check_mqrfh2), functor(_check_md))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)

        jms_template.send(message, DESTINATION)

        del(sys.modules["pymqi"])

    def testMessageConverterForOutgoingMessages(self):

        customer = "123"
        customer_account = "456"
        number = "789"
        date = "20090126"

        expected_message_after_conversion = ";".join((customer, customer_account,
            number, date))

        class Invoice(object):
            def __init__(self):
                self.customer = customer
                self.customer_account = customer_account
                self.number = number
                self.date = date

        class InvoiceConverter(object):
            def to_message(self, invoice):
                text = ";".join((invoice.customer, invoice.customer_account,
                    invoice.number, invoice.date))

                return TextMessage(text)

        def _check_payload(message):
            """ Business payload is the last part of a message, i.e. comes
            after the MQ headers.
            """
            return message.endswith(expected_message_after_conversion)

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        queue.expects(once()).put(functor(_check_payload), eq(md))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)
        invoice = Invoice()

        # No message converter set yet.
        self.assertRaises(JMSException, jms_template.convert_and_send, invoice, DESTINATION)

        # No JMSException at this point.
        jms_template.message_converter = InvoiceConverter()
        jms_template.convert_and_send(invoice, DESTINATION)

        del(sys.modules["pymqi"])

    def testSettingDefaultDestinationForOutgoingMessages(self):

        default_destination = get_rand_string(24)

        def _check_mqrfh2_destination(message):
            return "queue:///" + default_destination in message

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))

        queue.stubs().put(functor(_check_mqrfh2_destination), eq(md))

        # Queue name must be equal to default destination, pmock will verify it.
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(default_destination), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)

        text_message = TextMessage()
        text_message.text = PAYLOAD

        # No default destination set yet.
        self.assertRaises(JMSException, jms_template.send, text_message)

        # No JMSException here.
        jms_template.default_destination = default_destination
        jms_template.send(text_message)

    def testUnhexlifyWebSphereMQIdentifiers(self):

        # Basic check.
        hex_wmq_id = "ID:414d5120535052494e47505954484f4ecc90674a041f0020"
        unhexlified = "AMQ SPRINGPYTHON\xcc\x90gJ\x04\x1f\x00 "

        self.assertEquals(unhexlify_wmq_id(hex_wmq_id), unhexlified)

        # Now the real message, check the unhexlifying for every relevant JMS
        # and MQMD header.

        def get_expected_md_header_value(jms_header_value):
            if jms_header_value.startswith("ID:"):
                expected_mqmd_header = unhexlify(jms_header_value.replace("ID:", "", 1))
            else:
                if len(jms_header_value) == 24:
                    expected_mqmd_header = jms_header_value
                elif len(jms_header_value) < 24:
                    expected_mqmd_header = jms_header_value.ljust(24)
                elif len(jms_header_value) > 24:
                    expected_mqmd_header = jms_header_value[:24]

            return expected_mqmd_header

        jms_to_mqmd_headers = {
            "jms_correlation_id":"CorrelId",
            "JMSXGroupID":"GroupId"}

        for jms_header, mqmd_header in jms_to_mqmd_headers.items():

            jms_wmq_id = get_rand_string(24)
            jms_wmq_id_header_value = "ID:" + hexlify(jms_wmq_id)
            jms_non_wmq_header_short_value = get_rand_string(12)
            jms_non_wmq_header_max_mqmd_length_value = get_rand_string(24)
            jms_non_wmq_header_long_value = get_rand_string(36)

            for jms_header_value in(jms_wmq_id_header_value,
                jms_non_wmq_header_short_value, jms_non_wmq_header_max_mqmd_length_value,
                jms_non_wmq_header_long_value):

                expected_mqmd_header_value = get_expected_md_header_value(jms_header_value)

                def _check_md(md):
                    mqmd_header_value = getattr(md, mqmd_header)

                    self.assertEquals(mqmd_header_value, expected_mqmd_header_value,
                        ("ID mismatch mqmd_header_value='%s' expected_mqmd_header_value='%s' " +
                            "jms_header='%s' mqmd_header='%s' jms_header_value='%s'") % (
                                mqmd_header_value, expected_mqmd_header_value,
                                jms_header, mqmd_header, jms_header_value))
                    return True

                message = TextMessage()
                message.text = "Hi there."

                setattr(message, jms_header, jms_header_value)

                queue = self.mock()
                mgr = self.mock()
                cd = self.mock()
                sco = self.mock()
                md = get_default_md()
                opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

                sys.modules["pymqi"] = self.mock()
                sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
                sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
                sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
                sys.modules["pymqi"].expects(once()).md().will(return_value(md))
                sys.modules["pymqi"].expects(once()).Queue(same(mgr),
                    eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

                mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

                queue.expects(once()).put(functor(condition_ignored), functor(_check_md))

                factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
                jms_template = JmsTemplate(factory)

                jms_template.send(message, DESTINATION)

                del(sys.modules["pymqi"])

    def testMappingJMSHeadersOverwrittenByCallingQueuePut(self):

        now = long(time() * 1000)

        jms_expiration = 2619
        expected_jms_expiration = now + jms_expiration

        jms_message_id = get_rand_string(24)
        expected_jms_message_id = "ID:" + hexlify(jms_message_id)

        priority = random.choice(range(1,9))

        expected_jmsxuserid = get_rand_string(6)
        expected_jmsxappid = get_rand_string(6)
        expected_jms_ibm_putdate = "20090813"
        expected_jms_ibm_puttime = "21324547"
        expected_jms_priority = priority
        expected_jms_timestamp = 1250199165470

        def update_md(md):

            md.MsgId = jms_message_id
            md.UserIdentifier = expected_jmsxuserid
            md.PutApplName = expected_jmsxappid
            md.PutDate = expected_jms_ibm_putdate
            md.PutTime = expected_jms_ibm_puttime
            md.Priority = priority

            return True

        message = TextMessage()
        message.text = "Hi there."
        message.jms_expiration = jms_expiration

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        queue.expects(once()).put(functor(condition_ignored), functor(update_md))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)

        jms_template.send(message, DESTINATION)

        # jms_template.send should've set those attributes, values taken from md.
        self.assertEquals(message.jms_message_id, expected_jms_message_id)
        self.assertTrue((expected_jms_expiration - message.jms_expiration) <= jms_expiration,
            "expected_jms_expiration: '%s', message.jms_expiration: '%s', jms_expiration: '%s'" % (
                expected_jms_expiration, message.jms_expiration, jms_expiration))
        self.assertEquals(message.JMSXUserID, expected_jmsxuserid)
        self.assertEquals(message.JMSXAppID, expected_jmsxappid)
        self.assertEquals(message.JMS_IBM_PutDate, expected_jms_ibm_putdate)
        self.assertEquals(message.JMS_IBM_PutTime, expected_jms_ibm_puttime)
        self.assertEquals(message.jms_priority, expected_jms_priority)
        self.assertEquals(message.jms_timestamp, expected_jms_timestamp)
        self.assertEquals(message.jms_destination, DESTINATION)

        del(sys.modules["pymqi"])

    def testRaisingJMSExceptionOnInvalidDeliveryMode(self):

        message, jms_template = get_simple_message_and_jms_template(self.mock)

        # jms_delivery_mode should be equal to DELIVERY_MODE_NON_PERSISTENT or DELIVERY_MODE_PERSISTENT
        message.jms_delivery_mode = get_rand_string(10)
        self.assertRaises(JMSException, jms_template.send, message, DESTINATION)

        # No JMSException here
        for mode in(DELIVERY_MODE_NON_PERSISTENT, DELIVERY_MODE_PERSISTENT):
            message.jms_delivery_mode = mode
            jms_template.send(message, DESTINATION)

        del(sys.modules["pymqi"])

    def testCachingOpenQueues(self):

        message = TextMessage()
        message.text = "Hi there."

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        gmo = self.mock()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK


        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(at_least_once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(at_least_once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(at_least_once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(at_least_once()).md().will(return_value(md))
        sys.modules["pymqi"].expects(at_least_once()).gmo().will(return_value(gmo))

        sys.modules["pymqi"].expects(at_least_once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        sys.modules["pymqi"].expects(at_least_once()).Queue(same(mgr),
            eq(DESTINATION)).will(return_value(queue))

        mgr.expects(at_least_once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
        queue.expects(at_least_once()).put(functor(condition_ignored), functor(condition_ignored))
        queue.expects(at_least_once()).close()
        queue.set_default_stub(return_value(raw_message_for_get))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT,
            cache_open_send_queues=False)
        jms_template = JmsTemplate(factory)

        for x in range(10):
            jms_template.send(message, DESTINATION)

            self.assertTrue(DESTINATION not in factory._open_send_queues_cache)
            self.assertTrue(len(factory._open_send_queues_cache) == 0)

        factory.cache_open_send_queues = True

        for x in range(10):
            jms_template.send(message, DESTINATION)

            self.assertTrue(DESTINATION in factory._open_send_queues_cache)
            self.assertTrue(len(factory._open_send_queues_cache), 1)

        factory2 = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template2 = JmsTemplate(factory2)

        for x in range(10):
            jms_template2.send(message, DESTINATION)
            self.assertTrue(DESTINATION in factory2._open_send_queues_cache)
            self.assertEquals(1, len(factory2._open_send_queues_cache))


        # Now make sure open queues are not stored in caches.
        factory3 = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        factory3.cache_open_send_queues = False
        factory3.cache_open_receive_queues = False

        jms_template3 = JmsTemplate(factory3)

        for x in range(10):
            jms_template3.send(message, DESTINATION)
            jms_template3.receive(DESTINATION)

            self.assertTrue(DESTINATION not in factory3._open_send_queues_cache)
            self.assertEquals(0, len(factory3._open_send_queues_cache))

            self.assertTrue(DESTINATION not in factory3._open_receive_queues_cache)
            self.assertEquals(0, len(factory3._open_receive_queues_cache))

        del(sys.modules["pymqi"])

    def testSettingUserAttributes(self):

        source = "<CRM>"
        preferred_provider = "<BILLING>"

        broker_id = get_rand_string(26)
        expected_source = escape(source)
        expected_preferred_provider = escape(preferred_provider)

        # 'bile' in Polish features no letters in ASCII range.
        foobar = unicode('\xc5\xbc\xc3\xb3\xc5\x82\xc4\x87', "utf-8") + get_rand_string(26)

        def _check_user_attributes(mqrfh2):

            usr_start = mqrfh2.find("<usr>")
            usr_end = mqrfh2.find("</usr>") + 6
            usr_str = str(mqrfh2[usr_start:usr_end])

            usr = etree.fromstring(usr_str)

            self.assertEqual(str(usr.find("broker_id").text), broker_id)
            self.assertEqual(str(usr.find("SOURCE").text), expected_source)
            self.assertEqual(str(usr.find("PREFERRED_PROVIDER").text), expected_preferred_provider)
            self.assertEqual(unicode(usr.find("foobar").text), foobar)

            return True

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))

        queue.stubs().put(functor(_check_user_attributes), eq(md))

        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)

        text_message = TextMessage()
        text_message.text = PAYLOAD
        text_message.broker_id = broker_id
        text_message.SOURCE = source
        text_message.PREFERRED_PROVIDER = preferred_provider
        text_message.foobar = foobar

        jms_template.send(text_message, DESTINATION)

    def testUnicodePayload(self):

        message, jms_template = get_simple_message_and_jms_template(self.mock)

        # 'Suzuki' in Japanese
        message.payload = unicode("\xe9\x88\xb4\xe6\x9c\xa8", "utf-8")

        # No exception should be raised.
        jms_template.send(message, DESTINATION)

        del(sys.modules["pymqi"])

    def testJmsTemplateSettingAndGettingJMSAttributes(self):
        (text, jms_correlation_id, jms_delivery_mode, jms_destination,
         jms_expiration, jms_priority, jms_redelivered,
         jms_reply_to) = self._get_random_data()

        message = TextMessage()
        message.text = text
        message.jms_correlation_id = jms_correlation_id
        message.jms_delivery_mode = jms_delivery_mode
        message.jms_destination = jms_destination
        message.jms_expiration = jms_expiration
        message.jms_priority = jms_priority
        message.jms_redelivered = jms_redelivered
        message.jms_reply_to = jms_reply_to

        self.assertEqual(message.text, text)
        self.assertEqual(message.jms_correlation_id, jms_correlation_id)
        self.assertEqual(message.jms_delivery_mode, jms_delivery_mode)
        self.assertEqual(message.jms_destination, jms_destination)
        self.assertEqual(message.jms_expiration, jms_expiration)
        self.assertEqual(message.jms_priority, jms_priority)
        self.assertEqual(message.jms_redelivered, jms_redelivered)
        self.assertEqual(message.jms_reply_to, jms_reply_to)

    def testSendingStringMessages(self):

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        string = "foo"
        uni = u"bar"

        for payload in(string, uni):

            def _check_payload(message):
                self.assertEquals(message[-3:], payload)
                return True

            sys.modules["pymqi"] = self.mock()
            sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
            sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
            sys.modules["pymqi"].expects(once()).sco().will(return_value(sco))
            sys.modules["pymqi"].expects(once()).md().will(return_value(md))
            sys.modules["pymqi"].expects(once()).Queue(same(mgr),
                eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))

            mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
            queue.expects(at_least_once()).put(functor(_check_payload), functor(condition_ignored))

            factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
            jms_template = JmsTemplate(factory)

            jms_template.send(payload, DESTINATION)

            del(sys.modules["pymqi"])


################################################################################


    def testReceivingMessages(self):

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        gmo = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        md.PutDate = "20090813"
        md.PutTime = "21324547"

        class Invoice(object):
            def __init__(self, number):
                self.number = number

        class InvoiceConverter(object):
            def from_message(self, message):
                return Invoice(message.text)

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
        queue.set_default_stub(return_value(raw_message_for_get))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        jms_template1 = JmsTemplate(factory)

        # No message converter set yet.
        self.assertRaises(JMSException, jms_template1.receive_and_convert, DESTINATION, 300)

        jms_template1.message_converter = InvoiceConverter()

        # No JMSException at this point.
        jms_template1.receive_and_convert(DESTINATION, 300)

        jms_template2 = JmsTemplate(factory)
        self.assertEquals("b0f32f11-b531-4bbf-b985-77e795d77024", jms_template2.receive(DESTINATION).text)

        jms_template3 = JmsTemplate(factory)
        jms_template3.default_destination = DESTINATION
        self.assertEquals("b0f32f11-b531-4bbf-b985-77e795d77024", jms_template3.receive().text)

        # No destination set.
        jms_template4 = JmsTemplate(factory)
        self.assertRaises(JMSException, jms_template4.receive)

        del(sys.modules["pymqi"])

################################################################################

    def testGetConnectionInfo(self):

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        conn_info = factory.get_connection_info()
        self.assertEquals(conn_info, "queue manager=[%s], channel=[%s], conn_name=[%s(%s)]" % (
            QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT))


    def testGetJMSTimestampFromMD(self):
        date = "20091021"
        time = "16321012"

        factory = WebSphereMQConnectionFactory()

        self.assertEquals(factory._get_jms_timestamp_from_md(date, time), 1256142730120)

    def testDynamicQueues(self):

        expected_dyn_queue_name = get_rand_string(12)
        expected_dyn_queue = self.mock()
        expected_dyn_queue._Queue__qDesc = self.mock()
        expected_dyn_queue._Queue__qDesc.ObjectName = expected_dyn_queue_name

        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        payload = get_rand_string(3)
        uni = u"bar"

        def _check_payload(message):
            self.assertEquals(message[-3:], payload)
            return True

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        sys.modules["pymqi"].expects(once()).md().will(return_value(md))
        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        sys.modules["pymqi"].expects(once()).Queue(same(mgr), eq("SYSTEM.DEFAULT.MODEL.QUEUE"),
            eq(CMQC.MQOO_INPUT_SHARED)).will(return_value(expected_dyn_queue))

        sys.modules["pymqi"].expects(once()).Queue(same(mgr), eq(expected_dyn_queue_name),
            eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(expected_dyn_queue))
        expected_dyn_queue.set_default_stub(return_value(None))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        jms_template = JmsTemplate(factory)

        dyn_queue = jms_template.open_dynamic_queue()

        self.assertEquals(len(factory._open_dynamic_queues_cache), 1)
        self.assertTrue(expected_dyn_queue_name in factory._open_dynamic_queues_cache)
        self.assertEquals(factory._open_dynamic_queues_cache[expected_dyn_queue_name], expected_dyn_queue)

        jms_template.send(payload, dyn_queue)
        jms_template.close_dynamic_queue(dyn_queue)

        self.assertEquals(len(factory._open_dynamic_queues_cache), 0)
        self.assertTrue(expected_dyn_queue_name not in factory._open_dynamic_queues_cache)
        self.assertRaises(KeyError, factory._open_dynamic_queues_cache.__getitem__, expected_dyn_queue_name)

        del(sys.modules["pymqi"])

    def testWebSphereMQJMSException(self):

        expected_completion_code = CMQC.MQCC_FAILED
        expected_reason_code = CMQC.MQRC_Q_MGR_STOPPING

        message = get_rand_string(20)
        mq_exception = mq.MQMIError(expected_completion_code, expected_reason_code)

        try:
            raise WebSphereMQJMSException()
        except WebSphereMQJMSException, e:
            self.assertEquals(e.completion_code, None)
            self.assertEquals(e.reason_code, None)
            self.assertEquals(e.message, None)

        try:
            raise WebSphereMQJMSException(message)
        except WebSphereMQJMSException, e:
            self.assertEquals(e.completion_code, None)
            self.assertEquals(e.reason_code, None)
            self.assertEquals(e.message, message)

        #sys.modules["pymqi"].MQMIError = mq.MQMIError

        try:
            raise WebSphereMQJMSException(completion_code=mq_exception.comp, reason_code=mq_exception.reason)
        except WebSphereMQJMSException, e:
            self.assertEquals(e.completion_code, expected_completion_code)
            self.assertEquals(e.reason_code, expected_reason_code)

    def testMessageConverterRaisingNotImplementedError(self):

        converter = MessageConverter()
        self.assertRaises(NotImplementedError, converter.to_message, None)
        self.assertRaises(NotImplementedError, converter.from_message, None)

    def testTextMessageStringRepresentation(self):

        expected_message_sha1_sum_max_100_chars = "aa340eed9dacde39fd355c27b54b2c0f33454f97"
        expected_message_sha1_sum_max_4_chars = "662a66f448dce916d0b008edfe995cb879d039bf"
        expected_message_sha1_sum_no_text = "6c59aa896a27fb6e7494089bc6a6d6193129b796"

        message1 = TextMessage()
        message1.text = "ZFJQ#(RAWFD" * 1000
        message1.jms_correlation_id = "APWRI!@#ffffq3rU"
        message1.jms_delivery_mode = DEFAULT_DELIVERY_MODE
        message1.jms_destination = "ZVCW#TRW"
        message1.jms_expiration = 1252094803975
        message1.jms_priority = 6
        message1.jms_redelivered = True
        message1.jms_reply_to = "SETAFJOEF"
        message1.jms_message_id = "SFJW)$%@)*%@#%@"
        message1.jms_correlation_id = "ARO@#$R@#%$@#RVSTYUO"
        message1.jms_timestamp = 1250199165470
        message1.CsKAo9 = "ZDCVKWER@_#%LA"

        self.assertEquals(message1.max_chars_printed, 100)
        self.assertEquals(sha1(str(message1)).hexdigest(), expected_message_sha1_sum_max_100_chars)

        message2 = TextMessage(max_chars_printed=4)
        message2.text = "SADFK@$#RTIWA" * 1000
        message2.jms_correlation_id = "SZDFKW$#A:<Q"
        message2.jms_delivery_mode = DEFAULT_DELIVERY_MODE
        message2.jms_destination = "PSDF#@$"
        message2.jms_expiration = 1252094803975
        message2.jms_priority = 8
        message2.jms_redelivered = False
        message2.jms_reply_to = "ASDOFJ#$"
        message2.jms_message_id = "MCNQW#%@#"
        message2.jms_correlation_id = "VWJ$T^I%F"
        message2.jms_timestamp = 1250199165470
        message2.SZVweFWJ = "VJWEROGWQ"

        self.assertEquals(message2.max_chars_printed, 4)
        self.assertEquals(sha1(str(message2)).hexdigest(), expected_message_sha1_sum_max_4_chars)

        message3 = TextMessage(max_chars_printed=1000)
        message3.jms_correlation_id = "FQW#(R%#@"
        message3.jms_delivery_mode = DEFAULT_DELIVERY_MODE
        message3.jms_destination = "SAFK@#@#"
        message3.jms_expiration = 1252094803975
        message3.jms_priority = 1
        message3.jms_redelivered = True
        message3.jms_reply_to = "PSAEF#J"
        message3.jms_message_id = "AFJ#)@#DF"
        message3.jms_correlation_id = "AVJEOW%$"
        message3.jms_timestamp = 1250199165470
        message3.zxfWEOJWA = "cASJOR@#$"

        self.assertEquals(message3.max_chars_printed, 1000)
        self.assertEquals(sha1(str(message3)).hexdigest(), expected_message_sha1_sum_no_text)

    def testDestroyingConnectionFactory(self):

        class DummyQueue(object):
            pass

        class DummyQueueManager(object):
            def disconnect(self):
                pass

        send_queue = DummyQueue()
        receive_queue = DummyQueue()
        dyn_queue = DummyQueue()

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        factory.mgr = DummyQueueManager()
        factory._is_connected = True

        factory._open_send_queues_cache["foo"] = send_queue
        factory._open_receive_queues_cache["bar"] = receive_queue
        factory._open_dynamic_queues_cache["baz"] = dyn_queue

        self.assertEquals(len(factory._open_send_queues_cache), 1)
        self.assertEquals(len(factory._open_receive_queues_cache), 1)
        self.assertEquals(len(factory._open_dynamic_queues_cache), 1)

        factory.destroy()

        self.assertEquals(len(factory._open_send_queues_cache), 0)
        self.assertEquals(len(factory._open_receive_queues_cache), 0)
        self.assertEquals(len(factory._open_dynamic_queues_cache), 0)

        factory.destroy()

        self.assertEquals(False, factory._is_connected)
        self.assertEquals(True, factory._disconnecting)

    def testStrippingPrefixesFromDestination(self):
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        dest1 = "queue:///TEST2"
        dest2 = "queue://SPRINGPYTHON1/SPRING/PYTHON.TO/JAVA.REQ.1"
        dest3 = "TEST3"
        dest4 = "ABC/"
        dest5 = "/ABC/"
        dest6 = "queue://///ABC/"

        expected_dest1 = "TEST2"
        expected_dest2 = "SPRING/PYTHON.TO/JAVA.REQ.1"
        expected_dest3 = "TEST3"
        expected_dest4 = "ABC/"
        expected_dest5 = "/ABC/"
        expected_dest6 = "//ABC/"

        self.assertEquals(expected_dest1, factory._strip_prefixes_from_destination(dest1))
        self.assertEquals(expected_dest2, factory._strip_prefixes_from_destination(dest2))
        self.assertEquals(expected_dest3, factory._strip_prefixes_from_destination(dest3))
        self.assertEquals(expected_dest4, factory._strip_prefixes_from_destination(dest4))
        self.assertEquals(expected_dest5, factory._strip_prefixes_from_destination(dest5))
        self.assertEquals(expected_dest6, factory._strip_prefixes_from_destination(dest6))

    def testFactoryExportingWebSphereMQConnectionFactoryOnly(self):
        _globals = {}
        _locals = {}

        exec "from springpython.jms.factory import *" in _globals, _locals

        self.assertEquals(1, len(_locals.keys()))
        self.assertEquals("WebSphereMQConnectionFactory", _locals.keys()[0])


    def testFactoryRaisingJMSExceptionOnConnect(self):

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        gmo = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()

        # Setting None here makes sure there will be an AttributeError raised
        # later on when trying to 'connectWithOptions'.
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(None))

        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        self.assertRaises(JMSException, factory._connect)

        del(sys.modules["pymqi"])

    def testRaisingWebSphereMQJMSExceptionOnUnknownMDPersistence(self):
        md = mq.md()
        md.Persistence = 1000 # There's no such 'Persistence' mode in WMQ

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        self.assertRaises(JMSException, factory._build_text_message, md, raw_message_for_get)

    def testRaisingExceptionsOnMQMIErrors(self):

        class NoMessageAvailableExceptionRaisingQueue(object):
            def get(self, *ignored_args, **ignored_kwargs):
                e = mq.MQMIError(CMQC.MQCC_FAILED, CMQC.MQRC_NO_MSG_AVAILABLE)
                raise e

        class OptionNotValidForTypeReturningQueue(object):
            def get(self, *ignored_args, **ignored_kwargs):
                e = mq.MQMIError(CMQC.MQCC_FAILED, CMQC.MQRC_OPTION_NOT_VALID_FOR_TYPE)
                raise e

        class TestQueueManager(object):
            def connectWithOptions(self, *ignored_args, **ignored_kwargs):
                pass

        mgr = TestQueueManager()
        cd = self.mock()
        sco = self.mock()
        gmo = self.mock()
        md = mq.md()

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))

        #
        # MQRC_NO_MSG_AVAILABLE
        #
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(NoMessageAvailableExceptionRaisingQueue()))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        factory._connected = True
        jms_template = JmsTemplate(factory)

        self.assertRaises(NoMessageAvailableException, jms_template.receive, DESTINATION)

        #
        # MQRC_OPTION_NOT_VALID_FOR_TYPE
        #
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(OptionNotValidForTypeReturningQueue()))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)
        factory._connected = True
        jms_template = JmsTemplate(factory)

        self.assertRaises(WebSphereMQJMSException, jms_template.receive, DESTINATION)

        del(sys.modules["pymqi"])

    def testMQRFH2JMSMissingNamespaceWorkaround(self):
        mqrfh2jms = MQRFH2JMS()
        mqrfh2jms.build_folder('<mcd><Msd>jms_text</Msd><msgbody xsi:nil="true" /></mcd>')

        msgbody = mqrfh2jms.folders["mcd"].find("msgbody")

        # msgbody.get will return None if such a namespace will not have been defined.
        self.assertEquals("true", msgbody.get("{dummy}nil"))

    def testSimpleMessageListenerContainer(self):

        class TestMessageHandler(object):
            def handle(self, message):
                return 123

        handler = TestMessageHandler()
        concurrent_listeners = 4
        handlers_per_listener = 2
        wait_interval = 1300

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        gmo = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts))
        queue.set_default_stub(return_value(raw_message_for_get))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        smlc = SimpleMessageListenerContainer(factory, DESTINATION, handler,
                    concurrent_listeners, handlers_per_listener, wait_interval)
        smlc.after_properties_set()

        self.assertEquals(smlc.factory, factory)
        self.assertEquals(smlc.destination, DESTINATION)
        self.assertEquals(smlc.handler, handler)
        self.assertEquals(smlc.concurrent_listeners, concurrent_listeners)
        self.assertEquals(smlc.handlers_per_listener, handlers_per_listener)
        self.assertEquals(smlc.wait_interval, wait_interval)

        del(sys.modules["pymqi"])

    def testWebSphereMQListener(self):

        message = get_rand_string(12)
        exception_reason = get_rand_string(12) + "ęóąśłżźćń"

        class TestMessageHandler(object):
            def __init__(self):
                self.data = []

            def __str__(self):
                return "%s %s" % (hex(id(self)), str(self.data))

            def handle(self, message):
                self.data.append(message)

        class _ConnectionFactory(WebSphereMQConnectionFactory):
            def __init__(self, *args):
                super(_ConnectionFactory, self).__init__(*args)
                self.call_count = 0

            def receive(self, destination, wait_interval):
                self.call_count += 1

                if self.call_count == 1:
                    import sys
                    return message
                elif self.call_count == 2:
                    raise NoMessageAvailableException()
                else:
                    raise WebSphereMQJMSException(exception_reason, CMQC.MQCC_FAILED, CMQC.MQRC_OPTION_NOT_VALID_FOR_TYPE)


        handler = TestMessageHandler()
        handlers_per_listener = 1
        wait_interval = 1300

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        gmo = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts))

        factory = _ConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        listener = WebSphereMQListener()
        listener.factory = factory
        listener.destination = DESTINATION
        listener.wait_interval = wait_interval
        listener.handler = handler
        listener.handlers_pool = ThreadPool(handlers_per_listener)

        try:
            listener.run()
        except WebSphereMQJMSException, e:
            sleep(0.1) # Allows the handler thread to process the message
            self.assertEquals(e.message, exception_reason)
            self.assertEquals(3, factory.call_count)
            self.assertEquals(1, len(handler.data))
            self.assertEquals(message, handler.data[0])
        finally:
            del(sys.modules["pymqi"])

    def testSimpleMessageListenerContainerMessageHandler(self):
        handler = MessageHandler()
        self.assertRaises(NotImplementedError, handler.handle, "foo")

        try:
            handler.handle("foo")
        except NotImplementedError, e:
            self.assertEquals(e.message, "Should be overridden by subclasses.")

    def testSSLCorrectSettings(self):
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()

        cd.SSLCipherSpec = "TLS_RSA_WITH_AES_256_CBC_SHA"
        sco.KeyRepository = "/tmp/foobar"

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(once()).cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        mgr.expects(once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT, ssl=True,
                                               ssl_cipher_spec="TLS_RSA_WITH_AES_256_CBC_SHA",
                                               ssl_key_repository="/tmp/foobar")
        factory._connect()

        del(sys.modules["pymqi"])

    def testSSLIncorrectSettings(self):

        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].expects(at_least_once()).QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].expects(at_least_once()).cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        mgr.expects(at_least_once()).connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        # ssl=True and no ssl_cipher_spec nor ssl_key_repository.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT, ssl=True)
        self.assertRaises(JMSException, factory._connect)
        try:
            factory._connect()
        except JMSException, e:
            self.assertEquals(e.args[0], "SSL support requires setting both ssl_cipher_spec and ssl_key_repository")

        # ssl=True and ssl_cipher_spec only.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT, ssl=True,
                                               ssl_cipher_spec="TLS_RSA_WITH_AES_256_CBC_SHA")
        self.assertRaises(JMSException, factory._connect)
        try:
            factory._connect()
        except JMSException, e:
            self.assertEquals(e.args[0], "SSL support requires setting both ssl_cipher_spec and ssl_key_repository")

        # ssl=True and ssl_key_repository only.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT, ssl=True,
                                               ssl_key_repository="/tmp/foobar")
        self.assertRaises(JMSException, factory._connect)
        try:
            factory._connect()
        except JMSException, e:
            self.assertEquals(e.args[0], "SSL support requires setting both ssl_cipher_spec and ssl_key_repository")

        # ssl_cipher_spec only, ssl=False.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT,
                                               ssl_cipher_spec="TLS_RSA_WITH_AES_256_CBC_SHA")
        factory._connect()

        # ssl_key_repository only, ssl=False.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT,
                                               ssl_key_repository="/tmp/foobar")
        factory._connect()

        # ssl_cipher_spec and ssl_key_repository, ssl=False.
        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT,
                                               ssl_cipher_spec="TLS_RSA_WITH_AES_256_CBC_SHA",
                                               ssl_key_repository="/tmp/foobar")
        factory._connect()

        del(sys.modules["pymqi"])

    def testSimpleMessageListenerContainer(self):

        class TestMessageHandler(object):
            def handle(self, message):
                return 123

        handler = TestMessageHandler()
        concurrent_listeners = 4
        handlers_per_listener = 2
        wait_interval = 1300

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        gmo = self.mock()
        md = get_default_md()
        sco = self.mock()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))
        sys.modules["pymqi"].expects(once()).Queue(same(mgr),
            eq(DESTINATION), eq(CMQC.MQOO_INPUT_SHARED | CMQC.MQOO_OUTPUT)).will(return_value(queue))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))
        queue.set_default_stub(return_value(raw_message_for_get))

        factory = WebSphereMQConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        smlc = SimpleMessageListenerContainer(factory, DESTINATION, handler,
                    concurrent_listeners, handlers_per_listener, wait_interval)
        smlc.after_properties_set()

        self.assertEquals(smlc.factory, factory)
        self.assertEquals(smlc.destination, DESTINATION)
        self.assertEquals(smlc.handler, handler)
        self.assertEquals(smlc.concurrent_listeners, concurrent_listeners)
        self.assertEquals(smlc.handlers_per_listener, handlers_per_listener)
        self.assertEquals(smlc.wait_interval, wait_interval)

        del(sys.modules["pymqi"])

    def testWebSphereMQListener(self):

        message = get_rand_string(12)
        exception_reason = get_rand_string(12) + "ęóąśłżźćń"

        class TestMessageHandler(object):
            def __init__(self):
                self.data = []

            def __str__(self):
                return "%s %s" % (hex(id(self)), str(self.data))

            def handle(self, message):
                self.data.append(message)

        class _ConnectionFactory(WebSphereMQConnectionFactory):
            def __init__(self, *args):
                super(_ConnectionFactory, self).__init__(*args)
                self.call_count = 0

            def receive(self, destination, wait_interval):
                self.call_count += 1

                if self.call_count == 1:
                    import sys
                    return message
                elif self.call_count == 2:
                    raise NoMessageAvailableException()
                else:
                    raise WebSphereMQJMSException(exception_reason, CMQC.MQCC_FAILED, CMQC.MQRC_OPTION_NOT_VALID_FOR_TYPE)


        handler = TestMessageHandler()
        handlers_per_listener = 1
        wait_interval = 1300

        queue = self.mock()
        mgr = self.mock()
        cd = self.mock()
        sco = self.mock()
        gmo = self.mock()
        md = get_default_md()
        opts = CMQC.MQCNO_HANDLE_SHARE_BLOCK

        sys.modules["pymqi"] = self.mock()
        sys.modules["pymqi"].MQMIError = mq.MQMIError
        sys.modules["pymqi"].stubs().QueueManager(eq(None)).will(return_value(mgr))
        sys.modules["pymqi"].stubs().cd().will(return_value(cd))
        sys.modules["pymqi"].stubs().sco().will(return_value(sco))
        sys.modules["pymqi"].stubs().md().will(return_value(md))
        sys.modules["pymqi"].stubs().gmo().will(return_value(gmo))
        mgr.stubs().connectWithOptions(eq(QUEUE_MANAGER), cd=eq(cd), opts=eq(opts), sco=eq(sco))

        factory = _ConnectionFactory(QUEUE_MANAGER, CHANNEL, HOST, LISTENER_PORT)

        listener = WebSphereMQListener()
        listener.factory = factory
        listener.destination = DESTINATION
        listener.wait_interval = wait_interval
        listener.handler = handler
        listener.handlers_pool = ThreadPool(handlers_per_listener)

        try:
            listener.run()
        except WebSphereMQJMSException, e:
            sleep(0.5) # Allows the handler thread to process the message
            self.assertEquals(e.message, exception_reason)
            self.assertEquals(3, factory.call_count)
            self.assertEquals(1, len(handler.data))
            self.assertEquals(message, handler.data[0])
        finally:
            del(sys.modules["pymqi"])

    def testSimpleMessageListenerContainerMessageHandler(self):
        handler = MessageHandler()
        self.assertRaises(NotImplementedError, handler.handle, "foo")

        try:
            handler.handle("foo")
        except NotImplementedError, e:
            self.assertEquals(e.message, "Should be overridden by subclasses.")

    def testNeedsMCD(self):
        message = TextMessage(get_rand_string(12))
        destination = get_rand_string(12)
        now = long(time() * 1000)
        
        has_mcd = MQRFH2JMS(True).build_header(message, destination, CMQC, now)
        has_no_mcd = MQRFH2JMS(False).build_header(message, destination, CMQC, now)
        
        self.assertTrue('mcd' in has_mcd)
        self.assertTrue('mcd' not in has_no_mcd)